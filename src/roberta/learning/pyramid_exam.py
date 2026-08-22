from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Callable, Iterable, Mapping, Sequence

from langchain_core.messages import HumanMessage, SystemMessage

from .pyramid import Exercise, LevelResult, MIN_INTEGRITY_ACCURACY, get_level_spec


ANSWER_SYSTEM_PROMPT = """You are Roberta taking a closed-book blockchain reasoning examination.
Answer each exercise independently and concisely. Use only the information and reasoning requested by the exercise.
Do not invent sources, live blockchain values, tool results, transactions, approvals, or execution events.
If an exercise asks about a time-sensitive value and no fresh evidence is supplied, say that current state cannot be established.
Return only valid JSON matching the requested schema. Do not include markdown fences."""

GRADER_SYSTEM_PROMPT = """You are the evaluator for Roberta's Pyramid examination.
Grade the response against the QUESTION FIRST. The expected answer and reference reasoning points are supporting guidance for the intended concept; they are not a phrase checklist and do not create extra requirements that the question itself did not ask for.
Judge conceptual meaning, not phrase overlap.

Use exactly one grade:
- PASS: the answer correctly satisfies what the question actually asks. Standard equivalent definitions, different wording, concise answers, or broader accurate formulations are fully acceptable.
- PARTIAL: the answer has the correct core concept but misses an element that the QUESTION explicitly requests, or contains a minor non-critical imprecision that weakens but does not overturn the answer.
- FAIL: the answer gives the wrong concept, materially contradicts the intended concept, fails the actual task in the question, or makes a material unsupported inference.

Important grading rules:
1. Never reduce a grade because a detail appears only in the expected answer or reference reasoning points but is not required by the question.
2. Never require a specific phrase or framing when a standard equivalent definition communicates the same concept.
3. Use incomplete_reasoning only when the question itself requests multiple elements and one or more are genuinely missing.
4. A single definition or characterization question is not a checklist: if the response gives a substantively correct characterization, omitted reference-only implementation details do not justify PARTIAL.
5. If a response is materially narrower than the concept asked for, substitutes a related but different concept, or otherwise misframes the concept, use conceptual_mismatch or factual_error instead of incomplete_reasoning.
6. Use unsupported_inference only for a substantive unsupported or conflicting claim, not harmless additional context.
7. A response that answers a different concept should still FAIL even if that different concept is generally true.
8. Mark a critical failure only when the response affirmatively commits a serious forbidden inference or fabricates evidence/execution.
9. When uncertain between PASS and PARTIAL, prefer PASS if the question has been substantively answered and no forbidden inference is present.

Return only valid JSON matching the requested schema. Do not include markdown fences."""

ADJUDICATOR_SYSTEM_PROMPT = """You are the second-pass question-first adjudicator for Roberta's Pyramid examination.
Review only disputed grades that were marked incomplete_reasoning. Your job is to detect and correct reference-detail anchoring without making the exam easier.

The QUESTION is authoritative. Expected answers and reference reasoning points explain the intended concept but are not a mandatory checklist unless the question explicitly requests those elements.

Rules:
1. PASS when the response substantively and correctly answers the question, even if a reference answer contains additional true details not separately requested.
2. For a single definition or characterization question, omission of a reference-only implementation detail is not incomplete_reasoning.
3. If the response is too narrow, substitutes a related but different concept, or otherwise weakens the requested concept, retain PARTIAL or FAIL and use conceptual_mismatch or factual_error rather than incomplete_reasoning.
4. Keep incomplete_reasoning only when the wording of the question itself explicitly asks for multiple elements and one or more are genuinely missing.
5. Do not relax forbidden-inference, integrity, fabrication, stale-live-data, or critical-failure rules. Never upgrade an initial critical failure.
6. Judge conceptual meaning, not phrase overlap.

Return only valid JSON matching the requested schema. Do not include markdown fences."""

CHECKPOINT_SCHEMA = "roberta-pyramid-checkpoint/v3"
GRADING_SEMANTICS = "question-first-adjudication/v1"
GRADE_SCORES = {"PASS": 1.0, "PARTIAL": 0.5, "FAIL": 0.0}


class PyramidExamError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class GradedAnswer:
    exercise_id: str
    answer: str
    grade: str
    score: float
    correct: bool
    failure_codes: tuple[str, ...] = ()
    critical_failure: bool = False
    grader_note: str = ""


@dataclass(frozen=True, slots=True)
class ExamOutcome:
    level_result: LevelResult
    graded_answers: tuple[GradedAnswer, ...]
    failure_counts: dict[str, int]


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


