from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .pyramid import Exercise


CURRICULUM_ID = "mastering_blockchain_4e_2023_book01"
SOURCE_KEY = "mastering_blockchain_4e_2023"
LEVEL = 6
RUBRIC_ID = "MB4E-L6-RUBRIC-V1"
ORDINARY_VARIANTS_PER_TARGET = 13
INTEGRITY_COUNT = 50


@dataclass(frozen=True, slots=True)
class Level6Target:
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
    "Explain the source-supported tokenomics rule for {label}.",
    "What does the book establish about {label}?",
    "Give a precise technical explanation of {label}.",
    "A learner is confused about {label}. What should Roberta explain?",
    "State the key tokenization or economic mechanism involved in {label}.",
    "How should {label} be described without adding unsupported assumptions?",
    "What source-supported point must an answer about {label} include?",
    "Correct a vague explanation of {label} using the book's tokenization model.",
    "What would a correct operational summary of {label} say?",
    "Apply the book's explanation of {label} to a generic token ecosystem scenario.",
    "What distinction is essential when reasoning about {label}?",
    "If auditing an answer about {label}, what core token-design point must be present?",
    "What conclusion about {label} follows from the source material?",
)


def _pages(start: int, end: int) -> tuple[int, ...]:
    return tuple(range(start, end + 1))


CH15_FOUNDATIONS = "MB4E-CH15-P502-505-TOKENIZATION-FOUNDATIONS"
CH15_TYPES = "MB4E-CH15-P506-508-TOKEN-TYPES"
CH15_PROCESS_OFFERINGS = "MB4E-CH15-P508-511-PROCESS-OFFERINGS"
CH15_STANDARDS = "MB4E-CH15-P512-515-TOKEN-STANDARDS"
CH15_ERC20 = "MB4E-CH15-P516-527-ERC20-BUILD-DEPLOY"
CH15_ECONOMICS = "MB4E-CH15-P528-529-TOKENOMICS-ENGINEERING-TAXONOMY"


def level6_source_map() -> dict[str, dict[str, object]]:
    return {
        CH15_FOUNDATIONS: {
            "chapter": "Chapter 15",
            "section": "Token definition, blockchain tokenization, advantages, disadvantages, regulation, and security",
            "pdf_pages": _pages(502, 505),
        },
        CH15_TYPES: {
            "chapter": "Chapter 15",
            "section": "Coins versus tokens; fungible, non-fungible, stable, and security tokens",
            "pdf_pages": _pages(506, 508),
        },
        CH15_PROCESS_OFFERINGS: {
            "chapter": "Chapter 15",
            "section": "Tokenization process and ICO, STO, IEO, ETO, and DAICO offerings",
            "pdf_pages": _pages(508, 511),
        },
        CH15_STANDARDS: {
            "chapter": "Chapter 15",
            "section": "Ethereum token standards including ERC-20, ERC-223, ERC-777, ERC-721, ERC-1400/1404, ERC-1155, and ERC-4626",
            "pdf_pages": _pages(512, 515),
        },
        CH15_ERC20: {
            "chapter": "Chapter 15",
            "section": "ERC-20 interface, balances, allowances, events, Solidity implementation, Remix deployment, Sepolia, and MetaMask",
            "pdf_pages": _pages(516, 527),
        },
        CH15_ECONOMICS: {
            "chapter": "Chapter 15",
            "section": "Tokenomics, cryptoeconomics, token engineering, and token taxonomy",
            "pdf_pages": _pages(528, 529),
        },
    }


