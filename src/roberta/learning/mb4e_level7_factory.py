from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .pyramid import Exercise


CURRICULUM_ID = "mastering_blockchain_4e_2023_book01"
SOURCE_KEY = "mastering_blockchain_4e_2023"
LEVEL = 7
RUBRIC_ID = "MB4E-L7-RUBRIC-V1"
ORDINARY_VARIANTS_PER_TARGET = 13
INTEGRITY_COUNT = 50


@dataclass(frozen=True, slots=True)
class Level7Target:
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
    "Explain the source-supported liquidity rule for {label}.",
    "What does the book establish about {label}?",
    "Give a precise technical explanation of {label}.",
    "A learner is confused about {label}. What should Roberta explain?",
    "State the key liquidity mechanism involved in {label}.",
    "How should {label} be described without adding unsupported assumptions?",
    "What source-supported point must an answer about {label} include?",
    "Correct a vague explanation of {label} using the book's liquidity model.",
    "What would a correct operational summary of {label} say?",
    "Apply the book's explanation of {label} to a generic liquidity-pool scenario.",
    "What distinction is essential when reasoning about {label}?",
    "If auditing an answer about {label}, what core liquidity point must be present?",
    "What conclusion about {label} follows from the source material?",
)


def _pages(start: int, end: int) -> tuple[int, ...]:
    return tuple(range(start, end + 1))


CH21_AMM_FOUNDATIONS = "MB4E-CH21-P728-730-DEX-AMM-LIQUIDITY"
CH21_AMM_MODELS = "MB4E-CH21-P730-731-CFMM-MODELS"
CH21_LIQUIDITY_RISKS = "MB4E-CH21-P732-733-LIQUIDITY-RISKS-INNOVATIONS"
CH21_UNISWAP = "MB4E-CH21-P741-746-UNISWAP-LIQUIDITY-POOL"


def level7_source_map() -> dict[str, dict[str, object]]:
    return {
        CH21_AMM_FOUNDATIONS: {
            "chapter": "Chapter 21",
            "section": "DEX architecture, AMMs, liquidity pools, liquidity providers, fees, CPMM, depth, and slippage",
            "pdf_pages": _pages(728, 730),
        },
        CH21_AMM_MODELS: {
            "chapter": "Chapter 21",
            "section": "CPMM, CSMM, and CMMM reserve relationships and liquidity tradeoffs",
            "pdf_pages": _pages(730, 731),
        },
        CH21_LIQUIDITY_RISKS: {
            "chapter": "Chapter 21",
            "section": "DEX aggregation, impermanent loss, capital efficiency, dynamic/hybrid/virtual/proactive AMMs, and front running",
            "pdf_pages": _pages(732, 733),
        },
        CH21_UNISWAP: {
            "chapter": "Chapter 21",
            "section": "Uniswap AMM operation, token swaps, pool creation, fee tier, price range, liquidity management, and fee claims",
            "pdf_pages": _pages(741, 746),
        },
    }


