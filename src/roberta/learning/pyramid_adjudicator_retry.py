from __future__ import annotations

import json
from typing import Any, Mapping

from langchain_core.messages import HumanMessage

from roberta.models import create_runtime_model

from .pyramid_exam import ADJUDICATOR_SYSTEM_PROMPT, PyramidExamError


_FORMAT_RETRY_INSTRUCTION = (
    "Your previous adjudication response could not be parsed as JSON. "
    "Repeat the exact same adjudication task using the exact same item set, question-first policy, "
    "critical-validation rules, and requested schema. This is a serialization-only retry. "
    "Do not add, remove, rename, or substitute exercise ids. Do not weaken or broaden any safety rule. "
    "Return only one valid JSON object and no markdown fences or commentary."
)
_SCHEMA_RETRY_INSTRUCTION = (
    "Your previous adjudication response was valid JSON but did not conform to the required adjudication schema. "
    "Repeat the exact same adjudication task using the exact same item set, Roberta answers, question-first policy, "
    "critical-validation rules, and requested schema. This is a schema-conformance-only retry. "
    "Return exactly one grade row for every requested exercise_id and no other ids. "
    "Each grade must be exactly PASS, PARTIAL, or FAIL. failure_codes must be an array of strings. "
    "Do not infer, normalize, repair, or substitute ids or grades from the prior response. "
    "Do not weaken or broaden any safety rule. Return only one valid JSON object and no markdown fences or commentary."
)
_ALLOWED_GRADES = frozenset({"PASS", "PARTIAL", "FAIL"})


def _message_text(response: object) -> str:
    content = getattr(response, "content", response)
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, Mapping):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts).strip()
    return str(content).strip()


