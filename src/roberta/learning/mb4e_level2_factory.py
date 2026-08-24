from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .pyramid import Exercise


CURRICULUM_ID = "mastering_blockchain_4e_2023_book01"
LEVEL = 2
RUBRIC_ID = "MB4E-L2-RUBRIC-V1"
ORDINARY_VARIANTS_PER_TARGET = 21
ORDINARY_COUNT = 1155
INTEGRITY_COUNT = 50
TOTAL_COUNT = 1206


@dataclass(frozen=True, slots=True)
class Level2Target:
    concept: str
    subconcept: str
    principle: str
    source_ref: str
    chapter: str
    section: str
    pdf_pages: tuple[int, ...]
    required_points: tuple[str, ...]
    forbidden_inferences: tuple[str, ...] = ()


QUESTION_TEMPLATES: tuple[str, ...] = (
    "Explain the source-supported rule for {label}.",
    "What does the book establish about {label}?",
    "Give a precise explanation of {label} without adding assumptions.",
    "A learner asks what matters most about {label}. What should you tell them?",
    "State the key mechanism or distinction involved in {label}.",
    "How should {label} be described in the blockchain-mechanics context?",
    "What source-supported point must an answer about {label} include?",
    "A teammate gives a vague explanation of {label}. Replace it with the precise rule.",
    "What would a correct technical summary of {label} say?",
    "Describe {label} in a way that preserves the book's stated limits and conditions.",
    "Why is {label} important to blockchain mechanics?",
    "How does {label} affect agreement, replication, decentralization, or finality as applicable?",
    "If auditing an answer about {label}, what core point should be present?",
    "What common oversimplification should be avoided when explaining {label}?",
    "Apply the book's explanation of {label} to a generic blockchain system.",
    "What is the correct relationship between {label} and the surrounding protocol mechanics?",
    "Summarize the operational meaning of {label}.",
    "What condition or tradeoff is essential when reasoning about {label}?",
    "A design review raises {label}. What source-grounded answer resolves the issue?",
    "How would you correct a technically incomplete statement about {label}?",
    "What conclusion about {label} follows from the chapter's explanation?",
)


def _pages(start: int, end: int) -> tuple[int, ...]:
    return tuple(range(start, end + 1))


CH1_DISTRIBUTED = "MB4E-CH1-P37-41-DISTRIBUTED"
CH1_ARCH = "MB4E-CH1-P44-47-DEFINITION-ARCH"
CH1_ELEMENTS = "MB4E-CH1-P48-52-ELEMENTS-FUNCTION"
CH2_BASICS = "MB4E-CH2-P62-65-DECENTRALIZATION-BASICS"
CH2_METHODS = "MB4E-CH2-P66-70-METHODS-MEASURE-EVALUATE"
CH5_FOUNDATIONS = "MB4E-CH5-P152-156-CONSENSUS-FOUNDATIONS"
CH5_CFT = "MB4E-CH5-P157-161-CFT-PAXOS-RAFT"
CH5_PBFT = "MB4E-CH5-P162-167-PBFT"
CH5_IBFT = "MB4E-CH5-P168-170-IBFT"
CH5_TENDERMINT = "MB4E-CH5-P171-176-TENDERMINT"
CH5_NAKAMOTO = "MB4E-CH5-P177-180-NAKAMOTO-POW"
CH5_POS = "MB4E-CH5-P181-183-POS"
CH5_HOTSTUFF = "MB4E-CH5-P184-187-HOTSTUFF"
CH5_FINALITY = "MB4E-CH5-P188-189-FINALITY-PERFORMANCE"