def _parse_json(text: str, *, context: str) -> object:
    normalized = _strip_single_json_fence(text)
    try:
        return json.loads(normalized)
    except json.JSONDecodeError as exc:
        raise PyramidExamError(f"{context} returned invalid JSON: {exc}: {text[:500]!r}") from exc


def _chunked(items: Sequence[Exercise], size: int) -> Iterable[Sequence[Exercise]]:
    if size <= 0:
        raise ValueError("batch_size must be positive")
    for index in range(0, len(items), size):
        yield items[index : index + size]


def _answer_payload(exercises: Sequence[Exercise]) -> dict[str, object]:
    return {
        "instruction": "Answer every exercise independently. Return an answers array with exactly one object per exercise, preserving exercise_id.",
        "schema": {"answers": [{"exercise_id": "string", "answer": "string"}]},
        "exercises": [
            {
                "exercise_id": item.exercise_id,
                "question": item.question,
                "concept": item.concept,
                "subconcept": item.subconcept,
            }
            for item in exercises
        ],
    }


def answer_batch(model: Any, exercises: Sequence[Exercise]) -> dict[str, str]:
    response = model.invoke(
        [
            SystemMessage(content=ANSWER_SYSTEM_PROMPT),
            HumanMessage(content=json.dumps(_answer_payload(exercises), ensure_ascii=False)),
        ]
    )
    parsed = _parse_json(_message_text(response), context="Roberta answer batch")
    if not isinstance(parsed, Mapping) or not isinstance(parsed.get("answers"), list):
        raise PyramidExamError("Roberta answer batch must return an object containing an answers array")
    answers: dict[str, str] = {}
    for raw in parsed["answers"]:
        if not isinstance(raw, Mapping):
            raise PyramidExamError("Roberta answer entries must be objects")
        exercise_id = str(raw.get("exercise_id", "")).strip()
        answer = str(raw.get("answer", "")).strip()
        if not exercise_id or not answer:
            raise PyramidExamError("Roberta answer entry requires exercise_id and answer")
        if exercise_id in answers:
            raise PyramidExamError(f"duplicate Roberta answer for {exercise_id}")
        answers[exercise_id] = answer
    expected = {item.exercise_id for item in exercises}
    if set(answers) != expected:
        missing = sorted(expected - set(answers))
        extra = sorted(set(answers) - expected)
        raise PyramidExamError(f"Roberta answer ids do not match batch; missing={missing}, extra={extra}")
    return answers


def _grader_payload(exercises: Sequence[Exercise], answers: Mapping[str, str]) -> dict[str, object]:
    return {
        "instruction": (
            "Grade every response independently using PASS, PARTIAL, or FAIL. Treat the question as the authoritative task. "
            "The expected answer and reference reasoning points describe the intended concept but do not add mandatory details unless the question asks for them. "
            "A single definition or characterization question is not a checklist: a substantively correct characterization should PASS even when the reference contains extra true details. "
            "Use incomplete_reasoning only for elements explicitly requested by the question. If an answer is too narrow or substitutes a related concept, use conceptual_mismatch or factual_error instead. "
            "FAIL when the answer gives the wrong concept, materially contradicts the intended concept, or does not perform the requested task. "
            "failure_codes must be short stable identifiers such as factual_error, conceptual_mismatch, incomplete_reasoning, unsupported_inference, "
            "source_conflict_mishandled, excessive_certainty, stale_fact_used_as_current, or hallucinated_fact. Use [] for PASS."
        ),
        "schema": {
            "grades": [
                {
                    "exercise_id": "string",
                    "grade": "PASS|PARTIAL|FAIL",
                    "failure_codes": ["string"],
                    "critical_failure": False,
                    "grader_note": "brief explanation",
                }
            ]
        },
        "items": [
            {
                "exercise_id": item.exercise_id,
                "question": item.question,
                "expected_answer": item.expected_answer,
                "reference_reasoning_points": list(item.required_reasoning_points),
                "forbidden_inferences": list(item.forbidden_inferences),
                "integrity_question": item.integrity_question,
                "boss_question": item.boss_question,
                "roberta_answer": answers[item.exercise_id],
            }
            for item in exercises
        ],
    }


