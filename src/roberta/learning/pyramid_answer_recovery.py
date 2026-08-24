from __future__ import annotations

import json
from typing import Any, Mapping, Sequence

from langchain_core.messages import AIMessage, HumanMessage

from .pyramid_exam import PyramidExamError, _message_text, _parse_json


class MissingAnswerRetryModel:
    """Retry one incomplete or structurally malformed Pyramid answer batch.

    The wrapped model remains authoritative for the answer text. This adapter only
    performs bounded recovery. A structurally malformed initial response gets one
    full-batch regeneration attempt. A structurally valid but incomplete response
    gets one missing-only retry. No path makes more than two model calls for a batch.

    Existing ``answer_batch`` validation remains authoritative, so malformed retry
    output, duplicate ids, empty values, unexpected ids, or still-missing answers
    fail closed instead of being repaired or invented locally.

    Targeted practice may opt into ``recover_unexpected_initial_ids``. In that mode,
    unexpected rows in the *initial* response are discarded only when at least one
    expected exercise is missing, and the adapter retries exactly those missing
    exercise ids once. The recovery response itself is never filtered, so any
    unexpected, duplicate, empty, or still-missing recovery id continues to fail
    closed in ``answer_batch``. Canonical Pyramid callers keep the conservative
    default for unexpected ids while still receiving malformed-response recovery.
    """

    def __init__(
        self,
        model: Any,
        *,
        recover_unexpected_initial_ids: bool = False,
    ) -> None:
        self._model = model
        self._recover_unexpected_initial_ids = recover_unexpected_initial_ids

    def invoke(self, messages: Sequence[object], *args: object, **kwargs: object) -> object:
        response = self._model.invoke(messages, *args, **kwargs)
        request = self._answer_request(messages)
        if request is None:
            return response

        try:
            parsed = _parse_json(_message_text(response), context="Roberta answer batch")
        except PyramidExamError:
            return self._retry_full_batch(messages, request, *args, **kwargs)
        if not isinstance(parsed, Mapping) or not isinstance(parsed.get("answers"), list):
            return self._retry_full_batch(messages, request, *args, **kwargs)

        exercises = request["exercises"]
        expected_ids = [str(item["exercise_id"]).strip() for item in exercises]
        expected = set(expected_ids)
        returned_ids: list[str] = []
        valid_rows: list[object] = []
        saw_unexpected = False
        for row in parsed["answers"]:
            if not isinstance(row, Mapping):
                return self._retry_full_batch(messages, request, *args, **kwargs)
            exercise_id = str(row.get("exercise_id", "")).strip()
            answer = str(row.get("answer", "")).strip()
            if not exercise_id or not answer:
                return self._retry_full_batch(messages, request, *args, **kwargs)
            if exercise_id not in expected:
                if not self._recover_unexpected_initial_ids:
                    return response
                saw_unexpected = True
                continue
            returned_ids.append(exercise_id)
            valid_rows.append(row)

        if len(returned_ids) != len(set(returned_ids)):
            return response

        returned = set(returned_ids)
        missing_ids = [exercise_id for exercise_id in expected_ids if exercise_id not in returned]
        if not missing_ids:
            # Never hide an unexpected extra when the expected batch is already
            # complete; the ordinary answer_batch validator must see and reject it.
            return response
        if saw_unexpected and not self._recover_unexpected_initial_ids:
            return response

        missing = set(missing_ids)
        retry_request = dict(request)
        retry_request["instruction"] = (
            "Recovery pass: answer every exercise in this reduced batch independently. "
            "Return an answers array with exactly one object per exercise, preserving exercise_id."
        )
        retry_request["exercises"] = [
            item for item in exercises if str(item["exercise_id"]).strip() in missing
        ]

        retry_messages = list(messages)
        retry_messages[-1] = HumanMessage(content=json.dumps(retry_request, ensure_ascii=False))
        retry_response = self._model.invoke(retry_messages, *args, **kwargs)
        retry_parsed = _parse_json(
            _message_text(retry_response),
            context="Roberta missing-answer recovery",
        )
        if not isinstance(retry_parsed, Mapping) or not isinstance(retry_parsed.get("answers"), list):
            raise PyramidExamError(
                "Roberta missing-answer recovery must return an object containing an answers array"
            )

        combined = valid_rows + list(retry_parsed["answers"])
        return AIMessage(content=json.dumps({"answers": combined}, ensure_ascii=False))

    def _retry_full_batch(
        self,
        messages: Sequence[object],
        request: Mapping[str, object],
        *args: object,
        **kwargs: object,
    ) -> object:
        retry_request = dict(request)
        retry_request["instruction"] = (
            "Recovery pass: the previous response was structurally invalid. "
            "Answer every exercise in this full batch independently. Return valid JSON matching "
            "the supplied schema exactly, with exactly one non-empty exercise_id and answer per exercise."
        )
        retry_messages = list(messages)
        retry_messages[-1] = HumanMessage(content=json.dumps(retry_request, ensure_ascii=False))
        return self._model.invoke(retry_messages, *args, **kwargs)

    @staticmethod
    def _answer_request(messages: Sequence[object]) -> dict[str, object] | None:
        if not messages:
            return None
        content = getattr(messages[-1], "content", None)
        if not isinstance(content, str):
            return None
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            return None
        if not isinstance(parsed, Mapping) or not isinstance(parsed.get("exercises"), list):
            return None

        exercises = parsed["exercises"]
        if not all(
            isinstance(item, Mapping) and str(item.get("exercise_id", "")).strip()
            for item in exercises
        ):
            return None
        return dict(parsed)
