from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import random
from typing import Mapping, Sequence

from .curriculum_io import validate_package
from .pyramid import Exercise
from .pyramid_critical_origin import inherit_critical_origins
from .pyramid_practice import PreparedTargetedPractice, TargetedPyramidPracticeError
from .pyramid_remediation import build_remediation_plan, load_seen_exercise_ids, load_weak_items


SUPPLEMENTAL_PRACTICE_CONTRACT = "roberta-pyramid-supplemental-practice/v1"
SUPPLEMENTAL_PRACTICE_VERSION = "1.0.0"
SUPPLEMENTAL_ID_PREFIX = "MB4E-SUP-L01-"
MB4E_SOURCE_REF = "mastering_blockchain_4e_2023"

WeaknessKey = tuple[str, str | None]


@dataclass(frozen=True, slots=True)
class SupplementalPreparation:
    prepared: PreparedTargetedPractice
    current_weak_ids: tuple[str, ...]
    current_weakness_keys: tuple[WeaknessKey, ...]
    selected_supplemental_ids: tuple[str, ...]
    selected_bank_sha256: str
    reconstruction_sha256: str
    inherited_plan_sha256: tuple[str, ...]
    canonical_bank_overlap: bool


def _exercise(
    exercise_id: str,
    *,
    curriculum_id: str,
    concept: str,
    subconcept: str,
    question: str,
    expected_answer: str,
    reasoning: Sequence[str],
    forbidden: Sequence[str] = (),
    source_ref: str = MB4E_SOURCE_REF,
) -> Exercise:
    return Exercise(
        exercise_id=exercise_id,
        curriculum_id=curriculum_id,
        level=1,
        concept=concept,
        subconcept=subconcept,
        question=question,
        expected_answer=expected_answer,
        source_refs=(source_ref,),
        question_type="supplemental_reasoning",
        required_reasoning_points=tuple(reasoning),
        forbidden_inferences=tuple(forbidden),
        grading_rubric_id="MB4E-L1-RUBRIC-V1",
        integrity_question=False,
        boss_question=False,
        requires_live_data=False,
    )