def level2_source_map() -> dict[str, dict[str, object]]:
    return {
        CH1_DISTRIBUTED: {"chapter": "Chapter 1", "section": "Distributed systems", "pdf_pages": _pages(37, 41)},
        CH1_ARCH: {"chapter": "Chapter 1", "section": "Blockchain definition and layered architecture", "pdf_pages": _pages(44, 47)},
        CH1_ELEMENTS: {"chapter": "Chapter 1", "section": "Generic blockchain elements and functionality", "pdf_pages": _pages(48, 52)},
        CH2_BASICS: {"chapter": "Chapter 2", "section": "Introducing decentralization", "pdf_pages": _pages(62, 65)},
        CH2_METHODS: {"chapter": "Chapter 2", "section": "Methods, measurement, and evaluation of decentralization", "pdf_pages": _pages(66, 70)},
        CH5_FOUNDATIONS: {"chapter": "Chapter 5", "section": "Consensus foundations, fault tolerance, models, and timing", "pdf_pages": _pages(152, 156)},
        CH5_CFT: {"chapter": "Chapter 5", "section": "Consensus properties, Paxos, and Raft", "pdf_pages": _pages(157, 161)},
        CH5_PBFT: {"chapter": "Chapter 5", "section": "Practical Byzantine Fault Tolerance", "pdf_pages": _pages(162, 167)},
        CH5_IBFT: {"chapter": "Chapter 5", "section": "Istanbul Byzantine Fault Tolerance", "pdf_pages": _pages(168, 170)},
        CH5_TENDERMINT: {"chapter": "Chapter 5", "section": "Tendermint", "pdf_pages": _pages(171, 176)},
        CH5_NAKAMOTO: {"chapter": "Chapter 5", "section": "Nakamoto consensus and proof of work", "pdf_pages": _pages(177, 180)},
        CH5_POS: {"chapter": "Chapter 5", "section": "Proof of stake", "pdf_pages": _pages(181, 183)},
        CH5_HOTSTUFF: {"chapter": "Chapter 5", "section": "HotStuff", "pdf_pages": _pages(184, 187)},
        CH5_FINALITY: {"chapter": "Chapter 5", "section": "Choosing consensus, finality, performance, and scalability", "pdf_pages": _pages(188, 189)},
    }


def _target(
    concept: str,
    subconcept: str,
    principle: str,
    source_ref: str,
    *required_points: str,
    forbidden: Sequence[str] = (),
) -> Level2Target:
    source = level2_source_map()[source_ref]
    return Level2Target(
        concept=concept,
        subconcept=subconcept,
        principle=principle,
        source_ref=source_ref,
        chapter=str(source["chapter"]),
        section=str(source["section"]),
        pdf_pages=tuple(int(page) for page in source["pdf_pages"]),
        required_points=tuple(required_points) or (principle,),
        forbidden_inferences=tuple(forbidden),
    )


