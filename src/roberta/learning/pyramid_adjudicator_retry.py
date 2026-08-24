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


def _is_pyramid_adjudication(messages: object) -> bool:
    if not isinstance(messages, (list, tuple)) or not messages:
        return False
    content = getattr(messages[0], "content", None)
    return isinstance(content, str) and content == ADJUDICATOR_SYSTEM_PROMPT


class PyramidAdjudicatorJsonRetryModel:
    """Retry only malformed Pyramid adjudicator JSON, exactly once."""

    def __init__(self, model: Any) -> None:
        self._model = model

    def __getattr__(self, name: str) -> Any:
        return getattr(self._model, name)

    def invoke(self, messages: object, *args: object, **kwargs: object) -> Any:
        response = self._model.invoke(messages, *args, **kwargs)
        if not _is_pyramid_adjudication(messages):
            return response

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


def create_pyramid_runtime_model() -> PyramidAdjudicatorJsonRetryModel:
    """Create the normal runtime model with Pyramid-only adjudicator format recovery."""
    return PyramidAdjudicatorJsonRetryModel(create_runtime_model())