def mb4e_level1_supplemental_bank(curriculum_id: str) -> tuple[Exercise, ...]:
    """Return a practice-only bank for the exhausted MB4E Level-1 weaknesses.

    The returned exercises are not stored in the validated canonical curriculum package.
    The supplemental loader below also rejects any id that overlaps the canonical bank.
    """

    groups: tuple[tuple[str, str, tuple[tuple[str, str, tuple[str, ...], tuple[str, ...]], ...]], ...] = (
        (
            "architecture",
            "network_layer",
            (
                ("What does the Network layer provide, and how is that different from the P2P layer above it?", "The Network layer provides base communication connectivity, normally the internet; P2P is a separate layer above it for peer information propagation.", ("Network is the base communication layer.", "P2P is separate and above it."), ("The Network layer itself is the gossip or flooding layer.",)),
                ("A blockchain uses gossip between peers. Which layer supplies connectivity and which layer performs the gossip-style propagation?", "The Network layer supplies connectivity, while the P2P layer performs peer propagation such as gossip.", ("Separate connectivity from peer propagation.",), ()),
                ("Why is it inaccurate to define the Network layer itself as the gossip and flooding layer?", "Because the Network layer provides base communications; gossip and flooding are P2P information-propagation protocols above it.", ("Gossip/flooding belong to P2P.",), ()),
                ("If peer-propagation software stopped while internet connectivity remained, which lower layer would still perform its basic role?", "The Network layer would still provide base communications even though the P2P layer was not functioning.", ("Base communications can remain without P2P propagation."), ()),
                ("State the bottom two layers in order and give the role of the lower layer.", "The Network layer is lowest and provides base communications; the P2P layer runs above it.", ("Network is below P2P.", "Network provides base communications."), ()),
            ),
        ),
        (
            "architecture",
            "p2p_layer",
            (
                ("What is the main role of the P2P layer in the discussed blockchain stack?", "It handles peer-to-peer information propagation above the base Network layer, using mechanisms such as gossip or flooding.", ("P2P handles peer propagation.", "It runs above Network."), ()),
                ("Where does the P2P layer sit relative to Network, and what kind of protocols characterize it?", "It sits above the Network layer and contains peer information-propagation protocols such as gossip or flooding.", ("P2P is above Network.",), ()),
                ("A node receives transaction information from peers through gossip. Which layer is directly responsible for that propagation behavior?", "The P2P layer is responsible for that peer information propagation.", ("Identify P2P rather than Network."), ()),
                ("How should Roberta distinguish internet connectivity from peer-to-peer dissemination in this layered model?", "Internet connectivity belongs to the Network layer; peer-to-peer dissemination belongs to the P2P layer above it.", ("Keep the two layer roles separate."), ()),
                ("Why do gossip and flooding identify the P2P layer rather than the Network layer?", "They are peer information-propagation protocols, which is the role of the P2P layer above the base communication layer.", ("Gossip/flooding are propagation protocols."), ()),
            ),
        ),
        (
            "benefits",
            "immutability",
            (
                ("Does blockchain immutability mean recorded data is literally impossible to change under every circumstance?", "No. The intended meaning is practical immutability: changing recorded data is extremely difficult or nearly impossible, not absolutely impossible.", ("Reject absolute immutability.", "State the practical difficult-to-change meaning."), ("Blockchain data can never be changed under any circumstance.",)),
                ("Why can immutability still be a benefit even though it is not absolute?", "Because changing recorded history is so difficult that the ledger is effectively stable for uses such as audit and compliance.", ("Practical resistance to change creates the benefit."), ("Immutability is absolute and exceptionless.",)),
                ("Evaluate the claim that a blockchain ledger is genuinely immutable because old data is impossible to change.", "The claim is too absolute; the intended framing is that changing data is extremely difficult or nearly impossible, producing practical rather than genuine absolute immutability.", ("Correct the absolute claim."), ("Old blockchain data is mathematically impossible to alter.",)),
                ("How does practical immutability help audit or compliance?", "It makes previously recorded transactions extremely difficult to alter, helping preserve a stable historical record.", ("Connect difficult-to-change history with audit/compliance."), ()),
                ("What wording best distinguishes useful blockchain immutability from genuine absolute immutability?", "Useful immutability means data is extremely difficult or nearly impossible to change; it does not mean change is genuinely impossible.", ("Practical, not absolute, immutability."), ("No conceivable change can ever occur.",)),
            ),
        ),
        (
            "types",
            "monolithic_polylithic",
            (
                ("What makes a blockchain architecture monolithic in this Layer-1 classification?", "A monolithic architecture uses one base chain for the system's main functionality, including areas such as programmability, consensus, and security.", ("Single base chain is the defining structure."), ()),
                ("What makes an architecture polylithic rather than monolithic?", "A polylithic architecture is a multi-chain design in which multiple chains connect into a broader network of networks.", ("Multiple connected chains define polylithic."), ()),
                ("Why are Bitcoin, Ethereum, and Solana examples of monolithic chains in this classification?", "They are base-layer single-chain protocols whose major functionality belongs to the same base blockchain.", ("Single-chain base layer is decisive."), ()),
                ("A design contains several connected chains in one broader system. Which architecture label fits and why?", "Polylithic fits because the architecture is composed of multiple connected chains rather than one chain carrying the system's functionality.", ("Identify the multi-chain structure."), ()),
                ("What is the core structural contrast between monolithic and polylithic Layer-1 architectures?", "Monolithic is a single-base-chain architecture; polylithic is a multi-chain architecture composed of connected chains.", ("Single chain versus multiple connected chains."), ()),
            ),
        ),
        (
            "types",
            "tokenized",
            (
                ("What does 'tokenized blockchain' mean in this blockchain-type classification?", "It means a standard blockchain that generates cryptocurrency through consensus, such as mining, or through an initial distribution.", ("Native cryptocurrency generation/distribution is central."), ("It primarily means converting real-world assets into security tokens.",)),
                ("Why do Bitcoin and Ethereum qualify as tokenized blockchains under this definition?", "They have cryptocurrency generated or distributed as part of the blockchain system, fitting the tokenized-blockchain category.", ("Relate the category to cryptocurrency, not asset tokenization."), ()),
                ("How should Roberta distinguish a tokenized blockchain from tokenizing a real-world asset?", "A tokenized blockchain here is a blockchain that generates or initially distributes cryptocurrency; that is different from representing a real-world asset as a token.", ("Distinguish blockchain type from asset tokenization."), ("The category is defined by real-world asset tokenization.",)),
                ("What role do mining, consensus, or initial distribution play in identifying a tokenized blockchain?", "They are mechanisms through which the blockchain's cryptocurrency is generated or distributed, which defines the category here.", ("Tie the category to cryptocurrency generation/distribution."), ()),
                ("What is the central difference between tokenized and tokenless blockchains in this classification?", "Tokenized blockchains have a cryptocurrency generated or initially distributed as part of the system, whereas tokenless blockchains do not have that basic transferable unit as a defining feature.", ("Presence versus absence of the blockchain cryptocurrency unit."), ()),
            ),
        ),
    )

    exercises: list[Exercise] = []
    counter = 1
    for concept, subconcept, questions in groups:
        for question, expected, reasoning, forbidden in questions:
            exercises.append(
                _exercise(
                    f"{SUPPLEMENTAL_ID_PREFIX}{counter:03d}",
                    curriculum_id=curriculum_id,
                    concept=concept,
                    subconcept=subconcept,
                    question=question,
                    expected_answer=expected,
                    reasoning=reasoning,
                    forbidden=forbidden,
                )
            )
            counter += 1
    return tuple(exercises)