def _strip_single_json_fence(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    first_newline = stripped.find("\n")
    if first_newline < 0:
        return stripped
    opening = stripped[:first_newline].strip().lower()
    if opening not in {"```", "```json"} or not stripped.endswith("```"):
        return stripped
    inner = stripped[first_newline + 1 : -3].strip()
    if "```" in inner:
        return stripped
    return inner


def _json_parse_error(response: object) -> json.JSONDecodeError | None:
    try:
        json.loads(_strip_single_json_fence(_message_text(response)))
    except json.JSONDecodeError as exc:
        return exc
    return None


def _parsed_json(response: object) -> object:
    return json.loads(_strip_single_json_fence(_message_text(response)))


def _is_pyramid_adjudication(messages: object) -> bool:
    if not isinstance(messages, (list, tuple)) or not messages:
        return False
    content = getattr(messages[0], "content", None)
    return isinstance(content, str) and content == ADJUDICATOR_SYSTEM_PROMPT


def _adjudication_expected_ids(messages: object) -> tuple[str, ...]:
    if not isinstance(messages, (list, tuple)) or len(messages) < 2:
        raise PyramidExamError("Pyramid adjudicator request is missing its payload")
    raw_payload = getattr(messages[1], "content", None)
    if not isinstance(raw_payload, str):
        raise PyramidExamError("Pyramid adjudicator request payload must be JSON text")
    try:
        payload = json.loads(raw_payload)
    except json.JSONDecodeError as exc:
        raise PyramidExamError("Pyramid adjudicator request payload is invalid JSON") from exc
    if not isinstance(payload, Mapping) or not isinstance(payload.get("items"), list):
        raise PyramidExamError("Pyramid adjudicator request payload must contain an items array")
    ids: list[str] = []
    for item in payload["items"]:
        if not isinstance(item, Mapping):
            raise PyramidExamError("Pyramid adjudicator request items must be objects")
        exercise_id = item.get("exercise_id")
        if not isinstance(exercise_id, str) or not exercise_id.strip():
            raise PyramidExamError("Pyramid adjudicator request item requires exercise_id")
        ids.append(exercise_id.strip())
    if len(ids) != len(set(ids)):
        raise PyramidExamError("Pyramid adjudicator request contains duplicate exercise ids")
    return tuple(ids)


def _adjudication_schema_error(response: object, messages: object) -> str | None:
    parsed = _parsed_json(response)
    if not isinstance(parsed, Mapping) or not isinstance(parsed.get("grades"), list):
        return "response must be an object containing a grades array"

    expected_ids = _adjudication_expected_ids(messages)
    expected_set = set(expected_ids)
    seen: set[str] = set()
    for raw in parsed["grades"]:
        if not isinstance(raw, Mapping):
            return "grade entries must be objects"
        exercise_id = raw.get("exercise_id")
        if not isinstance(exercise_id, str) or not exercise_id.strip():
            return "every grade entry must contain a non-empty exercise_id string"
        exercise_id = exercise_id.strip()
        if exercise_id not in expected_set:
            return f"unknown exercise_id {exercise_id!r}"
        if exercise_id in seen:
            return f"duplicate exercise_id {exercise_id!r}"
        seen.add(exercise_id)

        grade = raw.get("grade")
        if not isinstance(grade, str) or grade.strip().upper() not in _ALLOWED_GRADES:
            return f"grade for {exercise_id} must be PASS, PARTIAL, or FAIL"
        failure_codes = raw.get("failure_codes", [])
        if not isinstance(failure_codes, list) or not all(isinstance(code, str) for code in failure_codes):
            return f"failure_codes for {exercise_id} must be an array of strings"

    if seen != expected_set:
        missing = sorted(expected_set - seen)
        extra = sorted(seen - expected_set)
        return f"grade ids do not match requested item set; missing={missing}, extra={extra}"
    return None


class PyramidAdjudicatorJsonRetryModel:
    """Boundedly recover Pyramid adjudicator JSON syntax and schema conformance only."""

    def __init__(self, model: Any) -> None:
        self._model = model

    def __getattr__(self, name: str) -> Any:
        return getattr(self._model, name)

    def _invoke_with_format_retry(
        self,
        messages: object,
        *args: object,
        **kwargs: object,
    ) -> Any:
        response = self._model.invoke(messages, *args, **kwargs)
        first_error = _json_parse_error(response)
        if first_error is None:
            return response

        retry_notice = HumanMessage(
            content=json.dumps(
                {
                    "format_retry": 1,
                    "instruction": _FORMAT_RETRY_INSTRUCTION,
                    "prior_parse_error": {
                        "message": first_error.msg,
                        "line": first_error.lineno,
                        "column": first_error.colno,
                    },
                },
                ensure_ascii=False,
            )
        )
        retry_messages = list(messages) + [retry_notice]
        retried = self._model.invoke(retry_messages, *args, **kwargs)
        second_error = _json_parse_error(retried)
        if second_error is not None:
            raise PyramidExamError(
                "Pyramid adjudicator JSON format retry exhausted after one bounded retry: "
                f"{second_error.msg} at line {second_error.lineno} column {second_error.colno}"
            ) from second_error
        return retried

    def invoke(self, messages: object, *args: object, **kwargs: object) -> Any:
        if not _is_pyramid_adjudication(messages):
            return self._model.invoke(messages, *args, **kwargs)

        response = self._invoke_with_format_retry(messages, *args, **kwargs)
        first_schema_error = _adjudication_schema_error(response, messages)
        if first_schema_error is None:
            return response

        retry_notice = HumanMessage(
            content=json.dumps(
                {
                    "schema_retry": 1,
                    "instruction": _SCHEMA_RETRY_INSTRUCTION,
                    "prior_schema_error": first_schema_error,
                },
                ensure_ascii=False,
            )
        )
        retry_messages = list(messages) + [retry_notice]
        retried = self._invoke_with_format_retry(retry_messages, *args, **kwargs)
        second_schema_error = _adjudication_schema_error(retried, messages)
        if second_schema_error is not None:
            raise PyramidExamError(
                "Pyramid adjudicator schema retry exhausted after one bounded retry: "
                f"{second_schema_error}"
            )
        return retried


def create_pyramid_runtime_model() -> PyramidAdjudicatorJsonRetryModel:
    """Create the normal runtime model with Pyramid-only adjudicator response recovery."""
    return PyramidAdjudicatorJsonRetryModel(create_runtime_model())