def _target(
    concept: str,
    subconcept: str,
    principle: str,
    source_ref: str,
    *required_points: str,
    forbidden: Sequence[str] = (),
) -> Level7Target:
    source = level7_source_map()[source_ref]
    return Level7Target(
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


def level7_targets() -> tuple[Level7Target, ...]:
    return (
        _target("liquidity_foundations", "dex_non_custodial_exchange", "A DEX operates on a blockchain and enables token exchange without a central intermediary or centralized custodian; the source describes DEXs as decentralized, transparent, and non-custodial.", CH21_AMM_FOUNDATIONS, "A DEX removes the centralized exchange/custody intermediary from the trading path."),
        _target("liquidity_foundations", "dex_contract_functions", "The source describes the basic DEX smart-contract structure as supporting price discovery, trade matching, and trade clearing; liquidity mechanisms provide the assets and pricing behavior needed for those functions in an AMM.", CH21_AMM_FOUNDATIONS, "Price discovery, matching, and clearing are distinct exchange functions."),
        _target("amm", "liquidity_pool_market_making", "An AMM is a liquidity-pool-based DEX mechanism in which a smart contract automates market making instead of relying on users to place matching orders manually.", CH21_AMM_FOUNDATIONS, "A smart contract and liquidity pool replace manual order matching in the AMM model."),
        _target("amm", "liquidity_provider_role", "Liquidity providers deposit tokens into shared liquidity pools so traders can swap against pooled reserves; the pool supplies tradable inventory rather than requiring a simultaneous counterparty for each trade.", CH21_AMM_FOUNDATIONS, "LPs supply pool reserves used by traders."),
        _target("amm", "fees_and_liquidity_mining", "Traders using a liquidity pool pay fees, and liquidity providers earn pool fees in return for locking funds; the source calls the process of locking funds to earn pool-related rewards liquidity mining.", CH21_AMM_FOUNDATIONS, "Trading fees compensate liquidity providers in the source's AMM model."),
        _target("amm", "instant_liquidity", "AMMs can provide instant liquidity because buyers and sellers trade against pooled reserves rather than waiting for another trader to place a qualifying order.", CH21_AMM_FOUNDATIONS, "Pool reserves can satisfy trades even when there is no simultaneous opposite-side trader.", forbidden=("Do not claim an AMM guarantees zero slippage or infinite capacity for every trade size.",)),
        _target("cpmm", "constant_product_invariant", "In a constant product market maker, reserves x and y are related by x*y=k during swaps; changing one reserve changes the other and therefore changes the implied exchange price while the swap invariant is maintained.", CH21_AMM_MODELS, "Explain x*y=k as a reserve relationship during trading.", "Reserve changes move the implied price."),
        _target("cpmm", "reserve_ratio_price", "The source explains that the ratio of the two pool reserves determines price behavior: buying one asset reduces its pool quantity and changes the reserve relationship so its relative price rises while the other side adjusts.", CH21_AMM_MODELS, "Price emerges from reserve quantities and their mathematical relationship."),
        _target("cpmm", "liquidity_continuity", "The constant product formula is designed to preserve tradability across the curve, providing continuing liquidity as reserve quantities and prices adjust rather than exhausting one side at an ordinary finite price point.", CH21_AMM_MODELS, "CPMM liquidity is continuous across its curve, but trade quality still depends on pool depth."),
        _target("liquidity_depth", "slippage_definition", "Slippage is the difference between the current market price of an asset and the price at which an order is actually filled.", CH21_AMM_FOUNDATIONS, "Slippage compares expected/current market price with execution price."),
        _target("liquidity_depth", "depth_trade_size_slippage", "The source states that deeper liquidity and smaller trade sizes reduce slippage; large trades against shallow pools move the AMM curve more and therefore experience greater price impact.", CH21_AMM_FOUNDATIONS, "Deeper pools reduce price impact for a given trade size.", "Smaller trades generally produce less slippage than larger trades against the same pool."),
        _target("liquidity_depth", "slippage_not_eliminated", "In CPMMs, slippage can be minimized through deep liquidity and smaller trade sizes but is not completely avoidable; it must be anticipated and managed.", CH21_AMM_FOUNDATIONS, "Reduced slippage is not the same as zero slippage.", forbidden=("Do not claim deep liquidity eliminates CPMM slippage entirely.",)),
        _target("amm_models", "csmm", "A constant sum market maker uses x+y=k; the source notes that this simple relationship can protect against slippage but does not provide unlimited liquidity.", CH21_AMM_MODELS, "CSMM trades off stronger price stability/slippage protection against limited liquidity."),
        _target("amm_models", "cmmm", "A constant mean market maker extends AMMs to more than two assets and permits non-50/50 weightings by preserving a weighted geometric mean of reserves, enabling variable exposure and swaps among multiple pool assets.", CH21_AMM_MODELS, "CMMM supports multiple assets and configurable weights."),
        _target("amm_models", "model_tradeoffs", "CPMM, CSMM, and CMMM use different mathematical reserve relationships, so their liquidity, price-impact, asset-count, and weighting behavior differ; no single formula should be assumed to have all advantages of the others.", CH21_AMM_MODELS, "Keep constant-product, constant-sum, and constant-mean models distinct."),
        _target("liquidity_risk", "impermanent_loss", "Impermanent loss arises when the relative value of assets deposited in a liquidity pool changes, causing the value of the withdrawn pool position to differ from the value associated with the original deposit; the source warns that the term impermanent can be misleading because realized losses can become permanent at withdrawal.", CH21_LIQUIDITY_RISKS, "Relative asset-price changes create LP value divergence.", "Withdrawal can realize the loss."),
        _target("liquidity_risk", "capital_efficiency", "AMMs may require large amounts of deposited liquidity to achieve price impact comparable with an order-book exchange, which the source identifies as low capital efficiency.", CH21_LIQUIDITY_RISKS, "Capital efficiency concerns how much deposited liquidity is needed to support useful trading depth."),
        _target("liquidity_risk", "impermanent_loss_vs_slippage", "Impermanent loss is primarily an LP-position risk caused by relative asset-price changes, whereas slippage is a trader execution-price effect caused by movement along the pool curve; they are different consequences of AMM liquidity mechanics.", CH21_LIQUIDITY_RISKS, "Separate LP inventory/value risk from trader execution-price impact."),
        _target("amm_innovation", "dynamic_amm", "A dynamic AMM can use oracle price feeds, volatility, and other variables to reposition liquidity along the price curve, concentrating liquidity near market price in calmer conditions and adapting the curve as conditions change.", CH21_LIQUIDITY_RISKS, "DAMMs dynamically adjust liquidity distribution using market inputs."),
        _target("amm_innovation", "hybrid_cfmm", "Hybrid constant function market makers combine properties, functions, or parameters from multiple AMM designs to pursue more stable, efficient, or profitable trading behavior.", CH21_LIQUIDITY_RISKS, "Hybrid CFMMs combine model properties rather than using one pure invariant design."),
        _target("amm_innovation", "virtual_amm", "Virtual AMMs use a constant-product-style relationship without relying on a conventional underlying liquidity pool; traders instead post collateral to a smart contract and trade synthetic exposure, aiming to reduce price impact and impermanent-loss problems.", CH21_LIQUIDITY_RISKS, "A vAMM's synthetic/collateral model differs from a conventional reserve pool."),
        _target("amm_innovation", "proactive_market_maker", "A proactive market maker uses oracle market prices to move its price curve toward current market conditions and place more liquidity near the market price, seeking greater liquidity efficiency and lower impermanent loss.", CH21_LIQUIDITY_RISKS, "PMMs use oracle-informed curve movement and liquidity concentration."),
        _target("liquidity_risk", "front_running_sandwich", "Public AMM transactions can be exploited through front-running or sandwich behavior in which an attacker trades around a victim transaction to profit from induced price movement; the source connects this behavior with MEV.", CH21_LIQUIDITY_RISKS, "Public transaction ordering creates an AMM exploitation surface.", forbidden=("Do not claim formula-based AMMs eliminate front-running risk.",)),
        _target("liquidity_risk", "amm_pros_cons", "The source highlights AMM simplicity and the absence of a maintained order book as advantages, while impermanent loss, slippage, capital inefficiency, front-running, and technology/security risks remain material limitations.", CH21_LIQUIDITY_RISKS, "AMM automation does not remove liquidity or execution risks."),
        _target("uniswap_liquidity", "uniswap_amm_role", "Uniswap uses an AMM to determine asset prices and enable instant token trading without an order book; users can deposit assets into liquidity pools and receive a portion of trading fees.", CH21_UNISWAP, "Uniswap combines AMM pricing, pooled liquidity, and LP fee participation."),
        _target("uniswap_liquidity", "swap_transaction", "A Uniswap swap selects the token pair and is confirmed through the connected wallet; the swap is a blockchain transaction that must be processed before the resulting asset balance is finalized.", CH21_UNISWAP, "A swap requires wallet confirmation and on-chain processing."),
        _target("uniswap_liquidity", "pool_parameters", "The source's Uniswap pool-creation workflow selects a token pair, fee tier, and price range before previewing and confirming the liquidity position.", CH21_UNISWAP, "Pair, fee tier, and price range are explicit liquidity-position parameters."),
        _target("uniswap_liquidity", "position_management", "After a Uniswap liquidity position is mined, the provider can inspect liquidity, unclaimed fees, and price range, add more liquidity, remove liquidity, close the position, and claim earned fees.", CH21_UNISWAP, "Liquidity positions have an ongoing management lifecycle rather than being a one-time deposit."),
    )


ORDINARY_COUNT = len(level7_targets()) * ORDINARY_VARIANTS_PER_TARGET
TOTAL_COUNT = ORDINARY_COUNT + INTEGRITY_COUNT + 1


def _label(target: Level7Target) -> str:
    return f"{target.concept.replace('_', ' ')} / {target.subconcept.replace('_', ' ')}"


def build_level7_bank(curriculum_id: str = CURRICULUM_ID) -> tuple[Exercise, ...]:
    exercises: list[Exercise] = []
    sequence = 1
    targets = level7_targets()

    for target in targets:
        for template in QUESTION_TEMPLATES:
            exercises.append(
                Exercise(
                    exercise_id=f"MB4E-L07-{sequence:05d}",
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
            f"Integrity check: State the source-supported liquidity rule for {_label(target)} and reject any claim that changes the pool, reserve, pricing, fee, or execution mechanism described by the book."
            if index % 2 == 0
            else f"Integrity check: An analyst makes an overconfident liquidity claim about {_label(target)}. Give the precise source-grounded correction without inventing reserves, depth, returns, or live market evidence."
        )
        exercises.append(
            Exercise(
                exercise_id=f"MB4E-L07-{sequence:05d}",
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
            exercise_id=f"MB4E-L07-{sequence:05d}",
            curriculum_id=curriculum_id,
            level=LEVEL,
            concept="liquidity",
            subconcept="boss_synthesis",
            question=(
                "Boss: Explain an end-to-end source-grounded AMM liquidity system from liquidity-provider deposits and trader swaps through reserve-based pricing, fees, slippage, impermanent loss, capital efficiency, AMM design variants, front-running exposure, and practical Uniswap position management. Distinguish trader execution risk from LP position risk and do not invent live prices, APYs, reserves, or protocol behavior beyond the source."
            ),
            expected_answer=(
                "Liquidity providers deposit token reserves into a shared pool and traders swap against those reserves, paying fees that compensate providers. In an AMM the smart contract performs market making; under a CPMM, x*y=k links reserve changes to price changes and gives continuing tradability across the curve. Deeper liquidity and smaller trades reduce price impact and slippage, but CPMM slippage is not eliminated. CSMM and CMMM use different reserve relationships and therefore different liquidity tradeoffs. LPs face impermanent loss when relative asset prices move and the pool position diverges in value, while traders primarily experience execution-price slippage; AMMs can also be capital inefficient because large reserves may be needed for deep liquidity. Dynamic, hybrid, virtual, and proactive market makers alter liquidity distribution or pricing behavior to improve efficiency or mitigate specific limitations. Public transaction ordering creates front-running and sandwich/MEV risk. In the source's Uniswap workflow, users select a pair, fee tier, and price range, confirm the on-chain position, then monitor liquidity and unclaimed fees and may increase or remove liquidity and claim fees."
            ),
            source_refs=(SOURCE_KEY, *level7_source_map().keys()),
            question_type="boss",
            difficulty=3,
            required_reasoning_points=(
                "Explain LP deposits, pooled reserves, swaps, and fee compensation.",
                "Explain CPMM reserve-price mechanics and the depth/trade-size relationship to slippage.",
                "Distinguish impermanent loss, slippage, and capital efficiency.",
                "Compare core and newer AMM model approaches without collapsing them together.",
                "Explain public-ordering/front-running risk and the Uniswap liquidity-position lifecycle.",
            ),
            forbidden_inferences=(
                "Do not invent live pool reserves, prices, yields, fee APRs, or token performance.",
                "Do not claim deep liquidity eliminates slippage completely.",
                "Do not equate impermanent loss with trader slippage.",
                "Do not claim AMMs eliminate front-running or other execution-order risks.",
            ),
            grading_rubric_id=RUBRIC_ID,
            boss_question=True,
        )
    )

    if len(exercises) != TOTAL_COUNT:
        raise AssertionError(f"total Level-7 bank count drifted: {len(exercises)}")
    if sum(item.integrity_question for item in exercises) != INTEGRITY_COUNT:
        raise AssertionError("Level-7 integrity count drifted")
    if sum(item.boss_question for item in exercises) != 1:
        raise AssertionError("Level-7 Boss count drifted")
    if len({item.exercise_id for item in exercises}) != TOTAL_COUNT:
        raise AssertionError("Level-7 exercise IDs are not unique")
    return tuple(exercises)


def level7_provenance_records(
    exercises: Sequence[Exercise], *, source_key: str = SOURCE_KEY
) -> tuple[dict[str, object], ...]:
    if source_key != SOURCE_KEY:
        raise ValueError(f"Level-7 provenance source_key must be canonical {SOURCE_KEY!r}")
    targets = {(item.concept, item.subconcept): item for item in level7_targets()}
    source_map = level7_source_map()
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
                raise AssertionError(f"Level-7 provenance target mismatch: {exercise.exercise_id}")
        records.append(
            {
                "exercise_id": exercise.exercise_id,
                "source_key": SOURCE_KEY,
                "supports": ["question", "expected_answer", "required_reasoning_points"],
                "locations": locations,
            }
        )
    return tuple(records)