def _read_json_object(path: str | Path, *, label: str) -> Mapping[str, object]:
    source = Path(path)
    try:
        raw = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TargetedPyramidPracticeError(f"cannot read {label}: {exc}") from exc
    if not isinstance(raw, Mapping):
        raise TargetedPyramidPracticeError(f"{label} must be a JSON object")
    return raw


def _reconstruction_ids(path: str | Path) -> tuple[str, ...]:
    source = Path(path)
    try:
        rows = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
    except (OSError, json.JSONDecodeError) as exc:
        raise TargetedPyramidPracticeError(f"cannot read source-grounded reconstructions: {exc}") from exc
    ids: list[str] = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise TargetedPyramidPracticeError("source-grounded reconstruction rows must be objects")
        exercise_id = row.get("exercise_id")
        if not isinstance(exercise_id, str) or not exercise_id:
            raise TargetedPyramidPracticeError("source-grounded reconstruction exercise_id is invalid")
        ids.append(exercise_id)
    if not ids or len(ids) != len(set(ids)):
        raise TargetedPyramidPracticeError("source-grounded reconstruction ids must be non-empty and unique")
    return tuple(ids)


def _canonical_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _selected_bank_hash(exercises: Sequence[Exercise]) -> str:
    return _canonical_hash([
        {
            "exercise_id": item.exercise_id,
            "level": item.level,
            "concept": item.concept,
            "subconcept": item.subconcept,
            "question": item.question,
            "expected_answer": item.expected_answer,
            "source_refs": list(item.source_refs),
            "required_reasoning_points": list(item.required_reasoning_points),
            "forbidden_inferences": list(item.forbidden_inferences),
            "grading_rubric_id": item.grading_rubric_id,
        }
        for item in exercises
    ])


