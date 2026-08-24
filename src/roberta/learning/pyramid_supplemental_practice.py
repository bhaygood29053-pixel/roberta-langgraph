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
) -> Exercise:
    return Exercise(
        exercise_id=exercise_id,
        curriculum_id=curriculum_id,
        level=1,
        concept=concept,
        subconcept=subconcept,
        question=question,
        expected_answer=expected_answer,
        source_refs=(MB4E_SOURCE_REF,),
        question_type="supplemental_reasoning",
        required_reasoning_points=tuple(reasoning),
        forbidden_inferences=tuple(forbidden),
        grading_rubric_id="MB4E-L1-RUBRIC-V1",
        integrity_question=False,
        boss_question=False,
        requires_live_data=False,
    )


def mb4e_level1_supplemental_bank(curriculum_id: str) -> tuple[Exercise, ...]:
    """Return a noncanonical practice-only bank for the five exhausted Round-2 weaknesses.

    These exercises are intentionally absent from the validated Pyramid curriculum package.
    They may be used only through the supplemental-practice loader below, which fails closed
    if any supplemental id overlaps the canonical bank.
    """

    specs = (
        # architecture/network_layer
        ("001", "architecture", "network_layer", "In the layered blockchain architecture, what does the Network layer provide, and how is that different from the P2P layer above it?", "The Network layer provides the underlying communication connectivity, normally the internet. The P2P layer sits above it and handles peer information propagation protocols.", ("Network layer is the base communication layer.", "P2P is a separate layer above it."), ("The Network layer itself is the gossip or flooding protocol layer.",)),
        ("002", "architecture", "network_layer", "A blockchain uses gossip to spread information between peers. Which layer supplies the underlying connectivity, and which layer performs the gossip-style propagation?", "The Network layer supplies the base connectivity, while the P2P layer performs gossip-style peer propagation.", ("Separate base connectivity from peer propagation.",)),
        ("003", "architecture", "network_layer", "Why is it inaccurate to define the blockchain Network layer as the layer that runs gossip and flooding protocols?", "Because the Network layer is the base communication layer; gossip and flooding are information-propagation protocols of the P2P layer that runs above it.", ("Network and P2P are distinct layers.", "Gossip/flooding belong to P2P."),),
        ("004", "architecture", "network_layer", "If peer-to-peer propagation software stopped but ordinary internet connectivity still existed, which of the two lower blockchain layers would still be providing its basic function?", "The Network layer would still provide base communications, even though the P2P propagation layer was not functioning.", ("Base communication can be distinguished from P2P propagation."),),
        ("005", "architecture", "network_layer", "State the bottom two layers of the discussed blockchain architecture in order and give the role of the lower one.", "The Network layer is lowest and provides base communications; the P2P layer runs above it.", ("Network is lower than P2P.", "Network provides the base communication layer."),),

        # architecture/p2p_layer
        ("006", "architecture", "p2p_layer", "What is the main architectural role of the P2P layer in the discussed blockchain stack?", "It provides peer-to-peer information propagation above the base Network layer, using protocols such as gossip or flooding.", ("P2P handles peer information propagation.", "It runs above the Network layer."),),
        ("007", "architecture", "p2p_layer", "Where does the P2P layer sit relative to the Network layer, and what type of protocols characterize it?", "It sits on top of the Network layer and contains peer information-propagation protocols such as gossip or flooding.", ("P2P is above Network.", "Propagation protocols characterize P2P."),),
        ("008", "architecture", "p2p_layer", "A node receives transaction information from peers through a gossip mechanism. Which architectural layer is directly responsible for that propagation behavior?", "The P2P layer is directly responsible for peer information propagation through gossip-style protocols.", ("Identify P2P, not the base Network layer."),),
        ("009", "architecture", "p2p_layer", "What distinction should Roberta make between internet connectivity and peer-to-peer dissemination in the layered blockchain model?", "Internet connectivity belongs to the base Network layer, while peer-to-peer dissemination belongs to the P2P layer above it.", ("Keep connectivity and dissemination in separate layers."),),
        ("010", "architecture", "p2p_layer", "Why are gossip and flooding examples useful for identifying the P2P layer rather than the Network layer?", "They are information-propagation protocols used among peers, which is the function assigned to the P2P layer above the base communication layer.", ("Gossip/flooding are peer propagation mechanisms."),),

        # benefits/immutability
        ("011", "benefits", "immutability", "Does blockchain immutability mean that recorded data is literally impossible to change under every circumstance? Explain the intended meaning.", "No. The intended meaning is practical immutability: changing recorded data is extremely difficult or nearly impossible, not absolutely impossible in a mathematical sense.", ("Reject absolute immutability.", "State the practical extremely-difficult meaning."), ("Blockchain data can never be changed under any circumstance.",)),
        ("012", "benefits", "immutability", "Why can immutability still be treated as a blockchain benefit even though it is not absolute?", "Because changing recorded history is so difficult that the ledger is effectively stable for uses such as audit and compliance, even though it is not genuinely unchangeable.", ("Practical resistance to change is the benefit.", "Do not claim literal impossibility."), ("Immutability is absolute and exceptionless.",)),
        ("013", "benefits", "immutability", "Evaluate this statement: 'A blockchain ledger is genuinely immutable because changing old data is impossible.'", "The statement is too absolute. The book's framing is that changing data is extremely difficult and nearly impossible, which produces practical immutability rather than genuine absolute immutability.", ("Correct the absolute claim.", "Preserve the near-impossibility qualification."), ("Old blockchain data is mathematically impossible to alter.",)),
        ("014", "benefits", "immutability", "How does practical immutability support audit or compliance use cases?", "It makes previously recorded transactions extremely difficult to alter, helping preserve a stable historical record for audit and compliance.", ("Connect difficult-to-change history to audit/compliance."), ("Audit usefulness requires absolute impossibility of change.",)),
        ("015", "benefits", "immutability", "What wording best captures the book's distinction between 'immutable' as a useful property and 'genuinely immutable'?", "Useful blockchain immutability means data is extremely difficult or nearly impossible to change; it does not mean change is genuinely impossible.", ("Practical, not absolute, immutability."), ("Immutability means no conceivable change can ever occur.",)),

        # types/monolithic_polylithic
        ("016", "types", "monolithic_polylithic", "What makes a blockchain architecture monolithic in the book's Layer-1 classification?", "A monolithic architecture uses one base chain for the system's functionality, with components such as programmability, consensus, and security on that same blockchain rather than off-chain.", ("Single base chain.", "Core functionality remains on the same chain."),),
        ("017", "types", "monolithic_polylithic", "What makes a blockchain architecture polylithic rather than monolithic?", "A polylithic architecture is a multi-chain design in which multiple chains connect with a core chain or with one another, forming a network of networks.", ("Multiple connected chains.", "Network-of-networks structure."),),
        ("018", "types", "monolithic_polylithic", "Why are Bitcoin, Ethereum, and Solana examples of monolithic chains in this classification?", "They are base-layer single-chain protocols whose major functionality belongs to the same base blockchain.", ("Single-chain base layer is the defining feature."),),
        ("019", "types", "monolithic_polylithic", "A design has several chains connected into one broader system. Which architecture label fits that description, and why?", "Polylithic fits because the architecture is composed of multiple connected chains rather than one chain carrying all system functionality.", ("Identify polylithic from multi-chain composition."),),
        ("020", "types", "monolithic_polylithic", "What is the key structural contrast between monolithic and polylithic Layer-1 architectures?", "Monolithic is a single base-chain architecture; polylithic is a multi-chain architecture composed of connected chains.", ("Single chain versus multiple connected chains."),),

        # types/tokenized
        ("021", "types", "tokenized", "What does 'tokenized blockchain' mean in the book's blockchain-type classification?", "It means a standard blockchain that generates cryptocurrency through its consensus process, such as mining, or through an initial distribution.", ("Native cryptocurrency generation is the defining idea."), ("It primarily means converting real-world assets into security tokens.",)),
        ("022", "types", "tokenized", "Why do Bitcoin and Ethereum qualify as tokenized blockchains under this definition?", "They are blockchains with cryptocurrency generated or distributed as part of the blockchain system, fitting the book's tokenized-blockchain category.", ("Relate the category to native cryptocurrency, not asset tokenization."),),
        ("023", "types", "tokenized", "How should Roberta distinguish a tokenized blockchain from the separate idea of tokenizing a real-world asset?", "A tokenized blockchain in this classification is a blockchain that generates or initially distributes cryptocurrency. That is different from representing a real-world asset as a token.", ("Distinguish blockchain type from asset tokenization."), ("The category is defined by real-world asset tokenization.",)),
        ("024", "types", "tokenized", "What role do mining, consensus, or initial distribution play in identifying a tokenized blockchain?", "They are mechanisms through which the blockchain's cryptocurrency is generated or distributed, which is what defines the tokenized category here.", ("Tie category to cryptocurrency generation/distribution."),),
        ("025", "types", "tokenized", "What is the central difference between tokenized and tokenless blockchains in the book's classification?", "Tokenized blockchains have a cryptocurrency generated or initially distributed as part of the system, whereas tokenless blockchains do not have that basic transferable unit as a defining feature.", ("Presence versus absence of the blockchain's cryptocurrency unit."),),
    )

    return tuple(
        _exercise(
            f"{SUPPLEMENTAL_ID_PREFIX}{suffix}",
            curriculum_id=curriculum_id,
            concept=concept,
            subconcept=subconcept,
            question=question,
            expected_answer=expected,
            reasoning=reasoning,
            forbidden=forbidden,
        )
        for suffix, concept, subconcept, question, expected, reasoning, forbidden in specs
    )


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
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
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

    current_plan = {
        "curriculum_id": curriculum_id,
        **build_remediation_plan(canonical_bank, weak_items),
    }
    inherited_plans = tuple(
        _read_json_object(path, label=f"inherited remediation plan {index}")
        for index, path in enumerate(inherited_remediation_plan_paths, start=1)
    )
    try:
        effective_plan = inherit_critical_origins(
            current_plan,
            inherited_plans,
            curriculum_id=curriculum_id,
        )
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
        raise TargetedPyramidPracticeError(
            f"supplemental practice ids overlap canonical curriculum: {sorted(overlap)}"
        )

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
            raise TargetedPyramidPracticeError(
                f"supplemental exercise {item.exercise_id} references an unapproved source"
            )

    seen_supplemental: set[str] = set()
    if exclude_checkpoint_dirs:
        try:
            seen_supplemental.update(load_seen_exercise_ids(exclude_checkpoint_dirs))
        except ValueError as exc:
            raise TargetedPyramidPracticeError(str(exc)) from exc

    rng = random.Random(seed)
    selected: list[Exercise] = []
    for key in sorted(active_counts, key=lambda item: (item[0], item[1] or "")):
        pool = [
            item for item in bank
            if (item.concept, item.subconcept) == key
            and item.exercise_id not in seen_supplemental
        ]
        rng.shuffle(pool)
        if len(pool) < questions_per_weakness:
            raise TargetedPyramidPracticeError(
                "supplemental practice bank does not contain enough fresh questions for "
                f"{key[0]}/{key[1] or '-'}: need {questions_per_weakness}, found {len(pool)}"
            )
        selected.extend(pool[:questions_per_weakness])

    selected_keys = {(item.concept, item.subconcept) for item in selected}
    if selected_keys != set(active_counts):
        raise TargetedPyramidPracticeError("supplemental practice does not cover every active weakness")

    reconstruction_ids = _reconstruction_ids(reconstructions_path)
    recon_sha = hashlib.sha256(Path(reconstructions_path).read_bytes()).hexdigest()
    inherited_hashes = tuple(
        hashlib.sha256(Path(path).read_bytes()).hexdigest()
        for path in inherited_remediation_plan_paths
    )

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
            {"concept": concept, "subconcept": subconcept, "critical_origin": (concept, subconcept) in preparation.prepared.critical_weakness_keys}
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
