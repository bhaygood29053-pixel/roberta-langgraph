from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .pyramid import Exercise


CURRICULUM_ID = "mastering_blockchain_4e_2023_book01"
SOURCE_KEY = "mastering_blockchain_4e_2023"
LEVEL = 5
RUBRIC_ID = "MB4E-L5-RUBRIC-V1"
ORDINARY_VARIANTS_PER_TARGET = 13
INTEGRITY_COUNT = 50


@dataclass(frozen=True, slots=True)
class Level5Target:
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
    "Explain the source-supported smart-contract rule for {label}.",
    "What does the book establish about {label}?",
    "Give a precise technical explanation of {label}.",
    "A learner is confused about {label}. What should Roberta explain?",
    "State the key smart-contract mechanism involved in {label}.",
    "How should {label} be described without adding unsupported assumptions?",
    "What source-supported point must an answer about {label} include?",
    "Correct a vague explanation of {label} using the book's smart-contract model.",
    "What would a correct operational summary of {label} say?",
    "Apply the book's explanation of {label} to a generic smart-contract development scenario.",
    "What distinction is essential when reasoning about {label}?",
    "If auditing an answer about {label}, what core contract-development point must be present?",
    "What conclusion about {label} follows from the source material?",
)


def _pages(start: int, end: int) -> tuple[int, ...]:
    return tuple(range(start, end + 1))


CH8_FOUNDATIONS = "MB4E-CH8-P254-258-SMART-CONTRACT-FOUNDATIONS"
CH8_RICARDIAN = "MB4E-CH8-P258-263-RICARDIAN-TEMPLATES"
CH8_ORACLES = "MB4E-CH8-P264-272-ORACLES"
CH8_DEPLOY_SECURITY = "MB4E-CH8-P273-278-DEPLOYMENT-DAO-ADVANCES"
CH11_COMPILER_TOOLS = "MB4E-CH11-P376-387-COMPILER-TOOLS"
CH11_FUNCTIONS = "MB4E-CH11-P387-392-SOLIDITY-FUNCTIONS"
CH11_DATA = "MB4E-CH11-P392-398-SOLIDITY-DATA"
CH11_STRUCTURES = "MB4E-CH11-P398-402-SOLIDITY-STRUCTURES"
CH12_WEB3_DEPLOY = "MB4E-CH12-P404-414-WEB3-DEPLOYMENT"
CH12_FRONTENDS = "MB4E-CH12-P414-424-WEB3-FRONTENDS"
CH12_TRUFFLE = "MB4E-CH12-P424-437-TRUFFLE-WORKFLOW"
CH12_IPFS = "MB4E-CH12-P437-439-IPFS-DAPP"