def prepare_supplemental_targeted_practice(
    *,
    curriculum_dir: str | Path,
    checkpoint_dir: str | Path,
    reconstructions_path: str | Path,
    inherited_remediation_plan_paths: Sequence[str | Path] = (),
    exclude_checkpoint_dirs: Sequence[str | Path] = (),
    questions_per_weakness: int = 5,
    seed: str = "supplemental-r3",
    supplemental_bank: Sequence[Exercise] | None = None,
) -> SupplementalPreparation:
    if questions_per_weakness <= 0:
        raise TargetedPyramidPracticeError("questions_per_weakness must be positive")

    manifest, canonical_bank = validate_package(curriculum_dir)
    curriculum_id = str(manifest["curriculum_id"])
    weak_items = load_weak_items(checkpoint_dir)
    if not weak_items:
        raise TargetedPyramidPracticeError("current checkpoint set contains no unresolved Pyramid weakness")

    current_plan = {"curriculum_id": curriculum_id, **build_remediation_plan(canonical_bank, weak_items)}
    inherited_plans = tuple(
        _read_json_object(path, label=f"inherited remediation plan {index}")
        for index, path in enumerate(inherited_remediation_plan_paths, start=1)
    )
    try:
        effective_plan = inherit_critical_origins(current_plan, inherited_plans, curriculum_id=curriculum_id)
    except ValueError as exc:
        raise TargetedPyramidPracticeError(str(exc)) from exc

    weaknesses = effective_plan.get("weaknesses")
    if not isinstance(weaknesses, list) or not weaknesses:
        raise TargetedPyramidPracticeError("effective remediation plan has no weaknesses")

    active_counts: dict[WeaknessKey, int] = {}
    current_weak_ids: list[str] = []
    for raw in weaknesses:
        if not isinstance(raw, Mapping):
            raise TargetedPyramidPracticeError("effective remediation weakness must be an object")
        concept = raw.get("concept")
        subconcept = raw.get("subconcept")
        critical_count = raw.get("critical_count")
        ids = raw.get("exercise_ids")
        if (
            not isinstance(concept, str)
            or not concept
            or (subconcept is not None and (not isinstance(subconcept, str) or not subconcept))
            or isinstance(critical_count, bool)
            or not isinstance(critical_count, int)
            or critical_count < 0
            or not isinstance(ids, list)
            or not all(isinstance(item, str) and item for item in ids)
        ):
            raise TargetedPyramidPracticeError("effective remediation weakness is malformed")
        key = (concept, subconcept)
        if key in active_counts:
            raise TargetedPyramidPracticeError(f"duplicate effective remediation weakness {key}")
        active_counts[key] = critical_count
        current_weak_ids.extend(ids)

    bank = tuple(supplemental_bank) if supplemental_bank is not None else mb4e_level1_supplemental_bank(curriculum_id)
    if not bank:
        raise TargetedPyramidPracticeError("supplemental practice bank is empty")

    canonical_ids = {item.exercise_id for item in canonical_bank}
    supplemental_ids = [item.exercise_id for item in bank]
    if len(supplemental_ids) != len(set(supplemental_ids)):
        raise TargetedPyramidPracticeError("supplemental practice bank contains duplicate exercise ids")
    overlap = canonical_ids & set(supplemental_ids)
    if overlap:
        raise TargetedPyramidPracticeError(f"supplemental practice ids overlap canonical curriculum: {sorted(overlap)}")

    approved_refs = manifest.get("approved_source_refs")
    if not isinstance(approved_refs, list):
        raise TargetedPyramidPracticeError("validated curriculum manifest is missing approved_source_refs")
    approved = {str(item) for item in approved_refs}
    for item in bank:
        if item.curriculum_id != curriculum_id or item.level != 1:
            raise TargetedPyramidPracticeError("supplemental exercises must bind to the current Level-1 curriculum")
        if item.integrity_question or item.boss_question or item.requires_live_data:
            raise TargetedPyramidPracticeError("supplemental practice cannot contain integrity, Boss, or live-data questions")
        if not set(item.source_refs).issubset(approved):
            raise TargetedPyramidPracticeError(f"supplemental exercise {item.exercise_id} references an unapproved source")

    seen_supplemental: set[str] = set()
    if exclude_checkpoint_dirs:
        try:
            seen_supplemental.update(load_seen_exercise_ids(exclude_checkpoint_dirs))
        except ValueError as exc:
            raise TargetedPyramidPracticeError(str(exc)) from exc

    rng = random.Random(seed)
    selected: list[Exercise] = []
    for key in sorted(active_counts, key=lambda item: (item[0], item[1] or "")):
        pool = [item for item in bank if (item.concept, item.subconcept) == key and item.exercise_id not in seen_supplemental]
        rng.shuffle(pool)
        if len(pool) < questions_per_weakness:
            raise TargetedPyramidPracticeError(
                "supplemental practice bank does not contain enough fresh questions for "
                f"{key[0]}/{key[1] or '-'}: need {questions_per_weakness}, found {len(pool)}"
            )
        selected.extend(pool[:questions_per_weakness])

    if {(item.concept, item.subconcept) for item in selected} != set(active_counts):
        raise TargetedPyramidPracticeError("supplemental practice does not cover every active weakness")

    reconstruction_ids = _reconstruction_ids(reconstructions_path)
    recon_sha = hashlib.sha256(Path(reconstructions_path).read_bytes()).hexdigest()
    inherited_hashes = tuple(hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in inherited_remediation_plan_paths)

    prepared = PreparedTargetedPractice(
        curriculum_id=curriculum_id,
        level=1,
        exercises=tuple(selected),
        weakness_critical_counts=tuple(
            (concept, subconcept, active_counts[(concept, subconcept)])
            for concept, subconcept in sorted(active_counts, key=lambda item: (item[0], item[1] or ""))
        ),
        original_weak_ids=reconstruction_ids,
        source_grounded_weak_items=len(reconstruction_ids),
    )

    return SupplementalPreparation(
        prepared=prepared,
        current_weak_ids=tuple(sorted(set(current_weak_ids))),
        current_weakness_keys=tuple(sorted(active_counts, key=lambda item: (item[0], item[1] or ""))),
        selected_supplemental_ids=tuple(item.exercise_id for item in selected),
        selected_bank_sha256=_selected_bank_hash(selected),
        reconstruction_sha256=recon_sha,
        inherited_plan_sha256=inherited_hashes,
        canonical_bank_overlap=False,
    )


