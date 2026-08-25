from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .pyramid import Exercise


CURRICULUM_ID = "mastering_blockchain_4e_2023_book01"
SOURCE_KEY = "mastering_blockchain_4e_2023"
LEVEL = 3
RUBRIC_ID = "MB4E-L3-RUBRIC-V1"
ORDINARY_VARIANTS_PER_TARGET = 13
INTEGRITY_COUNT = 50


@dataclass(frozen=True, slots=True)
class Level3Target:
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
    "Explain the source-supported transaction rule for {label}.",
    "What does the book establish about {label}?",
    "Give a precise technical explanation of {label}.",
    "A learner is confused about {label}. What should Roberta explain?",
    "State the key transaction-lifecycle mechanism involved in {label}.",
    "How should {label} be described without adding unsupported assumptions?",
    "What source-supported point must an answer about {label} include?",
    "Correct a vague explanation of {label} using the book's transaction model.",
    "What would a correct operational summary of {label} say?",
    "Apply the book's explanation of {label} to a generic transaction scenario.",
    "What distinction is essential when reasoning about {label}?",
    "If auditing an answer about {label}, what core transaction point must be present?",
    "What conclusion about {label} follows from the source material?",
)


def _pages(start: int, end: int) -> tuple[int, ...]:
    return tuple(range(start, end + 1))


CH6_LIFECYCLE = "MB4E-CH6-P198-199-BTC-TX-LIFECYCLE"
CH6_STRUCTURE = "MB4E-CH6-P200-203-BTC-TX-STRUCTURE"
CH9_TYPES = "MB4E-CH9-P297-298-ETH-TX-TYPES"
CH9_EXECUTION = "MB4E-CH9-P299-301-ETH-TX-EXECUTION"
CH13_POS_FLOW = "MB4E-CH13-P451-452-ETH-POS-TX-FLOW"
CH14_FABRIC_FLOW = "MB4E-CH14-P496-497-FABRIC-TX-LIFECYCLE"


def level3_source_map() -> dict[str, dict[str, object]]:
    return {
        CH6_LIFECYCLE: {
            "chapter": "Chapter 6",
            "section": "Bitcoin transaction lifecycle, validation, and fees",
            "pdf_pages": _pages(198, 199),
        },
        CH6_STRUCTURE: {
            "chapter": "Chapter 6",
            "section": "Bitcoin transaction data structure, inputs, outputs, and verification",
            "pdf_pages": _pages(200, 203),
        },
        CH9_TYPES: {
            "chapter": "Chapter 9",
            "section": "Ethereum transaction types, contract creation, and message calls",
            "pdf_pages": _pages(297, 298),
        },
        CH9_EXECUTION: {
            "chapter": "Chapter 9",
            "section": "Ethereum transaction validation, execution, and state transition",
            "pdf_pages": _pages(299, 301),
        },
        CH13_POS_FLOW: {
            "chapter": "Chapter 13",
            "section": "Ethereum transaction flow after The Merge",
            "pdf_pages": _pages(451, 452),
        },
        CH14_FABRIC_FLOW: {
            "chapter": "Chapter 14",
            "section": "Hyperledger Fabric transaction lifecycle",
            "pdf_pages": _pages(496, 497),
        },
    }