def level2_targets() -> tuple[Level2Target, ...]:
    targets = (
        _target("distributed_systems", "message_passing", "For blockchain mechanics, nodes coordinate as a message-passing distributed system: participants exchange messages over communication channels rather than relying on shared memory.", CH1_DISTRIBUTED, "Blockchain nodes coordinate through message exchange across a network."),
        _target("architecture", "p2p_nodes", "The peer-to-peer layer connects participants directly without a central network controller and propagates information between peers.", CH1_ARCH, "Peers communicate directly rather than through one central controller."),
        _target("architecture", "consensus_updates", "Blockchain state is updated under protocol rules through consensus among participating nodes rather than by a single central updater.", CH1_ARCH, "Protocol-valid updates require network agreement rather than unilateral central control.", forbidden=("Do not claim that any single participant can unilaterally finalize shared ledger state.",)),
        _target("blocks", "generic_structure", "A generic block groups transactions with header metadata and normally links to the preceding block by a hash reference, supporting an ordered chain of blocks.", CH1_ELEMENTS, "Blocks bundle transactions and carry metadata.", "Non-genesis blocks reference the preceding block by hash."),
        _target("decentralization", "definition", "Decentralization distributes control among participants instead of concentrating authority in one central body; in blockchain this supports operation without a single controlling authority.", CH2_BASICS, "Control is distributed rather than concentrated in one authority."),
        _target("decentralization", "distributed_vs_decentralized", "A system can be distributed yet still centrally controlled; decentralization concerns where control and authority reside, not merely whether computation or data are spread across nodes.", CH2_BASICS, "Distribution of nodes does not by itself prove decentralization of control.", forbidden=("Do not treat distributed and decentralized as synonyms.",)),
        _target("decentralization", "decentralized_consensus", "Decentralized consensus lets network participants agree through a protocol without depending on a central trusted intermediary to make the shared decision.", CH2_BASICS, "Agreement is reached through consensus rather than a central trusted third party."),
        _target("decentralization", "replication_and_control", "A blockchain-based decentralized system can replicate application state and data across participating nodes while also distributing control; replication and decentralization are related but distinct properties.", CH2_BASICS, "Replication spreads state across nodes while decentralization spreads control."),
        _target("decentralization", "disintermediation", "Disintermediation decentralizes a process by removing a central intermediary so participants can interact directly through the blockchain protocol.", CH2_METHODS, "The intermediary is removed rather than merely replaced by another central provider."),
        _target("decentralization", "contest_driven", "Contest-driven decentralization introduces competition among possible service providers, reducing monopoly control but generally producing partial rather than complete decentralization.", CH2_METHODS, "Competition can reduce concentration without fully eliminating intermediaries."),
        _target("decentralization", "spectrum", "Decentralization is a spectrum: a design should seek a level appropriate to the use case rather than assume maximum decentralization is always operationally optimal.", CH2_METHODS, "The appropriate degree of decentralization depends on requirements and tradeoffs."),
        _target("decentralization", "nakamoto_coefficient", "The Nakamoto coefficient estimates how many independent entities must be controlled to compromise a network; a higher coefficient indicates stronger decentralization by that measure.", CH2_METHODS, "Higher values correspond to more entities required for compromise.", forbidden=("Do not reverse the metric by claiming a higher Nakamoto coefficient means greater centralization.",)),
        _target("decentralization", "weakest_subsystem", "Effective decentralization must consider multiple subsystems such as nodes, miners or validators, clients, developers, exchanges, and ownership; a highly concentrated subsystem can constrain the system's overall decentralization.", CH2_METHODS, "Overall decentralization can be limited by the most concentrated relevant subsystem."),
        _target("decentralization", "blockchain_suitability", "Not every problem should be decentralized with a blockchain; requirements such as trust, control of updates, throughput, consensus scope, and desired immutability determine whether a blockchain or conventional database is more suitable.", CH2_METHODS, "Choose blockchain only when the use-case requirements justify its coordination model and tradeoffs.", forbidden=("Do not claim blockchain is automatically the best database for every application.",)),
        _target("consensus", "definition", "Distributed consensus is the process by which network processes agree on a value despite faults; blockchain consensus applies this agreement problem to replicated ledger state.", CH5_FOUNDATIONS, "Consensus seeks agreement among processes in the presence of faults."),
        _target("consensus", "public_vs_permissioned", "Public blockchains commonly use Nakamoto-style or other open-participation consensus, while permissioned networks can use classical fault-tolerant voting protocols or blockchain variants of them.", CH5_FOUNDATIONS, "Consensus design depends in part on the participation and trust model of the network."),
        _target("fault_tolerance", "cft_vs_bft", "Crash fault tolerance addresses benign failures such as stopped processes, whereas Byzantine fault tolerance is designed for arbitrary behavior that may be malicious.", CH5_FOUNDATIONS, "CFT and BFT differ in the fault model they are designed to tolerate.", forbidden=("Do not claim ordinary CFT by itself tolerates arbitrary Byzantine behavior.",)),
        _target("fault_tolerance", "replication", "Replication improves availability and resilience by maintaining copies of state across multiple nodes so the service can continue when some replicas fail within the protocol's tolerance.", CH5_FOUNDATIONS, "Replication supports availability but does not remove the protocol's fault threshold."),
        _target("consensus", "state_machine_replication", "State machine replication keeps replicas consistent by starting from compatible state, processing requests in the same total order, and applying deterministic state transitions.", CH5_FOUNDATIONS, "Ordered deterministic execution lets replicas converge on the same state."),
        _target("consensus", "flp_impossibility", "FLP shows that deterministic consensus cannot be guaranteed in a fully asynchronous system when even one process may fail; it is a conditional impossibility result, not a claim that consensus is impossible in every model.", CH5_FOUNDATIONS, "The impossibility depends on deterministic consensus, full asynchrony, and the possibility of a fault.", forbidden=("Do not generalize FLP into a claim that all consensus is impossible under all network assumptions.",)),
        _target("consensus", "flp_mitigations", "Practical protocols work around FLP's conditions by adding mechanisms such as failure detectors or timeouts, randomization, or synchrony and partial-synchrony assumptions that enable progress.", CH5_FOUNDATIONS, "The workaround changes assumptions or termination guarantees rather than disproving FLP."),
        _target("fault_tolerance", "cft_lower_bound", "For the crash-fault model described in the chapter, tolerating f crash failures requires at least 2f+1 processes so a correct majority can remain.", CH5_FOUNDATIONS, "CFT lower bound: at least 2f+1 nodes for f crash faults."),
        _target("fault_tolerance", "bft_lower_bound", "For Byzantine fault tolerance in the standard model described in the chapter, tolerating f Byzantine nodes requires at least 3f+1 processes.", CH5_FOUNDATIONS, "BFT lower bound: at least 3f+1 nodes for f Byzantine faults.", forbidden=("Do not use the CFT 2f+1 threshold as the standard Byzantine threshold.",)),
        _target("timing", "synchrony", "A synchronous model assumes known upper bounds on message and processing delays, allowing protocol steps to reason about bounded communication rounds.", CH5_FOUNDATIONS, "Synchrony includes known bounds on communication and processing delays."),
        _target("timing", "asynchrony", "A fully asynchronous model assumes no known upper bound on communication or processing delay, so a slow response cannot be reliably distinguished from a failed process using timing alone.", CH5_FOUNDATIONS, "Asynchrony provides no timing upper bound for communication or processing."),
        _target("timing", "partial_synchrony", "Partial synchrony allows bounded communication eventually even though the bound or the stabilization time may be unknown; after global stabilization, the network remains synchronous long enough for progress.", CH5_FOUNDATIONS, "Eventual synchrony after an unknown GST supports liveness reasoning."),
        _target("consensus", "traditional_vs_nakamoto", "The chapter distinguishes traditional voting-based fault-tolerant consensus from lottery-based Nakamoto-style blockchain consensus; they use different mechanisms and assumptions to obtain agreement.", CH5_FOUNDATIONS, "Traditional voting protocols and Nakamoto-style protocols are distinct consensus families."),
        _target("consensus", "safety", "Consensus safety means bad decisions are prevented; the chapter expresses this through properties such as agreement, validity, and integrity.", CH5_CFT, "Agreement prevents different decisions, validity constrains decided values, and integrity prevents repeated decision by a process."),
        _target("consensus", "liveness", "Consensus liveness means the protocol can eventually make progress; its central termination property requires honest participants eventually to decide.", CH5_CFT, "Liveness is about eventual progress or termination, not merely correctness of a decided value."),
        _target("paxos", "fault_model", "The Paxos form described here runs in an asynchronous message-passing model and tolerates crash or benign faults; basic Paxos is not a Byzantine-fault-tolerant protocol.", CH5_CFT, "Basic Paxos handles crash faults under an asynchronous model.", forbidden=("Do not classify basic Paxos in this chapter as Byzantine fault tolerant.",)),
        _target("paxos", "roles_and_majority", "Paxos uses proposers, acceptors, and learners; a proposed value becomes decided when a majority of acceptors accepts it, after which learners can learn the decision.", CH5_CFT, "Majority acceptance is central to deciding the proposed value."),
        _target("paxos", "prepare_accept", "Paxos separates proposal handling into a prepare phase and an accept phase so competing proposals can be ordered and a majority can converge on one decision.", CH5_CFT, "Prepare establishes proposal ordering and accept obtains majority acceptance."),
        _target("raft", "roles_and_election", "Raft servers operate as followers, candidates, or a leader; a leader is elected for a term and coordinates log replication, with a new election if leadership is lost.", CH5_CFT, "Leader election is one of Raft's core subproblems and roles change by protocol state."),
        _target("raft", "log_replication_and_commit", "Raft commits a log entry after the leader replicates it to enough followers to obtain majority confirmation; the leader then propagates the committed state.", CH5_CFT, "An entry is not committed merely because the leader appended it locally; majority replication is required."),
        _target("pbft", "phases", "PBFT normal operation orders and commits requests through pre-prepare, prepare, and commit phases led by a primary with backup replicas participating in the quorum.", CH5_PBFT, "The three normal-operation phases are pre-prepare, prepare, and commit."),
        _target("pbft", "quorums", "PBFT uses the standard Byzantine model n>=3f+1 and relies on 2f+1 matching messages for key prepare and commit certificates or decisions.", CH5_PBFT, "The network-size bound and message quorum are related but not the same quantity."),
        _target("pbft", "view_change", "PBFT view change replaces a suspected faulty primary and is a liveness mechanism that allows the protocol to resume normal operation under a new view.", CH5_PBFT, "View change protects progress when the current primary is faulty or unresponsive."),
        _target("pbft", "checkpointing", "PBFT checkpointing lets replicas agree on a stable state snapshot and discard obsolete protocol messages that precede the stable checkpoint.", CH5_PBFT, "Stable checkpoints bound retained protocol history without changing the committed state itself."),
        _target("pbft", "finality_tradeoff", "PBFT-style consensus can provide immediate deterministic finality and good performance in smaller permissioned settings, but its communication overhead limits node scalability compared with open PoW networks.", CH5_PBFT, "Deterministic finality and communication scalability are distinct design dimensions.", forbidden=("Do not describe PBFT finality as confirmation-based probabilistic finality.",)),
        _target("ibft", "membership_rounds_and_quorums", "IBFT adapts PBFT for blockchain: validator membership can change, consensus runs in rounds on a partially synchronous network with at least 3f+1 processes, and prepare/commit progress uses 2f+1 message thresholds.", CH5_IBFT, "IBFT distinguishes synchronized non-validator nodes from validators that participate in consensus.", "Rounds and quorum thresholds govern proposal commitment."),
        _target("tendermint", "rounds_and_phases", "Tendermint proceeds in rounds with a proposer and proposal, prevote, precommit, and commit behavior; 2f+1 voting thresholds drive locking and decisions.", CH5_TENDERMINT, "Proposal, prevote, and precommit messages coordinate each round before decision."),
        _target("tendermint", "partial_synchrony_timeouts", "Tendermint assumes partial synchrony and uses phase timeouts and round changes so replicas do not wait forever; after the network stabilizes, timely communication permits termination.", CH5_TENDERMINT, "Timeouts support liveness by advancing rounds during delays or failed proposals."),
        _target("tendermint", "consensus_properties", "Tendermint's core consensus properties are agreement, termination, and validity: correct processes do not decide conflicting values, eventually decide, and decide only values satisfying the validity predicate.", CH5_TENDERMINT, "Agreement and validity are safety-oriented while termination supplies liveness."),
        _target("nakamoto", "pow_role", "In the chapter's framing, proof of work is primarily a Sybil-resistance and consensus-facilitation mechanism; chain consensus is obtained by applying the fork-choice rule to select the canonical longest or heaviest chain.", CH5_NAKAMOTO, "PoW raises the resource cost of Sybil influence while fork choice selects the canonical chain.", forbidden=("Do not reduce Nakamoto consensus to the claim that the hash puzzle alone is the complete consensus decision rule.",)),
        _target("nakamoto", "probabilistic_consensus", "Nakamoto consensus provides probabilistic rather than deterministic agreement and finality; confidence grows as honest work extends the selected chain.", CH5_NAKAMOTO, "Its guarantees are probabilistic and depend on the honest-participant resource assumption.", forbidden=("Do not describe Nakamoto finality as immediate deterministic finality.",)),
        _target("nakamoto", "pow_process", "In PoW block production, transactions are gathered into a candidate block and miners vary a nonce while hashing the block data until the result satisfies the network target; a valid proposed block then participates in chain selection.", CH5_NAKAMOTO, "The nonce search is checked against the difficulty target."),
        _target("nakamoto", "backbone_properties", "The chapter maps Nakamoto-style common prefix to agreement, chain quality to validity, and chain growth to liveness, connecting blockchain-specific behavior to traditional consensus properties.", CH5_NAKAMOTO, "Common prefix, chain quality, and chain growth address different consensus guarantees."),
        _target("pos", "stake_based_selection", "Proof of stake assigns block-proposal opportunity using stake-related selection rather than PoW energy expenditure; greater stake generally increases selection probability under the protocol's rule.", CH5_POS, "Stake affects proposer selection, while the exact stake calculation is protocol-specific."),
        _target("pos", "committee_and_delegated", "Committee-based PoS can select a stakeholder committee using randomized mechanisms such as a VRF, while delegated PoS selects a limited proposer set through stake-weighted delegation or voting.", CH5_POS, "Random committee selection and delegated selection are different ways to form the proposer group."),
        _target("hotstuff", "optimizations", "HotStuff reduces PBFT-style communication costs by organizing consensus around a leader, enabling linear view-change behavior after stabilization and supporting responsive progress with frequent leader rotation.", CH5_HOTSTUFF, "Leader-centered communication reduces the all-to-all messaging burden of traditional PBFT-style designs."),
        _target("hotstuff", "quorum_certificates", "HotStuff summarizes sufficient votes in quorum certificates and advances through prepare, pre-commit, commit, and decide phases under the standard n=3f+1 Byzantine model.", CH5_HOTSTUFF, "A quorum certificate represents the protocol's required threshold of validator votes."),
        _target("hotstuff", "safety_liveness_separation", "HotStuff separates safety from liveness: voting and commit rules protect safety, while the Pacemaker coordinates view progress and leader changes to support liveness after stabilization.", CH5_HOTSTUFF, "Safety rules and Pacemaker liveness responsibilities are intentionally separated."),
        _target("finality", "probabilistic_vs_deterministic", "Probabilistic finality gains confidence over time as more blocks extend a chain, whereas deterministic finality treats a committed decision as final immediately under the protocol's fault assumptions.", CH5_FINALITY, "Nakamoto-style systems exemplify probabilistic finality; PBFT-style systems exemplify deterministic finality."),
        _target("consensus", "performance_scalability_tradeoff", "Consensus choice involves tradeoffs: voting-based BFT protocols can offer fast deterministic decisions in smaller permissioned networks, while PoW-style networks support large open participation but with slower probabilistic confirmation.", CH5_FINALITY, "Performance, scalability, participation model, and finality must be evaluated separately."),
        _target("consensus", "algorithm_choice", "There is no universally best consensus algorithm; selection should preserve safety and liveness while matching the use case's participation model, fault assumptions, finality needs, performance, and scalability requirements.", CH5_FINALITY, "Consensus selection is a requirements-and-tradeoffs decision, not a single global ranking.", forbidden=("Do not claim one consensus mechanism is universally optimal for all network models and use cases.",)),
    )
    if len(targets) != 55:
        raise AssertionError(f"Level-2 target count drifted: {len(targets)}")
    return targets