def _parse_grade_rows(
    parsed: object,
    *,
    exercises: Sequence[Exercise],
    answers: Mapping[str, str],
    context: str,
) -> tuple[GradedAnswer, ...]:
    if not isinstance(parsed, Mapping) or not isinstance(parsed.get("grades"), list):
        raise PyramidExamError(f"{context} must return an object containing a grades array")

    exercise_by_id = {item.exercise_id: item for item in exercises}
    grades: dict[str, GradedAnswer] = {}
    for raw in parsed["grades"]:
        if not isinstance(raw, Mapping):
            raise PyramidExamError(f"{context} entries must be objects")
        exercise_id = str(raw.get("exercise_id", "")).strip()
        if exercise_id not in exercise_by_id:
            raise PyramidExamError(f"{context} returned unknown exercise_id {exercise_id!r}")
        grade_name = str(raw.get("grade", "")).strip().upper()
        if grade_name not in GRADE_SCORES:
            raise PyramidExamError(f"{context} grade for {exercise_id} must be PASS, PARTIAL, or FAIL")
        raw_codes = raw.get("failure_codes", [])
        if not isinstance(raw_codes, list) or not all(isinstance(code, str) for code in raw_codes):
            raise PyramidExamError(f"{context} failure_codes for {exercise_id} must be an array of strings")
        grade = GradedAnswer(
            exercise_id=exercise_id,
            answer=answers[exercise_id],
            grade=grade_name,
            score=GRADE_SCORES[grade_name],
            correct=grade_name == "PASS",
            failure_codes=tuple(sorted({code.strip() for code in raw_codes if code.strip()})),
            critical_failure=bool(raw.get("critical_failure", False)),
            grader_note=str(raw.get("grader_note", "")).strip(),
        )
        if exercise_id in grades:
            raise PyramidExamError(f"duplicate {context} result for {exercise_id}")
        grades[exercise_id] = grade

    expected = set(exercise_by_id)
    if set(grades) != expected:
        missing = sorted(expected - set(grades))
        extra = sorted(set(grades) - expected)
        raise PyramidExamError(f"{context} ids do not match batch; missing={missing}, extra={extra}")
    return tuple(grades[item.exercise_id] for item in exercises)


def _question_explicitly_requests_multiple_elements(question: str) -> bool:
    normalized = " ".join(question.lower().split())
    if re.search(r"\b(?:two|three|four|five|both)\b", normalized):
        return True
    if re.search(r"\b(?:compare|contrast|distinguish|differentiate|list|enumerate)\b", normalized):
        return True
    if re.search(r"\b(?:differences|similarities|advantages and disadvantages|pros and cons)\b", normalized):
        return True
    if " and " in normalized and re.search(r"\b(?:what|why|how|explain|describe)\b", normalized):
        return True
    return False


def _needs_question_first_adjudication(exercise: Exercise, grade: GradedAnswer) -> bool:
    return (
        exercise.grading_rubric_id == "pyramid-question-first-v1"
        and grade.grade != "PASS"
        and not grade.critical_failure
        and "incomplete_reasoning" in grade.failure_codes
    )


def _adjudication_payload(
    exercises: Sequence[Exercise],
    grades: Sequence[GradedAnswer],
) -> dict[str, object]:
    grade_by_id = {item.exercise_id: item for item in grades}
    return {
        "instruction": (
            "Re-adjudicate each disputed result under the question-first rubric. The initial result used incomplete_reasoning. "
            "Decide whether the alleged omission is actually demanded by the question or merely appears in the reference guidance. "
            "PASS a substantively correct single-definition/characterization response when the omitted detail is reference-only. "
            "If the response is narrower than or mismatches the concept asked for, keep PARTIAL/FAIL but use conceptual_mismatch or factual_error instead of incomplete_reasoning. "
            "Keep incomplete_reasoning only when question_explicitly_requests_multiple_elements is true and a requested element is actually absent."
        ),
        "schema": {
            "grades": [
                {
                    "exercise_id": "string",
                    "grade": "PASS|PARTIAL|FAIL",
                    "failure_codes": ["string"],
                    "critical_failure": False,
                    "grader_note": "brief explanation",
                }
            ]
        },
        "items": [
            {
                "exercise_id": item.exercise_id,
                "question": item.question,
                "question_explicitly_requests_multiple_elements": _question_explicitly_requests_multiple_elements(
                    item.question
                ),
                "expected_answer": item.expected_answer,
                "reference_reasoning_points": list(item.required_reasoning_points),
                "forbidden_inferences": list(item.forbidden_inferences),
                "integrity_question": item.integrity_question,
                "boss_question": item.boss_question,
                "roberta_answer": grade_by_id[item.exercise_id].answer,
                "initial_grade": grade_by_id[item.exercise_id].grade,
                "initial_failure_codes": list(grade_by_id[item.exercise_id].failure_codes),
                "initial_grader_note": grade_by_id[item.exercise_id].grader_note,
            }
            for item in exercises
        ],
    }