def _target(
    concept: str,
    subconcept: str,
    principle: str,
    source_ref: str,
    *required_points: str,
    forbidden: Sequence[str] = (),
) -> Level3Target:
    source = level3_source_map()[source_ref]
    return Level3Target(
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


def level3_targets() -> tuple[Level3Target, ...]:
    return (
        _target("bitcoin_transactions", "regular_vs_coinbase", "A normal Bitcoin spend is signed by the sender and references a previous transaction output, while a coinbase input has no previous-transaction reference and uses special coinbase fields.", CH6_LIFECYCLE, "Normal spends reference previous UTXOs and require the sender's signature.", "Coinbase inputs do not reference a previous transaction."),
        _target("bitcoin_transactions", "sign_broadcast_pool", "A Bitcoin transaction is created through wallet software, signed with the sender's private key, broadcast across the network, and held in transaction pools until selected for a candidate block.", CH6_LIFECYCLE, "Creation/signing precede network broadcast.", "Unconfirmed transactions are temporarily held in node memory pools."),
        _target("bitcoin_transactions", "confirmation_finality", "After inclusion in a mined block, confirmations accumulate as further blocks are accepted; additional confirmations reduce the practical probability of reversal rather than changing the transaction into a different object.", CH6_LIFECYCLE, "Confirmations begin after block inclusion.", "More confirmations increase confidence against reversal.", forbidden=("Do not claim a fixed number of confirmations is an absolute protocol guarantee of irreversibility.",)),
        _target("bitcoin_transactions", "validation_rules", "Bitcoin nodes validate that referenced inputs are unspent, output value does not exceed input value, and digital signatures/scripts are valid before a transaction is eligible for inclusion.", CH6_LIFECYCLE, "Inputs must be unspent.", "Outputs cannot exceed inputs.", "Signatures must validate."),
        _target("bitcoin_transactions", "fees_and_selection", "Bitcoin transaction fees equal input value minus output value and incentivize miners; miners may prefer higher-fee transactions when selecting from the memory pool.", CH6_LIFECYCLE, "Fee equals sum(inputs) minus sum(outputs).", "Fees influence transaction-selection priority.", forbidden=("Do not reverse the fee formula.",)),
        _target("bitcoin_structure", "metadata", "A Bitcoin transaction contains metadata such as version, size or weight, input/output counts, transaction hash, and locktime alongside its inputs and outputs.", CH6_STRUCTURE, "Metadata describes processing/version and transaction shape rather than the spend conditions alone."),
        _target("bitcoin_structure", "utxo_inputs", "A regular Bitcoin input spends a previous UTXO by referencing the previous transaction hash and output index and supplying an unlocking script that satisfies the prior output's locking conditions.", CH6_STRUCTURE, "Inputs consume previous UTXOs.", "The previous transaction hash and output index identify the UTXO."),
        _target("bitcoin_structure", "outputs_locking", "A Bitcoin output specifies a value and a locking script; the locking script defines conditions that must later be satisfied to spend that output.", CH6_STRUCTURE, "Outputs create spendable conditions and value.", "ScriptPubKey is the output locking script."),
        _target("bitcoin_structure", "script_verification", "Bitcoin verification uses Script to check cryptographic signatures, inputs, outputs, and the value relationship between them; ScriptSig and ScriptPubKey participate in satisfying spending conditions.", CH6_STRUCTURE, "Signature/script validity is part of transaction verification.", "Input value must be at least output value."),
        _target("bitcoin_structure", "locktime", "Bitcoin locktime defines the earliest time or block height at which a transaction becomes valid under the transaction structure described by the book.", CH6_STRUCTURE, "Locktime can be represented by a Unix timestamp or block height."),
        _target("ethereum_transactions", "simple_transfer", "An Ethereum simple transaction is the standard value-transfer transaction used to move ether between accounts.", CH9_TYPES, "Simple transactions transfer ether between accounts."),
        _target("ethereum_transactions", "contract_creation", "An Ethereum contract-creation transaction supplies sender/origin, gas parameters, endowment and initialization EVM code; successful initialization creates the contract account and state, while execution failure such as out-of-gas prevents the state change described by the source.", CH9_TYPES, "Contract creation executes initialization EVM code.", "Successful creation changes world state; failed initialization does not create the successful state transition."),
        _target("ethereum_transactions", "message_call_transaction", "A message-call transaction is an externally initiated, signed blockchain transaction used to invoke deployed contract code and can produce a state transition while consuming gas.", CH9_TYPES, "Message-call transactions invoke contract code.", "They are blockchain write transactions, not merely local simulations."),
        _target("ethereum_transactions", "messages_vs_transactions", "Ethereum messages can be produced internally by contracts during execution, whereas blockchain transactions originate externally from EOAs and are digitally signed by the sender.", CH9_TYPES, "Transactions originate from external actors/EOAs.", "Messages may be produced by contracts inside the execution environment."),
        _target("ethereum_transactions", "local_call_vs_write", "A local Ethereum call executes synchronously on a node without broadcast, mining, gas cost, ether transfer, or persistent state change; a message-call transaction is a write operation that can cost gas and change state.", CH9_EXECUTION, "Local calls are simulations/read operations.", "Message-call transactions can change blockchain state.", forbidden=("Do not treat a local call and a message-call transaction as the same operation.",)),
        _target("ethereum_transactions", "validation_prechecks", "Before Ethereum transaction execution, the transaction must be well formed and RLP encoded, its signature must be valid, its nonce must match the sender account nonce, its gas limit must cover gas used, and the sender must have sufficient balance for execution cost.", CH9_EXECUTION, "Validity is checked before execution.", "Signature, nonce, gas, encoding, and balance checks are part of the listed preconditions."),
        _target("ethereum_transactions", "state_transition", "Ethereum can be modeled as a transaction-based state machine in which executing transactions incrementally transforms the current state into a new state that is persisted through the blockchain's state structures.", CH9_EXECUTION, "Transactions drive state transitions.", "World/account state and transaction-related structures persist the resulting state."),
        _target("ethereum_transactions", "account_nonce", "For an Ethereum externally owned account, the account nonce increments when transactions are sent and transaction validation requires the transaction nonce to match the sender account's current nonce.", CH9_EXECUTION, "Nonce participates in ordering/validity of account-originated transactions."),
        _target("ethereum_pos_flow", "submission_mempool_gossip", "After The Merge, a user composes and signs a transaction, submits it to an execution client for balance/signature checks, and a valid transaction enters the mempool and propagates through execution-layer P2P gossip.", CH13_POS_FLOW, "Execution client validation precedes mempool admission.", "Valid pending transactions propagate through execution-layer gossip."),
        _target("ethereum_pos_flow", "proposer_payload", "A protocol-selected block proposer works with an execution client that gathers mempool transactions into an execution payload, executes them locally on the EVM, and passes the payload to the consensus client for beacon-block construction.", CH13_POS_FLOW, "Execution payload construction and EVM execution are execution-client responsibilities.", "Consensus client encapsulates the payload in a beacon block."),
        _target("ethereum_pos_flow", "distributed_reexecution", "Other consensus nodes receive the beacon block and pass its payload to their execution clients, which re-execute transactions locally to validate the proposed state change before accepting the block.", CH13_POS_FLOW, "Receiving nodes independently validate the proposed execution result."),
        _target("ethereum_pos_flow", "checkpoint_finality", "The post-Merge flow describes finalization through validator attestations and a supermajority link between checkpoints; checkpoints require 66% attestation of total staked ETH to qualify as a supermajority link.", CH13_POS_FLOW, "Finality depends on validator attestations and checkpoint links.", "The source specifies a 66% attestation threshold for a supermajority link.", forbidden=("Do not describe post-Merge Ethereum finality as PoW mining confirmation.",)),
        _target("fabric_transactions", "proposal_and_simulation", "In Hyperledger Fabric, an enrolled client proposes a transaction to endorsing peers; endorsers simulate chaincode and produce a read-write set without updating the ledger at the simulation stage.", CH14_FABRIC_FLOW, "Client enrollment precedes proposal.", "Endorser simulation produces an RW set without committing ledger state."),
        _target("fabric_transactions", "ordering_and_commit", "The application submits endorsed transactions and read-write sets to the ordering service, which orders them into a block and broadcasts it to committing peers for validation and commitment.", CH14_FABRIC_FLOW, "Ordering follows endorsement and precedes commit.", "Committers receive an ordered block rather than mining a block."),
        _target("fabric_transactions", "validation_and_notification", "Fabric committing peers validate endorsement policy and read-set versions, commit the block and valid state updates, check transaction logic/state conflicts, and notify the client or application of success or failure.", CH14_FABRIC_FLOW, "Validation checks endorsements and state-version conflicts.", "Clients receive a final success/failure notification."),
    )


ORDINARY_COUNT = len(level3_targets()) * ORDINARY_VARIANTS_PER_TARGET
TOTAL_COUNT = ORDINARY_COUNT + INTEGRITY_COUNT + 1


def _label(target: Level3Target) -> str:
    return f"{target.concept.replace('_', ' ')} / {target.subconcept.replace('_', ' ')}"


def build_level3_bank(curriculum_id: str = CURRICULUM_ID) -> tuple[Exercise, ...]:
    exercises: list[Exercise] = []
    sequence = 1
    targets = level3_targets()

    for target in targets:
        for template in QUESTION_TEMPLATES:
            exercises.append(
                Exercise(
                    exercise_id=f"MB4E-L03-{sequence:05d}",
                    curriculum_id=curriculum_id,
                    level=LEVEL,
                    concept=target.concept,
                    subconcept=target.subconcept,
                    question=template.format(label=_label(target)),
                    expected_answer=target.principle,
                    source_refs=(SOURCE_KEY, target.source_ref),
                    question_type="application",
                    difficulty=3,
                    required_reasoning_points=target.required_points,
                    forbidden_inferences=target.forbidden_inferences,
                    grading_rubric_id=RUBRIC_ID,
                )
            )
            sequence += 1

    for index in range(INTEGRITY_COUNT):
        target = targets[index % len(targets)]
        mode = index % 2
        question = (
            f"Integrity check: State the source-supported rule for {_label(target)} and reject any claim that changes the transaction mechanism described by the book."
            if mode == 0
            else f"Integrity check: An analyst makes an overconfident claim about {_label(target)}. Give the precise source-grounded correction without inventing transaction state or execution evidence."
        )
        exercises.append(
            Exercise(
                exercise_id=f"MB4E-L03-{sequence:05d}",
                curriculum_id=curriculum_id,
                level=LEVEL,
                concept=target.concept,
                subconcept=target.subconcept,
                question=question,
                expected_answer=target.principle,
                source_refs=(SOURCE_KEY, target.source_ref),
                question_type="integrity",
                difficulty=3,
                required_reasoning_points=target.required_points,
                forbidden_inferences=target.forbidden_inferences,
                grading_rubric_id=RUBRIC_ID,
                integrity_question=True,
            )
        )
        sequence += 1

    boss_refs = (
        SOURCE_KEY,
        CH6_LIFECYCLE,
        CH6_STRUCTURE,
        CH9_TYPES,
        CH9_EXECUTION,
        CH13_POS_FLOW,
        CH14_FABRIC_FLOW,
    )
    exercises.append(
        Exercise(
            exercise_id=f"MB4E-L03-{sequence:05d}",
            curriculum_id=curriculum_id,
            level=LEVEL,
            concept="transactions",
            subconcept="boss_synthesis",
            question=(
                "Boss: Trace and compare a transaction from creation through validation, propagation, execution or ordering, commitment, and finality across Bitcoin, post-Merge Ethereum, and Hyperledger Fabric. "
                "Identify the distinct state/UTXO, validation, fee/gas, participant-role, and finality mechanics without treating the three systems as if they use one transaction model."
            ),
            expected_answer=(
                "Bitcoin spends UTXOs: a wallet signs and broadcasts a transaction, nodes validate unspent inputs/value/signatures, pending transactions sit in memory pools, miners select them into blocks, and confirmations increase confidence against reversal. "
                "Ethereum uses account/state transitions: externally signed transactions pass encoding/signature/nonce/gas/balance checks, execution clients maintain mempools and execute payloads, consensus clients and validators attest blocks, and checkpoint supermajority links provide post-Merge finality. "
                "Fabric uses an execute-order-validate style flow: enrolled clients propose, endorsers simulate chaincode into read-write sets, the ordering service orders endorsed transactions into blocks, committers validate endorsement/state versions and commit valid updates, then clients receive success/failure notification. "
                "These transaction lifecycles differ in data model, fee/gas mechanics, participant roles, validation path, and finality mechanism."
            ),
            source_refs=boss_refs,
            question_type="boss",
            difficulty=3,
            required_reasoning_points=(
                "Describe Bitcoin UTXO signing, validation, mempool/block inclusion, and confirmation behavior.",
                "Describe Ethereum signed account transactions, execution-client checks/execution, validator attestations, and checkpoint finality.",
                "Describe Fabric proposal, endorsement simulation/RW sets, ordering, validation/commit, and notification.",
                "Keep UTXO, account-state, and Fabric execute-order-validate models distinct.",
            ),
            forbidden_inferences=(
                "Do not describe Bitcoin as using Ethereum account nonces and EVM execution.",
                "Do not describe post-Merge Ethereum finality as PoW mining confirmation.",
                "Do not describe Fabric committers as proof-of-work miners.",
            ),
            grading_rubric_id=RUBRIC_ID,
            boss_question=True,
        )
    )

    if len(exercises) != TOTAL_COUNT:
        raise AssertionError(f"total Level-3 bank count drifted: {len(exercises)}")
    if sum(item.integrity_question for item in exercises) != INTEGRITY_COUNT:
        raise AssertionError("Level-3 integrity count drifted")
    if sum(item.boss_question for item in exercises) != 1:
        raise AssertionError("Level-3 Boss count drifted")
    if len({item.exercise_id for item in exercises}) != TOTAL_COUNT:
        raise AssertionError("Level-3 exercise IDs are not unique")
    return tuple(exercises)


def level3_provenance_records(
    exercises: Sequence[Exercise], *, source_key: str = SOURCE_KEY
) -> tuple[dict[str, object], ...]:
    if source_key != SOURCE_KEY:
        raise ValueError(f"Level-3 provenance source_key must be canonical {SOURCE_KEY!r}")
    targets = {(item.concept, item.subconcept): item for item in level3_targets()}
    source_map = level3_source_map()
    records: list[dict[str, object]] = []
    for exercise in exercises:
        locations = []
        for source_ref in exercise.source_refs:
            if source_ref == SOURCE_KEY:
                continue
            raw = source_map[source_ref]
            locations.append(
                {
                    "chapter": raw["chapter"],
                    "section": raw["section"],
                    "pdf_pages": list(raw["pdf_pages"]),
                    "legacy_source_ref": source_ref,
                }
            )
        if not exercise.boss_question:
            target = targets.get((exercise.concept, exercise.subconcept))
            if target is None or exercise.source_refs != (SOURCE_KEY, target.source_ref):
                raise AssertionError(f"Level-3 provenance target mismatch: {exercise.exercise_id}")
        records.append(
            {
                "exercise_id": exercise.exercise_id,
                "source_key": SOURCE_KEY,
                "supports": ["question", "expected_answer", "required_reasoning_points"],
                "locations": locations,
            }
        )
    return tuple(records)