def supplemental_manifest(preparation: SupplementalPreparation, *, checkpoint_binding: str) -> dict[str, object]:
    return {
        "contract": SUPPLEMENTAL_PRACTICE_CONTRACT,
        "version": SUPPLEMENTAL_PRACTICE_VERSION,
        "curriculum_id": preparation.prepared.curriculum_id,
        "level": preparation.prepared.level,
        "current_weak_ids": list(preparation.current_weak_ids),
        "active_weaknesses": [
            {
                "concept": concept,
                "subconcept": subconcept,
                "critical_origin": (concept, subconcept) in preparation.prepared.critical_weakness_keys,
            }
            for concept, subconcept in preparation.current_weakness_keys
        ],
        "supplemental_exercise_ids": list(preparation.selected_supplemental_ids),
        "supplemental_bank_sha256": preparation.selected_bank_sha256,
        "source_grounded_reconstructions_sha256": preparation.reconstruction_sha256,
        "inherited_remediation_plan_sha256": list(preparation.inherited_plan_sha256),
        "grounded_checkpoint_binding": checkpoint_binding,
        "canonical_bank_overlap": preparation.canonical_bank_overlap,
        "canonical_exam": False,
        "ledger_mutation_authorized": False,
        "phase8_candidate_creation_authorized": False,
        "source_truth_authorized": False,
        "live_state_authorized": False,
        "memory_promotion_authorized": False,
        "retention_authorized": False,
        "governance_mutation_authorized": False,
        "execution_authorized": False,
    }