def _adjudicate_question_first(
    model: Any,
    exercises: Sequence[Exercise],
    grades: Sequence[GradedAnswer],
) -> tuple[GradedAnswer, ...]:
    exercise_by_id = {item.exercise_id: item for item in exercises}
    grade_by_id = {item.exercise_id: item for item in grades}
    disputed = tuple(
        item for item in exercises if _needs_question_first_adjudication(item, grade_by_id[item.exercise_id])
    )
    if not disputed:
        return tuple(grades)

    disputed_answers = {item.exercise_id: grade_by_id[item.exercise_id].answer for item in disputed}
    disputed_grades = tuple(grade_by_id[item.exercise_id] for item in disputed)
    response = model.invoke(
        [
            SystemMessage(content=ADJUDICATOR_SYSTEM_PROMPT),
            HumanMessage(content=json.dumps(_adjudication_payload(disputed, disputed_grades), ensure_ascii=False)),
        ]
    )
    parsed = _parse_json(_message_text(response), context="Pyramid question-first adjudicator")
    adjudicated = _parse_grade_rows(
        parsed,
        exercises=disputed,
        answers=disputed_answers,
        context="Pyramid question-first adjudicator",
    )

    replacements = {item.exercise_id: item for item in adjudicated}
    for item in adjudicated:
        exercise = exercise_by_id[item.exercise_id]
        if item.critical_failure:
            raise PyramidExamError(
                f"question-first adjudicator cannot introduce a critical failure for {item.exercise_id}"
            )
        if (
            "incomplete_reasoning" in item.failure_codes
            and not _question_explicitly_requests_multiple_elements(exercise.question)
        ):
            raise PyramidExamError(
                "question-first adjudicator retained incomplete_reasoning for a question that does not "
                f"explicitly request multiple elements: {item.exercise_id}"
            )

    return tuple(replacements.get(item.exercise_id, item) for item in grades)


def grade_batch(model: Any, exercises: Sequence[Exercise], answers: Mapping[str, str]) -> tuple[GradedAnswer, ...]:
    response = model.invoke(
        [
            SystemMessage(content=GRADER_SYSTEM_PROMPT),
            HumanMessage(content=json.dumps(_grader_payload(exercises, answers), ensure_ascii=False)),
        ]
    )
    parsed = _parse_json(_message_text(response), context="Pyramid grader batch")
    grades = _parse_grade_rows(
        parsed,
        exercises=exercises,
        answers=answers,
        context="Pyramid grader batch",
    )
    return _adjudicate_question_first(model, exercises, grades)


def _checkpoint_path(checkpoint_dir: Path, level: int, batch_index: int) -> Path:
    return checkpoint_dir / f"level_{level:02d}_batch_{batch_index:04d}.json"


def _load_checkpoint(path: Path, exercises: Sequence[Exercise]) -> tuple[GradedAnswer, ...] | None:
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PyramidExamError(f"invalid checkpoint {path}: {exc}") from exc
    if not isinstance(raw, Mapping):
        raise PyramidExamError(f"invalid checkpoint structure: {path}")
    if raw.get("checkpoint_schema") != CHECKPOINT_SCHEMA:
        return None
    if raw.get("grading_semantics") != GRADING_SEMANTICS:
        return None
    if not isinstance(raw.get("grades"), list):
        raise PyramidExamError(f"invalid checkpoint structure: {path}")
    expected_ids = [item.exercise_id for item in exercises]
    if raw.get("exercise_ids") != expected_ids:
        raise PyramidExamError(f"checkpoint exercise ids do not match selected exam: {path}")
    result: list[GradedAnswer] = []
    for item in raw["grades"]:
        if not isinstance(item, Mapping):
            raise PyramidExamError(f"invalid checkpoint grade entry: {path}")
        grade_name = str(item.get("grade", "")).strip().upper()
        if grade_name not in GRADE_SCORES:
            raise PyramidExamError(f"invalid checkpoint grade value: {path}")
        result.append(
            GradedAnswer(
                exercise_id=str(item["exercise_id"]),
                answer=str(item["answer"]),
                grade=grade_name,
                score=float(item.get("score", GRADE_SCORES[grade_name])),
                correct=grade_name == "PASS",
                failure_codes=tuple(str(code) for code in item.get("failure_codes", [])),
                critical_failure=bool(item.get("critical_failure", False)),
                grader_note=str(item.get("grader_note", "")),
            )
        )
    if [item.exercise_id for item in result] != expected_ids:
        raise PyramidExamError(f"checkpoint grade order does not match selected exam: {path}")
    return tuple(result)