def level5_source_map() -> dict[str, dict[str, object]]:
    return {
        CH8_FOUNDATIONS: {
            "chapter": "Chapter 8",
            "section": "Smart-contract definitions, properties, state-machine behavior, and real-world constraints",
            "pdf_pages": _pages(254, 258),
        },
        CH8_RICARDIAN: {
            "chapter": "Chapter 8",
            "section": "Ricardian contracts, smart-contract templates, DSLs, and legal/operational semantics",
            "pdf_pages": _pages(258, 263),
        },
        CH8_ORACLES: {
            "chapter": "Chapter 8",
            "section": "Oracle data flow, authenticity proofs, oracle types, and the blockchain oracle problem",
            "pdf_pages": _pages(264, 272),
        },
        CH8_DEPLOY_SECURITY: {
            "chapter": "Chapter 8",
            "section": "Deployment, determinism, DAO/reentrancy lessons, and smart-contract platform advances",
            "pdf_pages": _pages(273, 278),
        },
        CH11_COMPILER_TOOLS: {
            "chapter": "Chapter 11",
            "section": "Ethereum languages, solc, ABI/bytecode/gas, Ganache, Truffle, and development lifecycle",
            "pdf_pages": _pages(376, 387),
        },
        CH11_FUNCTIONS: {
            "chapter": "Chapter 11",
            "section": "Solidity functions, signatures, calls, visibility, modifiers, fallback, and constructors",
            "pdf_pages": _pages(387, 392),
        },
        CH11_DATA: {
            "chapter": "Chapter 11",
            "section": "Solidity variables, storage, value/reference types, data locations, arrays, structs, and mappings",
            "pdf_pages": _pages(392, 398),
        },
        CH11_STRUCTURES: {
            "chapter": "Chapter 11",
            "section": "Control flow, events, inheritance, libraries, and error handling",
            "pdf_pages": _pages(398, 402),
        },
        CH12_WEB3_DEPLOY: {
            "chapter": "Chapter 12",
            "section": "Web3/Geth RPC, contract deployment, ABI/bytecode, querying, calls, and JSON-RPC",
            "pdf_pages": _pages(404, 414),
        },
        CH12_FRONTENDS: {
            "chapter": "Chapter 12",
            "section": "web3.js providers, contract instances, frontend integration, and function calls",
            "pdf_pages": _pages(414, 424),
        },
        CH12_TRUFFLE: {
            "chapter": "Chapter 12",
            "section": "Truffle initialization, compile/test/migrate workflow, console interaction, and Ganache deployment",
            "pdf_pages": _pages(424, 437),
        },
        CH12_IPFS: {
            "chapter": "Chapter 12",
            "section": "IPFS as decentralized storage for DApp frontend content",
            "pdf_pages": _pages(437, 439),
        },
    }


