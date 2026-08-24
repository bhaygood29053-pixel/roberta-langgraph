from __future__ import annotations

from dataclasses import dataclass
import hashlib
import random
from typing import Iterable, Mapping, Sequence


PYRAMID_CONTRACT = "roberta-pyramid-curriculum/v1"
CANONICAL_LEVEL_QUESTION_COUNT = 300
CANONICAL_INTEGRITY_QUESTION_COUNT = 50
MIN_INTEGRITY_ACCURACY = 0.90


@dataclass(frozen=True, slots=True)
class LevelSpec:
    level: int
    name: str
    domain: str
    pass_accuracy: float


LEVEL_SPECS: tuple[LevelSpec, ...] = (
    LevelSpec(1, "Fundamentals", "blockchain fundamentals", 0.85),
    LevelSpec(2, "Blockchain Mechanics", "blocks, nodes, consensus", 0.85),
    LevelSpec(3, "Transactions", "transaction lifecycle", 0.85),
    LevelSpec(4, "Cryptography", "hashes, keys, signatures", 0.85),
    LevelSpec(5, "Smart Contracts", "contract and program reasoning", 0.85),
    LevelSpec(6, "Tokenomics", "supply, inflation, burns, dilution", 0.88),
    LevelSpec(7, "Liquidity", "pools, depth, slippage, price impact", 0.88),
    LevelSpec(8, "Market Structure", "price, volume, market cap, FDV", 0.88),
    LevelSpec(9, "DeFi", "AMMs, staking, lending", 0.88),
    LevelSpec(10, "Advanced DeFi", "liquidations, bridges, complex protocols", 0.88),
    LevelSpec(11, "On-chain Analysis", "accounts, transactions, flows", 0.90),
    LevelSpec(12, "Wallet Relationships", "interaction without ownership overclaim", 0.90),
    LevelSpec(13, "Risk Reasoning", "multi-dimensional risk", 0.90),
    LevelSpec(14, "Adversarial Analysis", "misleading premises and traps", 0.90),
    LevelSpec(15, "Evidence Forensics", "provenance and conflicting evidence", 0.90),
    LevelSpec(16, "Intelligence Synthesis", "multiple evidence streams", 0.92),
    LevelSpec(17, "Cross-chain Reasoning", "chain-specific semantics", 0.92),
    LevelSpec(18, "Complex Investigations", "open multi-step investigations", 0.92),
    LevelSpec(19, "Red-team Mastery", "deliberately deceptive cases", 0.92),
    LevelSpec(20, "Grandmaster", "full-system synthesis", 0.95),
)


_LEVEL_BY_NUMBER = {spec.level: spec for spec in LEVEL_SPECS}


@dataclass(frozen=True, slots=True)
class Exercise:
    exercise_id: str
    curriculum_id: str
    level: int
    concept: str
    question: str
    expected_answer: str
    source_refs: tuple[str, ...]
    question_type: str = "application"
    subconcept: str | None = None
    difficulty: int | None = None
    required_reasoning_points: tuple[str, ...] = ()
    forbidden_inferences: tuple[str, ...] = ()
    grading_rubric_id: str | None = None
    integrity_question: bool = False
    boss_question: bool = False
    requires_live_data: bool = False

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> "Exercise":
        def strings(name: str) -> tuple[str, ...]:
            raw = value.get(name, ())
            if raw is None:
                return ()
            if not isinstance(raw, (list, tuple)) or not all(isinstance(item, str) for item in raw):
                raise ValueError(f"{name} must be an array of strings")
            return tuple(raw)

        exercise = cls(
            exercise_id=str(value.get("exercise_id", "")).strip(),
            curriculum_id=str(value.get("curriculum_id", "")).strip(),
            level=int(value.get("level", 0)),
            concept=str(value.get("concept", "")).strip(),
            question=str(value.get("question", "")).strip(),
            expected_answer=str(value.get("expected_answer", "")).strip(),
            source_refs=strings("source_refs"),
            question_type=str(value.get("question_type", "application")).strip(),
            subconcept=(str(value["subconcept"]).strip() if value.get("subconcept") is not None else None),
            difficulty=(int(value["difficulty"]) if value.get("difficulty") is not None else None),
            required_reasoning_points=strings("required_reasoning_points"),
            forbidden_inferences=strings("forbidden_inferences"),
            grading_rubric_id=(
                str(value["grading_rubric_id"]).strip() if value.get("grading_rubric_id") is not None else None
            ),
            integrity_question=bool(value.get("integrity_question", False)),
            boss_question=bool(value.get("boss_question", False)),
            requires_live_data=bool(value.get("requires_live_data", False)),
        )
        exercise.validate()
        return exercise

    def validate(self) -> None:
        if not self.exercise_id:
            raise ValueError("exercise_id is required")
        if not self.curriculum_id:
            raise ValueError("curriculum_id is required")
        if self.level not in _LEVEL_BY_NUMBER:
            raise ValueError("level must be between 1 and 20")
        if not self.concept:
            raise ValueError("concept is required")
        if not self.question:
            raise ValueError("question is required")
        if not self.expected_answer:
            raise ValueError("expected_answer is required")
        if not self.source_refs:
            raise ValueError("at least one source_ref is required")
        if self.difficulty is not None and not 1 <= self.difficulty <= 20:
            raise ValueError("difficulty must be between 1 and 20")


@dataclass(frozen=True, slots=True)
class LevelResult:
    level: int
    total_questions: int
    correct_questions: int
    integrity_total: int
    integrity_correct: int
    boss_passed: bool
    critical_failures: int
    passed: bool
    accuracy: float
    integrity_accuracy: float
    required_accuracy: float