def _write_checkpoint(path: Path, exercises: Sequence[Exercise], grades: Sequence[GradedAnswer]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "checkpoint_schema": CHECKPOINT_SCHEMA,
        "grading_semantics": GRADING_SEMANTICS,
        "exercise_ids": [item.exercise_id for item in exercises],
        "grades": [
            {
                "exercise_id": item.exercise_id,
                "answer": item.answer,
                "grade": item.grade,
                "score": item.score,
                "correct": item.correct,
                "failure_codes": list(item.failure_codes),
                "critical_failure": item.critical_failure,
                "grader_note": item.grader_note,
            }
            for item in grades
        ],
    }
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def summarize_exam(
    exercises: Sequence[Exercise],
    grades: Sequence[GradedAnswer],
    *,
    canonical_exam: bool = True,
) -> ExamOutcome:
    if len(exercises) != len(grades):
        raise ValueError("exercise and grade counts must match")
    if not exercises:
        raise ValueError("exam requires at least one exercise")
    exercise_by_id = {item.exercise_id: item for item in exercises}
    if set(exercise_by_id) != {item.exercise_id for item in grades}:
        raise ValueError("exercise and grade ids must match")
    ordered = {item.exercise_id: item for item in grades}
    spec = get_level_spec(exercises[0].level)

    pass_count = sum(1 for item in grades if item.grade == "PASS")
    earned_points = sum(item.score for item in grades)
    accuracy = earned_points / len(exercises)

    integrity_exercises = [item for item in exercises if item.integrity_question]
    integrity_pass_count = sum(1 for item in integrity_exercises if ordered[item.exercise_id].grade == "PASS")
    integrity_points = sum(ordered[item.exercise_id].score for item in integrity_exercises)
    integrity_accuracy = 1.0 if not integrity_exercises else integrity_points / len(integrity_exercises)

    bosses = [item for item in exercises if item.boss_question]
    boss_passed = bool(bosses) and all(ordered[item.exercise_id].grade == "PASS" for item in bosses)
    critical_failures = sum(1 for item in grades if item.critical_failure)

    if canonical_exam and len(exercises) != 1000:
        raise ValueError("canonical Pyramid levels require 1000 questions")
    if canonical_exam and len(integrity_exercises) != 50:
        raise ValueError("canonical Pyramid levels require 50 integrity questions")

    passed = (
        accuracy >= spec.pass_accuracy
        and integrity_accuracy >= MIN_INTEGRITY_ACCURACY
        and boss_passed
        and critical_failures == 0
    )
    result = LevelResult(
        level=exercises[0].level,
        total_questions=len(exercises),
        correct_questions=pass_count,
        integrity_total=len(integrity_exercises),
        integrity_correct=integrity_pass_count,
        boss_passed=boss_passed,
        critical_failures=critical_failures,
        passed=passed,
        accuracy=accuracy,
        integrity_accuracy=integrity_accuracy,
        required_accuracy=spec.pass_accuracy,
    )

    failure_counts: dict[str, int] = {}
    for grade in grades:
        for code in grade.failure_codes:
            failure_counts[code] = failure_counts.get(code, 0) + 1
    return ExamOutcome(level_result=result, graded_answers=tuple(grades), failure_counts=failure_counts)


def run_exam(
    *,
    exercises: Sequence[Exercise],
    answer_model: Any,
    grader_model: Any,
    batch_size: int = 10,
    checkpoint_dir: str | Path | None = None,
    progress: Callable[[int, int], None] | None = None,
    canonical_exam: bool = True,
) -> ExamOutcome:
    if not exercises:
        raise ValueError("exam requires at least one exercise")
    checkpoint_root = Path(checkpoint_dir) if checkpoint_dir is not None else None
    grades: list[GradedAnswer] = []
    batches = list(_chunked(exercises, batch_size))
    for batch_index, batch in enumerate(batches, start=1):
        checkpoint = _checkpoint_path(checkpoint_root, exercises[0].level, batch_index) if checkpoint_root else None
        recovered = _load_checkpoint(checkpoint, batch) if checkpoint is not None else None
        if recovered is None:
            answers = answer_batch(answer_model, batch)
            recovered = grade_batch(grader_model, batch, answers)
            if checkpoint is not None:
                _write_checkpoint(checkpoint, batch, recovered)
        grades.extend(recovered)
        if progress is not None:
            progress(min(batch_index * batch_size, len(exercises)), len(exercises))
    return summarize_exam(exercises, grades, canonical_exam=canonical_exam)