def _target(
    concept: str,
    subconcept: str,
    principle: str,
    source_ref: str,
    *required_points: str,
    forbidden: Sequence[str] = (),
) -> Level5Target:
    source = level5_source_map()[source_ref]
    return Level5Target(
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


def level5_targets() -> tuple[Level5Target, ...]:
    return (
        _target("smart_contract_foundations", "definition_and_properties", "The source defines a smart contract as a secure and unstoppable computer program representing an agreement that is automatically executable and enforceable; core properties include automatic execution, enforceability, security, determinism, semantic soundness, and unstoppable execution, with the first four treated as minimum requirements.", CH8_FOUNDATIONS, "Automatic execution, enforceability, security, and determinism are central properties.", "The source distinguishes optional/relaxable semantic-soundness and unstoppable properties from the minimum set."),
        _target("smart_contract_foundations", "determinism_and_consensus", "Determinism requires the same input to produce the same result on every node; divergent results would prevent nodes from reaching a consistent distributed consensus about contract execution.", CH8_FOUNDATIONS, "Same input should yield the same output across nodes.", forbidden=("Do not describe nondeterministic execution as acceptable for replicated smart-contract consensus.",)),
        _target("smart_contract_foundations", "state_machine_model", "Smart contracts typically manage internal state through the state-machine model provided by the underlying blockchain, advancing contract state when predefined criteria and conditions are satisfied.", CH8_FOUNDATIONS, "Contract state changes according to predefined conditions.", "The underlying blockchain supplies the replicated execution/state substrate."),
        _target("smart_contract_foundations", "code_and_legal_world", "The source highlights a gap between machine-executable code and legal prose: smart contracts emphasize operational execution, while legal enforceability, human readability, regulatory interpretation, and dispute resolution may require additional semantic/legal representation.", CH8_FOUNDATIONS, "Operational execution and legal meaning are separate concerns.", forbidden=("Do not claim source code alone automatically resolves all legal enforceability questions.",)),
        _target("ricardian_contracts", "ricardian_vs_smart", "A Ricardian contract is a human-readable and machine-readable legal document that is digitally signed and hashed so its identifier can link legal prose to operational transactions, while a smart contract is primarily oriented toward executable performance.", CH8_RICARDIAN, "Ricardian contracts emphasize legal prose plus machine-readable structure.", "The document hash serves as a secure identifier linking the contract to transactions."),
        _target("ricardian_contracts", "semantics_and_performance", "The source distinguishes denotational/legal semantics from operational semantics/performance and presents an ideal smart contract as combining meaningful contractual semantics with executable business logic.", CH8_RICARDIAN, "Legal meaning and execution correctness are distinct dimensions."),
        _target("smart_contract_templates", "templates_and_dsl", "Smart-contract templates aim to standardize legally meaningful agreements, especially in finance, by linking prose, parameters, and executable code; domain-specific languages trade general expressiveness for optimized constructs within a specific domain.", CH8_RICARDIAN, "Templates link legal prose with code and parameters.", "DSLs are optimized for a bounded application domain rather than general-purpose software."),
        _target("oracles", "external_data_role", "Blockchains are closed systems and smart contracts cannot directly access off-chain facts; an oracle acts as an interface that brings external data into contract execution so business logic can depend on real-world inputs.", CH8_ORACLES, "Oracles bridge off-chain data into smart-contract logic.", forbidden=("Do not claim a smart contract can directly fetch arbitrary internet data without an external mechanism.",)),
        _target("oracles", "authenticated_data_flow", "The generic oracle flow is request, external data retrieval, authenticity proof or attestation, optional decentralized storage of large proofs, and delivery of data plus proof back to the smart contract; cryptographic evidence supports authenticity but does not by itself guarantee that the original data source is factually correct.", CH8_ORACLES, "Separate proof of authenticity from truth of the underlying data.", "Data and proof travel through a defined request/attestation/delivery flow."),
        _target("oracles", "oracle_problem", "The blockchain oracle problem is the trust conflict created when a trustless blockchain depends on third-party data sources or oracle infrastructure that can fail, become malicious, or provide incorrect data; decentralization, aggregation, incentives, and attestation can reduce but not magically eliminate this trust problem.", CH8_ORACLES, "Oracle failure or bad source data can damage contract correctness.", forbidden=("Do not claim cryptographic attestation proves that a false source value is objectively true.",)),
        _target("oracles", "oracle_types", "The source distinguishes inbound oracles that feed external data into contracts, outbound or reverse oracles that move blockchain-derived signals outward, computation oracles that offload expensive work, aggregation/crowd-wisdom oracles that combine sources, decentralized oracles that reduce reliance on one trusted party, and cryptoeconomic oracles that use incentives or penalties.", CH8_ORACLES, "Keep inbound, outbound, computation, aggregation, decentralized, and cryptoeconomic roles distinct."),
        _target("smart_contract_security", "deployment_and_determinism", "Smart contracts can run on multiple platforms and languages, but blockchain execution requires deterministic behavior; a contract should be verified and tested before production deployment because the replicated network will consistently execute whatever logic the code actually contains.", CH8_DEPLOY_SECURITY, "Determinism is a cross-platform requirement.", "Testing and verification precede production deployment."),
        _target("smart_contract_security", "dao_reentrancy", "The DAO incident illustrates reentrancy risk: external control returned before the contract updated its internal withdrawal state, allowing repeated withdrawals; the source uses this to emphasize thorough testing, verification, and skepticism toward simplistic 'code is law' claims.", CH8_DEPLOY_SECURITY, "State was not updated before repeated withdrawal opportunity.", "The incident motivated a hard fork and exposed governance/immutability tradeoffs."),
        _target("ethereum_toolchain", "solc_bytecode_abi_gas", "The Solidity compiler solc converts high-level Solidity into EVM bytecode, can emit the JSON ABI used by external programs to interact with deployed contracts, and can estimate gas for contract construction and operations.", CH11_COMPILER_TOOLS, "Bytecode is EVM-executable output.", "ABI describes callable functions/events and their types.", "Gas estimation helps approximate execution/deployment cost."),
        _target("ethereum_toolchain", "abi_interface", "The ABI is the interface between EVM-level bytecode and high-level callers: external programs generally need both a deployed contract address and the ABI in order to encode calls and interpret functions/events correctly.", CH11_COMPILER_TOOLS, "Contract address identifies the deployed instance.", "ABI describes its high-level callable interface."),
        _target("ethereum_toolchain", "ganache_role", "Ganache is a simulated personal Ethereum blockchain used for rapid local development and testing, exposing accounts, blocks, transactions, configurable chain parameters, and RPC without requiring developers to test directly on mainnet.", CH11_COMPILER_TOOLS, "Ganache is a local simulated chain.", forbidden=("Do not treat mainnet as the normal place for preliminary smart-contract testing.",)),
        _target("ethereum_toolchain", "truffle_role", "Truffle provides an Ethereum development environment with contract compilation/linking, automated testing, deployment/migrations, and console interaction, simplifying the manual workflow across private, test, and public networks.", CH11_COMPILER_TOOLS, "Truffle supports compile, test, deploy/migrate, and interaction workflows."),
        _target("ethereum_toolchain", "development_lifecycle", "The source organizes contract development into writing, testing, and deploying, with a user interface as an optional post-deployment layer; contracts should be tested in simulated/private environments and public test networks before production mainnet deployment.", CH11_COMPILER_TOOLS, "Writing precedes testing, which precedes production deployment."),
        _target("solidity", "static_typing_pragma_import", "Solidity is a statically typed contract-oriented language; variable types are checked at compile time, pragma constrains compatible compiler versions, and import brings symbols from other Solidity source files into scope.", CH11_COMPILER_TOOLS, "Static type checking occurs at compile time.", "Pragma and import serve compiler compatibility and modularity roles."),
        _target("solidity", "functions_and_signatures", "Solidity functions declare parameters, visibility, state mutability, and return types; a function selector/signature is derived from the first four bytes of the Keccak-256 hash of the canonical function signature string and is used in contract interfaces.", CH11_FUNCTIONS, "Function declaration includes visibility/mutability and optional returns.", "The selector is four bytes derived from Keccak-256 of the signature string."),
        _target("solidity", "internal_external_calls", "Internal function calls stay within the current contract context and compile to direct EVM control flow, while external function calls use message-call semantics and copy parameters into memory; calling through this is treated as an external call.", CH11_FUNCTIONS, "Internal and external calls have different EVM/call semantics."),
        _target("solidity", "visibility_and_mutability", "Solidity visibility controls whether functions are external, public, internal, or private, while mutability modifiers such as pure, view, and payable govern state access/modification and whether ether can accompany a call.", CH11_FUNCTIONS, "Visibility and state mutability solve different access/execution concerns."),
        _target("solidity", "fallback_constructor_modifiers", "Fallback behavior handles unmatched calls or ether reception when appropriately payable, constructors run once at contract creation, and modifier functions wrap or guard function behavior by applying conditions around the function body.", CH11_FUNCTIONS, "Constructor is creation-time only.", "Modifiers commonly enforce preconditions or guards."),
        _target("solidity_data", "variable_scopes_storage", "Solidity distinguishes local, global, and state variables; state variables persist in contract storage while local variables are scoped to function execution, and public state variables receive generated getter accessors.", CH11_DATA, "State variables persist in storage.", "Local variables are function-scoped."),
        _target("solidity_data", "value_reference_locations", "Value types hold values directly while reference types point to data structures such as arrays, structs, and mappings; reference-type data location must be reasoned about explicitly across storage, memory, and calldata because copying and persistence have gas and mutability consequences.", CH11_DATA, "Storage is persistent contract state.", "Memory/calldata are transient execution locations with different semantics."),
        _target("solidity_data", "arrays_structs_mappings", "Arrays group same-typed elements, structs group heterogeneous fields into custom types, and mappings associate keys with values; these constructs model contract data but differ in layout, access, and data-location behavior.", CH11_DATA, "Keep arrays, structs, and mappings conceptually distinct."),
        _target("solidity_structures", "events", "Solidity events write information to EVM transaction logs so external interfaces can observe contract state changes or notable conditions; contracts do not read those logs as ordinary contract storage.", CH11_STRUCTURES, "Events support external observation through logs.", forbidden=("Do not describe event logs as ordinary mutable contract storage read back by contracts.",)),
        _target("solidity_structures", "inheritance_libraries_errors", "Solidity supports inheritance for non-private parent members and libraries for reusable stateless code; error handling with assert, require, revert, and try/catch aborts failing execution and reverts state according to the construct and context.", CH11_STRUCTURES, "Private parent members are not inherited as accessible members.", "Libraries have restrictions such as no state variables and no receiving ether.", "Failed execution reverts state rather than preserving partial state changes."),
        _target("web3_development", "web3_rpc_provider", "Web3 provides a JavaScript/API layer for communicating with an Ethereum node through enabled RPC methods; a provider is the application's entry point to the node's HTTP-RPC service and enables contract and chain interaction.", CH12_WEB3_DEPLOY, "Web3 communicates through node RPC.", "Only APIs exposed by the node are available to callers."),
        _target("web3_development", "deployment_and_contract_instance", "A deployment workflow combines contract bytecode with an ABI-driven interface, submits a contract-creation transaction from an account, and after mining exposes a contract address and transaction hash that callers can use with the ABI to construct a contract instance.", CH12_WEB3_DEPLOY, "Bytecode is used for deployment; ABI plus address is used for high-level interaction.", "Successful deployment yields a contract address and creation transaction hash."),
        _target("web3_development", "calls_and_json_rpc", "Contracts can be queried from Geth/Web3 or through JSON-RPC over HTTP; local call-style invocations can execute contract logic for a result without persisting a state change, while state-changing interactions require blockchain transactions.", CH12_WEB3_DEPLOY, "JSON-RPC provides a transport/interface to node methods.", forbidden=("Do not equate a local .call simulation with a mined state-changing transaction.",)),
        _target("web3_frontend", "frontend_contract_bridge", "A DApp frontend can use web3.js from HTML/JavaScript to create a provider-backed web3 object, bind an ABI and deployed address into a contract instance, pass user input to contract methods, and render returned values to the user interface.", CH12_FRONTENDS, "Provider, ABI, and contract address connect the UI to the deployed contract."),
        _target("truffle_workflow", "compile_test_migrate_console", "The Truffle workflow initializes a project structure, compiles Solidity contracts into artifacts, runs automated tests against a development chain such as Ganache, migrates/deploys contracts using configured network settings, and then exposes deployed instances through the Truffle console for inspection and calls.", CH12_TRUFFLE, "Project initialization, compile, test, migrate, and console interaction are distinct workflow stages."),
        _target("dapp_architecture", "ipfs_frontend_storage", "The source presents IPFS as a decentralized storage layer for DApp web content: blockchain provides decentralized state/computation while frontend HTML/JavaScript assets can be added and pinned in IPFS to reduce reliance on centralized web hosting.", CH12_IPFS, "IPFS stores frontend content; it does not replace the smart-contract execution layer."),
    )


ORDINARY_COUNT = len(level5_targets()) * ORDINARY_VARIANTS_PER_TARGET
TOTAL_COUNT = ORDINARY_COUNT + INTEGRITY_COUNT + 1


def _label(target: Level5Target) -> str:
    return f"{target.concept.replace('_', ' ')} / {target.subconcept.replace('_', ' ')}"


def build_level5_bank(curriculum_id: str = CURRICULUM_ID) -> tuple[Exercise, ...]:
    exercises: list[Exercise] = []
    sequence = 1
    targets = level5_targets()

    for target in targets:
        for template in QUESTION_TEMPLATES:
            exercises.append(
                Exercise(
                    exercise_id=f"MB4E-L05-{sequence:05d}",
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
        question = (
            f"Integrity check: State the source-supported rule for {_label(target)} and reject any claim that changes the contract, toolchain, or execution mechanism described by the book."
            if index % 2 == 0
            else f"Integrity check: An analyst makes an overconfident claim about {_label(target)}. Give the precise source-grounded correction without inventing deployment, state, oracle, or execution evidence."
        )
        exercises.append(
            Exercise(
                exercise_id=f"MB4E-L05-{sequence:05d}",
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

    boss_refs = (SOURCE_KEY, *level5_source_map().keys())
    exercises.append(
        Exercise(
            exercise_id=f"MB4E-L05-{sequence:05d}",
            curriculum_id=curriculum_id,
            level=LEVEL,
            concept="smart_contracts",
            subconcept="boss_synthesis",
            question=(
                "Boss: Design and explain an end-to-end source-grounded smart-contract workflow from contract semantics and oracle assumptions through Solidity implementation, local testing, ABI/bytecode generation, deployment, Web3/RPC interaction, frontend integration, and decentralized frontend storage. "
                "Identify determinism, state, security, reentrancy, oracle-trust, data-location, call-vs-transaction, and deployment/testing boundaries without inventing capabilities the source does not support."
            ),
            expected_answer=(
                "Begin with contract semantics and deterministic business rules, treating off-chain facts as oracle-supplied inputs whose authenticity and factual correctness are separate trust questions. "
                "Implement the rules in Solidity with explicit types, function visibility/mutability, persistent state and transient data locations, events, guards/modifiers, and error handling; reason carefully about external calls and state-update ordering because the DAO reentrancy example shows the danger of exposing external control before internal state is safely updated. "
                "Compile with solc to obtain EVM bytecode and an ABI, estimate gas, and test on a simulated/private environment such as Ganache before production deployment. "
                "Use a framework such as Truffle to compile, test, migrate/deploy, and interact with deployed instances, or use Web3/Geth directly. After deployment, the contract address plus ABI identify the high-level interface. "
                "Web3 communicates with the Ethereum node through enabled RPC methods; local call-style invocations can read/simulate without persistent state changes, whereas writes require transactions. "
                "A browser frontend can create a provider-backed web3 object, bind the ABI and address into a contract instance, pass user input to methods, and render results. IPFS can host the frontend assets as a decentralized storage layer while the blockchain remains the execution/state layer."
            ),
            source_refs=boss_refs,
            question_type="boss",
            difficulty=3,
            required_reasoning_points=(
                "Explain smart-contract semantics, deterministic execution, and oracle trust boundaries.",
                "Explain Solidity state/data/function mechanics and security boundaries including reentrancy.",
                "Explain compile/test/deploy artifacts and the ABI/address relationship.",
                "Explain Web3/RPC calls versus state-changing transactions and frontend contract binding.",
                "Explain Truffle/Ganache workflow and IPFS's role as frontend storage rather than contract execution.",
            ),
            forbidden_inferences=(
                "Do not treat oracle attestation as proof that an incorrect source value is factually true.",
                "Do not treat a local Web3 call as a mined state-changing transaction.",
                "Do not describe IPFS as executing Ethereum smart-contract state transitions.",
                "Do not claim deployment should precede testing.",
            ),
            grading_rubric_id=RUBRIC_ID,
            boss_question=True,
        )
    )

    if len(exercises) != TOTAL_COUNT:
        raise AssertionError(f"total Level-5 bank count drifted: {len(exercises)}")
    if sum(item.integrity_question for item in exercises) != INTEGRITY_COUNT:
        raise AssertionError("Level-5 integrity count drifted")
    if sum(item.boss_question for item in exercises) != 1:
        raise AssertionError("Level-5 Boss count drifted")
    if len({item.exercise_id for item in exercises}) != TOTAL_COUNT:
        raise AssertionError("Level-5 exercise IDs are not unique")
    return tuple(exercises)


def level5_provenance_records(
    exercises: Sequence[Exercise], *, source_key: str = SOURCE_KEY
) -> tuple[dict[str, object], ...]:
    if source_key != SOURCE_KEY:
        raise ValueError(f"Level-5 provenance source_key must be canonical {SOURCE_KEY!r}")
    targets = {(item.concept, item.subconcept): item for item in level5_targets()}
    source_map = level5_source_map()
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
                raise AssertionError(f"Level-5 provenance target mismatch: {exercise.exercise_id}")
        records.append(
            {
                "exercise_id": exercise.exercise_id,
                "source_key": SOURCE_KEY,
                "supports": ["question", "expected_answer", "required_reasoning_points"],
                "locations": locations,
            }
        )
    return tuple(records)