def get_level_spec(level: int) -> LevelSpec:
    try:
        return _LEVEL_BY_NUMBER[level]
    except KeyError as exc:
        raise ValueError("level must be between 1 and 20") from exc


def derive_level_seed(run_seed: str | int, curriculum_id: str, level: int) -> int:
    get_level_spec(level)
    material = f"{PYRAMID_CONTRACT}|{run_seed}|{curriculum_id}|{level}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(material).digest()[:8], "big", signed=False)


def select_level_exercises(
    exercises: Iterable[Exercise],
    *,
    curriculum_id: str,
    level: int,
    run_seed: str | int,
    count: int = CANONICAL_LEVEL_QUESTION_COUNT,
) -> tuple[Exercise, ...]:
    if count <= 0:
        raise ValueError("count must be positive")
    get_level_spec(level)
    eligible = [item for item in exercises if item.curriculum_id == curriculum_id and item.level == level]
    ids = [item.exercise_id for item in eligible]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate exercise_id in eligible level bank")
    if len(eligible) < count:
        raise ValueError(f"level {level} needs at least {count} eligible exercises; found {len(eligible)}")

    rng = random.Random(derive_level_seed(run_seed, curriculum_id, level))
    if count != CANONICAL_LEVEL_QUESTION_COUNT:
        return tuple(rng.sample(eligible, count))

    overlapping_bosses = [item for item in eligible if item.boss_question and item.integrity_question]
    if overlapping_bosses:
        raise ValueError(f"level {level} Boss Questions cannot also be integrity questions")

    bosses = [item for item in eligible if item.boss_question]
    if not bosses:
        raise ValueError(f"level {level} needs at least one Boss Question")
    boss = rng.choice(bosses)

    integrity_pool = [item for item in eligible if item.integrity_question]
    if len(integrity_pool) < CANONICAL_INTEGRITY_QUESTION_COUNT:
        raise ValueError(
            f"level {level} needs at least {CANONICAL_INTEGRITY_QUESTION_COUNT} non-Boss integrity questions; "
            f"found {len(integrity_pool)}"
        )
    integrity = rng.sample(integrity_pool, CANONICAL_INTEGRITY_QUESTION_COUNT)
    selected_ids = {boss.exercise_id, *(item.exercise_id for item in integrity)}
    ordinary_pool = [
        item
        for item in eligible
        if item.exercise_id not in selected_ids
        and not item.integrity_question
        and not item.boss_question
    ]
    ordinary_count = count - CANONICAL_INTEGRITY_QUESTION_COUNT - 1
    if len(ordinary_pool) < ordinary_count:
        raise ValueError(f"level {level} does not contain enough remaining exercises for a canonical exam")
    selected = rng.sample(ordinary_pool, ordinary_count) + integrity
    rng.shuffle(selected)
    selected.append(boss)
    return tuple(selected)


def evaluate_level(
    *,
    level: int,
    total_questions: int,
    correct_questions: int,
    integrity_total: int,
    integrity_correct: int,
    boss_passed: bool,
    critical_failures: int = 0,
    canonical_exam: bool = True,
) -> LevelResult:
    spec = get_level_spec(level)
    if total_questions <= 0:
        raise ValueError("total_questions must be positive")
    if canonical_exam and total_questions != CANONICAL_LEVEL_QUESTION_COUNT:
        raise ValueError(f"canonical Pyramid levels require {CANONICAL_LEVEL_QUESTION_COUNT} questions")
    if canonical_exam and integrity_total != CANONICAL_INTEGRITY_QUESTION_COUNT:
        raise ValueError(f"canonical Pyramid levels require {CANONICAL_INTEGRITY_QUESTION_COUNT} integrity questions")
    if not 0 <= correct_questions <= total_questions:
        raise ValueError("correct_questions must be between 0 and total_questions")
    if integrity_total < 0 or not 0 <= integrity_correct <= integrity_total:
        raise ValueError("invalid integrity counts")
    if critical_failures < 0:
        raise ValueError("critical_failures cannot be negative")

    accuracy = correct_questions / total_questions
    integrity_accuracy = 1.0 if integrity_total == 0 else integrity_correct / integrity_total
    passed = (
        accuracy >= spec.pass_accuracy
        and integrity_accuracy >= MIN_INTEGRITY_ACCURACY
        and boss_passed
        and critical_failures == 0
    )
    return LevelResult(
        level=level,
        total_questions=total_questions,
        correct_questions=correct_questions,
        integrity_total=integrity_total,
        integrity_correct=integrity_correct,
        boss_passed=boss_passed,
        critical_failures=critical_failures,
        passed=passed,
        accuracy=accuracy,
        integrity_accuracy=integrity_accuracy,
        required_accuracy=spec.pass_accuracy,
    )


def next_level_after(result: LevelResult) -> int | None:
    if not result.passed:
        return 1
    if result.level == 20:
        return None
    return result.level + 1


def validate_curriculum(exercises: Sequence[Exercise]) -> None:
    seen: set[str] = set()
    curriculum_ids: set[str] = set()
    for exercise in exercises:
        exercise.validate()
        if exercise.exercise_id in seen:
            raise ValueError(f"duplicate exercise_id: {exercise.exercise_id}")
        seen.add(exercise.exercise_id)
        curriculum_ids.add(exercise.curriculum_id)
    if len(curriculum_ids) > 1:
        raise ValueError("a curriculum validation batch must contain one curriculum_id")