def _target(
    concept: str,
    subconcept: str,
    principle: str,
    source_ref: str,
    *required_points: str,
    forbidden: Sequence[str] = (),
) -> Level6Target:
    source = level6_source_map()[source_ref]
    return Level6Target(
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


def level6_targets() -> tuple[Level6Target, ...]:
    return (
        _target("tokenization_foundations", "token_and_tokenization", "In the blockchain context, a token digitally represents something of value and is generated, protected, and transferred through cryptographic protocols; tokenization converts ownership rights in an asset into a cryptographic or digital token on a blockchain.", CH15_FOUNDATIONS, "A blockchain token is a digital representation of value.", "Tokenization maps asset ownership rights into a blockchain token."),
        _target("tokenization_foundations", "asset_representation", "Blockchain tokenization can represent assets such as commodities, real estate, art ownership, currency, and other things of value, turning ownership claims into transferable digital representations on a blockchain.", CH15_FOUNDATIONS, "Tokenization is not limited to cryptocurrency-native assets."),
        _target("tokenization_benefits", "speed_flexibility_cost", "The source attributes faster processing, cross-border flexibility, and lower costs to digitized blockchain workflows that can reduce clearing, settlement, counterparty delays, and operational friction.", CH15_FOUNDATIONS, "Explain processing, cross-border, and cost advantages as source claims rather than universal guarantees."),
        _target("tokenization_benefits", "fractional_ownership_liquidity", "Tokenization can divide ownership of otherwise indivisible or illiquid real-world assets into fractions and make those fractions easier to trade, potentially increasing accessibility and liquidity.", CH15_FOUNDATIONS, "Fractional ownership and liquidity are related but distinct benefits.", forbidden=("Do not claim every tokenized asset is automatically liquid in every market.",)),
        _target("tokenization_benefits", "security_transparency_trust", "Tokens inherit cryptographic and blockchain security and transparency properties when implemented correctly, enabling auditable activity and supporting investor trust; poor implementation can still introduce exploitable vulnerabilities.", CH15_FOUNDATIONS, "Security depends on correct implementation.", forbidden=("Do not claim tokenization is immune to hacks merely because it uses cryptography.",)),
        _target("tokenization_risks", "regulation_and_legality", "Tokenization raises regulatory and legal questions because decentralized systems can make accountability difficult; security tokens may be treated as securities and inherit established legal and regulatory obligations, while legality differs across jurisdictions.", CH15_FOUNDATIONS, "Regulation and legal status are jurisdiction-dependent concerns."),
        _target("tokenization_risks", "technology_and_application_security", "A secure underlying blockchain does not guarantee a secure tokenization application: technical barriers, difficult interfaces, poor development practices, smart-contract limitations, and application-layer vulnerabilities can still cause user harm or financial loss.", CH15_FOUNDATIONS, "Separate base-chain security from DApp/token-contract security."),
        _target("token_types", "coin_vs_token", "The source calls a coin the native token or default cryptocurrency of its own blockchain, such as bitcoin or ether, while a token can represent an asset or application-specific value and run on top of an existing smart-contract blockchain.", CH15_TYPES, "Native coin and application token are not identical categories."),
        _target("token_types", "fungible_tokens", "Fungible tokens of the same type are indistinguishable, interchangeable, and divisible into smaller fractions, so one unit can substitute for another unit of the same value and type.", CH15_TYPES, "Indistinguishability, interchangeability, and divisibility define the source's fungible-token model."),
        _target("token_types", "non_fungible_tokens", "NFTs are unique and non-interchangeable representations of specific assets or attributes; the source also describes them as indivisible complete units in its treatment of non-fungibility.", CH15_TYPES, "Uniqueness and non-interchangeability distinguish NFTs from fungible tokens."),
        _target("token_types", "stable_tokens", "Stable tokens or stablecoins seek to maintain a stable value relative to a reference asset such as fiat currency or precious metal, addressing the volatility that limits ordinary cryptocurrencies for everyday use.", CH15_TYPES, "A stable token is defined by a peg or stabilization objective."),
        _target("token_types", "stablecoin_models", "The source classifies stablecoins as fiat-collateralized, commodity-collateralized, crypto-collateralized, or algorithmically stabilized; these models differ in what backs or controls the peg.", CH15_TYPES, "Keep collateralized and algorithmic stabilization mechanisms distinct."),
        _target("token_types", "security_tokens", "Security tokens derive value from external tradable assets such as company shares and place those securities on a blockchain; because they are securities, traditional legal and regulatory requirements still apply.", CH15_TYPES, "A blockchain representation does not remove the underlying security's regulatory character."),
        _target("tokenization_process", "asset_to_token_lifecycle", "The source's generic tokenization process onboards an investor, scrutinizes and verifies asset ownership, initiates the security-token process, places the physical asset with a custodian, creates a derivative token representing the asset, issues it on-chain, and allows secondary-market trading and settlement.", CH15_PROCESS_OFFERINGS, "Ownership verification and custody precede issuance in the source's generic process.", "The token represents the underlying asset rather than physically becoming the asset."),
        _target("token_offerings", "offering_purpose", "Token offerings use blockchain-hosted tokens to facilitate fundraising or financial activity such as crowdfunding and trading securities; the mechanism and regulatory posture differ by offering type.", CH15_PROCESS_OFFERINGS, "Offerings are fundraising/financial-distribution mechanisms rather than token standards."),
        _target("token_offerings", "ico_vs_ipo", "An ICO raises capital through blockchain-based token issuance, often from start-up projects and cryptocurrency contributions, whereas an IPO distributes company shares through traditional regulated markets and underwriters; the source emphasizes different maturity, regulation, and return structures.", CH15_PROCESS_OFFERINGS, "ICO and IPO are both capital-raising mechanisms but use different instruments and market structures."),
        _target("token_offerings", "security_token_offering", "An STO offers tokenized securities that represent financial assets and are treated as securities, allowing established securities regulation to apply more directly than in the largely unregulated ICO model described by the source.", CH15_PROCESS_OFFERINGS, "STO tokens are classified as securities."),
        _target("token_offerings", "initial_exchange_offering", "An IEO distributes tokens through an exchange rather than directly through an ICO-style crowdfunding wallet flow; exchange involvement and due diligence can add transparency and credibility.", CH15_PROCESS_OFFERINGS, "The exchange is the key distribution intermediary in an IEO."),
        _target("token_offerings", "equity_token_offering", "An ETO represents company equity or shares as tokens; the source treats it as a narrower security-token case focused specifically on company ownership rather than any possible security asset.", CH15_PROCESS_OFFERINGS, "ETO scope is company equity, narrower than the broader STO category."),
        _target("token_offerings", "daico", "A DAICO combines DAO-style governance with ICO fundraising so investors retain more control over the investment process, aiming for a more automated, decentralized, and controlled form of token fundraising.", CH15_PROCESS_OFFERINGS, "DAICO combines DAO governance concepts with ICO mechanics."),
        _target("token_standards", "why_standardize", "Without token standards, each smart contract could implement transfers and balances differently, creating interoperability and usability problems; standardized interfaces make tokens easier for wallets, exchanges, and applications to integrate.", CH15_STANDARDS, "Standardization addresses interoperability and usability."),
        _target("token_standards", "erc20", "ERC-20 is the widely adopted Ethereum standard for fungible tokens and defines a common interface that wallets and applications can support consistently.", CH15_STANDARDS, "ERC-20 standardizes fungible-token behavior.", forbidden=("Do not classify ERC-20 as an NFT standard.",)),
        _target("token_standards", "erc223_and_erc777", "ERC-223 and ERC-777 were proposed to improve limitations of ERC-20; the source describes ERC-223 as a fungible-token alternative with lower gas use and ERC-777 as backward compatible with ERC-20 while adding advanced interaction features such as hooks.", CH15_STANDARDS, "ERC-223 and ERC-777 are fungible-token standards intended to improve ERC-20 behavior."),
        _target("token_standards", "erc721", "ERC-721 is an NFT standard whose required rules govern management and trading of unique non-fungible tokens, made prominent by CryptoKitties.", CH15_STANDARDS, "ERC-721 is for non-fungible tokens."),
        _target("token_standards", "erc1400_and_erc1404", "ERC-1400 and its related standards address issuance, management, documentation, control, and processing of security tokens, while ERC-1404 adds transfer-restriction mechanisms that can enforce conditions such as whitelists or timing restrictions.", CH15_STANDARDS, "Security-token standards can encode regulatory transfer controls."),
        _target("token_standards", "erc1155", "ERC-1155 is a multi-token standard that can represent fungible and non-fungible token types through one interface and can batch transactions for efficiency.", CH15_STANDARDS, "ERC-1155 can handle multiple fungible and NFT types in one contract interface."),
        _target("token_standards", "erc4626", "ERC-4626 standardizes tokenized yield-bearing vault interactions such as deposits, withdrawals, balance-related operations, and other parameters to improve interoperability and composability across vault protocols.", CH15_STANDARDS, "ERC-4626 is a tokenized-vault interface standard."),
        _target("erc20_implementation", "required_functions", "The ERC-20 interface described by the source requires totalSupply, balanceOf, transfer, transferFrom, approve, and allowance so callers can inspect supply/balances, transfer tokens, and authorize delegated spending.", CH15_ERC20, "Name the six required functions and their roles."),
        _target("erc20_implementation", "metadata_and_events", "The source describes name, symbol, and decimals as optional ERC-20 metadata functions, while Transfer and Approval are required events used to record transfers and successful approvals in logs.", CH15_ERC20, "Distinguish optional metadata functions from required events."),
        _target("erc20_implementation", "balances_supply_allowance", "The example ERC-20 contract uses one mapping for account balances and a nested mapping for owner-to-spender allowances, stores token metadata and total supply as state, and initializes the creator with the supply while emitting a Transfer from the zero address.", CH15_ERC20, "Balances and allowances are different state relationships.", "Constructor initialization assigns the example supply to the creator."),
        _target("erc20_implementation", "transfer_approve_transferfrom", "transfer moves the caller's tokens after checking balance, approve records how much a spender may use on the owner's behalf, and transferFrom checks both balance and allowance before moving tokens and decrementing the authorized allowance.", CH15_ERC20, "Delegated transfer requires allowance in addition to available balance."),
        _target("erc20_implementation", "test_deploy_wallet_lifecycle", "The source builds and compiles an ERC-20 token in Remix, tests it first in a local JavaScript VM, deploys it to the Sepolia test network through MetaMask, then imports the token into MetaMask so balances and transfers can be exercised through a wallet interface.", CH15_ERC20, "Local testing precedes public testnet deployment.", forbidden=("Do not describe mainnet deployment as the first testing step.",)),
        _target("token_economics", "tokenomics_vs_cryptoeconomics", "Tokenomics studies economic activity, models, and impacts within tokenization ecosystems, including issuance, sale, purchase, investment, goods, assets, and participating entities; the source treats cryptoeconomics as a broader superset combining economics, game theory, cryptography, and wider blockchain protocols and cryptocurrencies.", CH15_ECONOMICS, "Tokenomics is narrower than cryptoeconomics in the source's taxonomy."),
        _target("token_economics", "token_engineering_and_taxonomy", "Token engineering applies engineering rigor, systems thinking, and mathematical foundations to tokenization and blockchain design, while token taxonomy seeks a reusable classification of token types and attributes; ERC development standards should not be confused with a universal token taxonomy.", CH15_ECONOMICS, "Token engineering is a design discipline; token taxonomy is a classification problem.", "ERC standards are implementation interfaces, not a universal token classification system."),
    )


ORDINARY_COUNT = len(level6_targets()) * ORDINARY_VARIANTS_PER_TARGET
TOTAL_COUNT = ORDINARY_COUNT + INTEGRITY_COUNT + 1


def _label(target: Level6Target) -> str:
    return f"{target.concept.replace('_', ' ')} / {target.subconcept.replace('_', ' ')}"


def build_level6_bank(curriculum_id: str = CURRICULUM_ID) -> tuple[Exercise, ...]:
    exercises: list[Exercise] = []
    sequence = 1
    targets = level6_targets()

    for target in targets:
        for template in QUESTION_TEMPLATES:
            exercises.append(
                Exercise(
                    exercise_id=f"MB4E-L06-{sequence:05d}",
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
            f"Integrity check: State the source-supported rule for {_label(target)} and reject any claim that changes the token type, standard, offering, or economic mechanism described by the book."
            if index % 2 == 0
            else f"Integrity check: An analyst makes an overconfident claim about {_label(target)}. Give the precise source-grounded correction without inventing supply, market, regulatory, or token-design evidence."
        )
        exercises.append(
            Exercise(
                exercise_id=f"MB4E-L06-{sequence:05d}",
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

    exercises.append(
        Exercise(
            exercise_id=f"MB4E-L06-{sequence:05d}",
            curriculum_id=curriculum_id,
            level=LEVEL,
            concept="tokenomics",
            subconcept="boss_synthesis",
            question=(
                "Boss: Design and explain a source-grounded tokenization system from the decision to represent an asset on-chain through token type, issuance process, offering model, Ethereum standard, ERC-20-style implementation boundaries, wallet/testnet deployment, and economic design. "
                "Distinguish coins from tokens, fungibility from NFTs, stable/security-token mechanisms, standards from taxonomy, tokenomics from cryptoeconomics, and engineering choices from unsupported market assumptions."
            ),
            expected_answer=(
                "Start by defining the asset and ownership rights being represented, then evaluate tokenization benefits and risks including fractional ownership, liquidity, regulation, legality, application security, and user barriers. "
                "Choose the token class according to the asset and behavior: native coins belong to their own blockchain; fungible tokens are interchangeable/divisible; NFTs are unique/non-interchangeable; stable tokens seek a peg through collateral or algorithmic mechanisms; security tokens represent regulated external financial assets. "
                "For real-world asset tokenization, verify ownership, establish custody where required, create the derivative token, issue it on-chain, and support secondary trading/settlement. Select an offering structure such as ICO, STO, IEO, ETO, or DAICO according to what is being distributed and the governance/regulatory model. "
                "Use a standard to provide interoperable contract behavior: ERC-20 for fungible tokens, ERC-721 for NFTs, ERC-1155 for multi-token contracts, security-token standards for controlled securities, or ERC-4626 for tokenized vault interfaces. "
                "An ERC-20-style implementation exposes supply, balance, transfer, delegated-transfer, approval, and allowance functions plus Transfer and Approval events; test locally before testnet deployment and use a wallet such as MetaMask for user-facing token operations. "
                "Finally, analyze tokenomics as the economic activity and model of the token ecosystem while recognizing that cryptoeconomics is broader; apply token engineering rigor and distinguish implementation standards from a universal token taxonomy."
            ),
            source_refs=(SOURCE_KEY, *level6_source_map().keys()),
            question_type="boss",
            difficulty=3,
            required_reasoning_points=(
                "Explain asset representation, tokenization benefits, and implementation/regulatory risks.",
                "Correctly distinguish coin, fungible token, NFT, stable token, and security token.",
                "Explain tokenization and offering lifecycles without conflating offering types with standards.",
                "Choose token standards according to their source-supported roles and explain core ERC-20 mechanics.",
                "Distinguish tokenomics, cryptoeconomics, token engineering, and token taxonomy.",
            ),
            forbidden_inferences=(
                "Do not claim tokenization guarantees liquidity or investment returns.",
                "Do not treat ERC standards as a universal economic taxonomy.",
                "Do not classify every token as a security or stablecoin without source-supported criteria.",
                "Do not invent token supply schedules, prices, yields, or market-cap assumptions absent from the source.",
            ),
            grading_rubric_id=RUBRIC_ID,
            boss_question=True,
        )
    )

    if len(exercises) != TOTAL_COUNT:
        raise AssertionError(f"total Level-6 bank count drifted: {len(exercises)}")
    if sum(item.integrity_question for item in exercises) != INTEGRITY_COUNT:
        raise AssertionError("Level-6 integrity count drifted")
    if sum(item.boss_question for item in exercises) != 1:
        raise AssertionError("Level-6 Boss count drifted")
    if len({item.exercise_id for item in exercises}) != TOTAL_COUNT:
        raise AssertionError("Level-6 exercise IDs are not unique")
    return tuple(exercises)


def level6_provenance_records(
    exercises: Sequence[Exercise], *, source_key: str = SOURCE_KEY
) -> tuple[dict[str, object], ...]:
    if source_key != SOURCE_KEY:
        raise ValueError(f"Level-6 provenance source_key must be canonical {SOURCE_KEY!r}")
    targets = {(item.concept, item.subconcept): item for item in level6_targets()}
    source_map = level6_source_map()
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
                raise AssertionError(f"Level-6 provenance target mismatch: {exercise.exercise_id}")
        records.append(
            {
                "exercise_id": exercise.exercise_id,
                "source_key": SOURCE_KEY,
                "supports": ["question", "expected_answer", "required_reasoning_points"],
                "locations": locations,
            }
        )
    return tuple(records)