def _label(target: Level2Target) -> str:
    return f"{target.concept.replace('_', ' ')} / {target.subconcept.replace('_', ' ')}"


def build_level2_bank(curriculum_id: str = CURRICULUM_ID) -> tuple[Exercise, ...]:
    targets = level2_targets()
    exercises: list[Exercise] = []
    sequence = 1
    for target in targets:
        label = _label(target)
        for template in QUESTION_TEMPLATES:
            exercises.append(Exercise(exercise_id=f"MB4E-L02-{sequence:05d}", curriculum_id=curriculum_id, level=LEVEL, concept=target.concept, subconcept=target.subconcept, question=template.format(label=label), expected_answer=target.principle, source_refs=(target.source_ref,), question_type="application", difficulty=2, required_reasoning_points=target.required_points, forbidden_inferences=target.forbidden_inferences, grading_rubric_id=RUBRIC_ID))
            sequence += 1
    if len(exercises) != ORDINARY_COUNT:
        raise AssertionError(f"ordinary Level-2 bank count drifted: {len(exercises)}")

    for target in targets[:INTEGRITY_COUNT]:
        label = _label(target)
        exercises.append(Exercise(exercise_id=f"MB4E-L02-{sequence:05d}", curriculum_id=curriculum_id, level=LEVEL, concept=target.concept, subconcept=target.subconcept, question=f"Integrity check: state the precise source-supported rule for {label}; preserve its fault, timing, trust, quorum, or finality conditions where relevant.", expected_answer=target.principle, source_refs=(target.source_ref,), question_type="integrity", difficulty=2, required_reasoning_points=target.required_points, forbidden_inferences=target.forbidden_inferences, grading_rubric_id=RUBRIC_ID, integrity_question=True))
        sequence += 1

    boss_refs = (CH2_BASICS, CH5_FOUNDATIONS, CH5_PBFT, CH5_NAKAMOTO, CH5_FINALITY)
    exercises.append(Exercise(exercise_id=f"MB4E-L02-{sequence:05d}", curriculum_id=curriculum_id, level=LEVEL, concept="blockchain_mechanics", subconcept="boss_synthesis", question="Boss: A team must choose mechanics for a replicated blockchain network. Explain how decentralization, fault model, timing assumptions, consensus safety/liveness, quorum design, and finality interact. Contrast a PBFT-style design with Nakamoto-style consensus and state why the choice is use-case dependent.", expected_answer="A sound design separates decentralization of control from mere distribution of replicas, identifies the faults and timing model the protocol must tolerate, and preserves both safety and liveness. Classical BFT designs use quorum voting under Byzantine thresholds and can provide deterministic finality in smaller permissioned settings. Nakamoto-style consensus combines resource-based Sybil resistance with fork choice and provides probabilistic agreement/finality suitable for open participation. The appropriate mechanism depends on trust and participation, fault assumptions, finality, performance, and scalability requirements rather than a universally best algorithm.", source_refs=boss_refs, question_type="boss", difficulty=2, required_reasoning_points=("Distinguish decentralization of control from distribution/replication.", "Name fault and timing assumptions as consensus design inputs.", "Preserve both safety and liveness as core requirements.", "Describe PBFT-style quorum voting and deterministic finality.", "Describe Nakamoto fork-choice consensus as probabilistic and PoW as Sybil-resistance/facilitation.", "Conclude that algorithm choice depends on use-case tradeoffs."), forbidden_inferences=("Do not claim distributed automatically means decentralized.", "Do not claim PoW's hash puzzle alone is the complete consensus decision rule.", "Do not describe Nakamoto finality as deterministic or PBFT finality as probabilistic."), grading_rubric_id=RUBRIC_ID, boss_question=True))

    if len(exercises) != TOTAL_COUNT:
        raise AssertionError(f"total Level-2 bank count drifted: {len(exercises)}")
    if sum(item.integrity_question for item in exercises) != INTEGRITY_COUNT:
        raise AssertionError("Level-2 integrity count drifted")
    if sum(item.boss_question for item in exercises) != 1:
        raise AssertionError("Level-2 Boss count drifted")
    if len({item.exercise_id for item in exercises}) != TOTAL_COUNT:
        raise AssertionError("Level-2 exercise IDs are not unique")
    return tuple(exercises)


def level2_provenance_records(exercises: Sequence[Exercise], *, source_key: str = "mastering_blockchain_4e_2023") -> tuple[dict[str, object], ...]:
    targets = {(item.concept, item.subconcept): item for item in level2_targets()}
    source_map = level2_source_map()
    records: list[dict[str, object]] = []
    for exercise in exercises:
        locations = []
        for source_ref in exercise.source_refs:
            raw = source_map[source_ref]
            locations.append({"chapter": raw["chapter"], "section": raw["section"], "pdf_pages": list(raw["pdf_pages"]), "legacy_source_ref": source_ref})
        if not exercise.boss_question:
            target = targets.get((exercise.concept, exercise.subconcept))
            if target is None or exercise.source_refs != (target.source_ref,):
                raise AssertionError(f"Level-2 provenance target mismatch: {exercise.exercise_id}")
        records.append({"exercise_id": exercise.exercise_id, "source_key": source_key, "supports": ["question", "expected_answer", "required_reasoning_points"], "locations": locations})
    return tuple(records)
