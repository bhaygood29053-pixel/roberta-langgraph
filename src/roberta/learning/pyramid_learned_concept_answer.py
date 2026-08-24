from __future__ import annotations

import json
from typing import Any, Mapping, Sequence

from langchain_core.messages import HumanMessage

from .pyramid_learned_concepts import (
    LearnedConcept,
    PYRAMID_LEARNED_CONCEPT_MEMORY_CONTRACT,
    PyramidLearnedConceptError,
)


class PyramidLearnedConceptAnswerModel:
    """Attach matching verified concept memory to Pyramid answer requests only.

    The caller must pre-scope `concepts` to one curriculum and level. The normal
    Pyramid answer payload remains unchanged: matching is by concept/subconcept,
    while the grader continues to receive its ordinary, unmodified request.
    """

    def __init__(self, model: Any, concepts: Sequence[LearnedConcept]) -> None:
        if not concepts:
            raise PyramidLearnedConceptError("learned concept answer model requires at least one concept")
        scopes = {(item.curriculum_id, item.level) for item in concepts}
        if len(scopes) != 1:
            raise PyramidLearnedConceptError(
                "learned concepts supplied to one answer model must share one curriculum/level scope"
            )
        self._model = model
        self._scope = next(iter(scopes))
        self._concepts = {(item.concept, item.subconcept): item for item in concepts}
        if len(self._concepts) != len(concepts):
            raise PyramidLearnedConceptError(
                "learned concept keys must be unique within one curriculum/level scope"
            )

    @property
    def scope(self) -> tuple[str, int]:
        return self._scope

    def invoke(self, messages: Sequence[object], *args: object, **kwargs: object) -> object:
        request = self._answer_request(messages)
        if request is None:
            return self._model.invoke(messages, *args, **kwargs)

        raw_exercises = request.get("exercises")
        if not isinstance(raw_exercises, list):
            return self._model.invoke(messages, *args, **kwargs)

        augmented: list[dict[str, object]] = []
        injected = 0
        for raw in raw_exercises:
            if not isinstance(raw, Mapping):
                raise PyramidLearnedConceptError("Pyramid answer exercise must be an object")
            if any(
                field in raw
                for field in (
                    "expected_answer",
                    "reference_reasoning_points",
                    "forbidden_inferences",
                    "remediation_context",
                    "source_evidence",
                )
            ):
                raise PyramidLearnedConceptError(
                    "Pyramid answer request contains prohibited grading/source material"
                )

            item = dict(raw)
            concept = item.get("concept")
            subconcept_raw = item.get("subconcept")
            subconcept = subconcept_raw if isinstance(subconcept_raw, str) else None
            if isinstance(concept, str):
                memory = self._concepts.get((concept, subconcept))
                if memory is not None:
                    item["learned_concept_memory"] = {
                        "contract": PYRAMID_LEARNED_CONCEPT_MEMORY_CONTRACT,
                        "principle": memory.principle,
                    }
                    injected += 1
            augmented.append(item)

        if injected == 0:
            return self._model.invoke(messages, *args, **kwargs)

        rewritten = dict(request)
        rewritten["instruction"] = (
            str(request.get("instruction", ""))
            + " You may use learned_concept_memory when present. It is previously verified internal "
            "curriculum knowledge, not source evidence, live state, or an answer key. Answer the "
            "actual question independently and do not mention the memory object."
        ).strip()
        rewritten["exercises"] = augmented

        updated = list(messages)
        updated[-1] = HumanMessage(content=json.dumps(rewritten, ensure_ascii=False))
        return self._model.invoke(updated, *args, **kwargs)

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
        return dict(parsed)
