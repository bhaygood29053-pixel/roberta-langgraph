from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .pyramid import Exercise


CURRICULUM_ID = "mastering_blockchain_4e_2023_book01"
SOURCE_KEY = "mastering_blockchain_4e_2023"
LEVEL = 8
RUBRIC_ID = "MB4E-L8-RUBRIC-V1"
ORDINARY_VARIANTS_PER_TARGET = 13
INTEGRITY_COUNT = 50


@dataclass(frozen=True, slots=True)
class Level8Target:
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
    "Explain the source-supported market-structure rule for {label}.",
    "What does the book establish about {label}?",
    "Give a precise technical explanation of {label}.",
    "A learner is confused about {label}. What should Roberta explain?",
    "State the key market-structure mechanism involved in {label}.",
    "How should {label} be described without adding unsupported assumptions?",
    "What source-supported point must an answer about {label} include?",
    "Correct a vague explanation of {label} using the book's market model.",
    "What would a correct operational summary of {label} say?",
    "Apply the book's explanation of {label} to a generic trading or exchange scenario.",
    "What distinction is essential when reasoning about {label}?",
    "If auditing an answer about {label}, what core market-structure point must be present?",
    "What conclusion about {label} follows from the source material?",
)


def _pages(start: int, end: int) -> tuple[int, ...]:
    return tuple(range(start, end + 1))


CH21_MARKETS = "MB4E-CH21-P713-715-FINANCIAL-MARKETS-TRADING-EXCHANGES"
CH21_ORDERS = "MB4E-CH21-P715-717-ORDERS-ROUTING-TRADE"
CH21_LIFECYCLE = "MB4E-CH21-P717-719-TRADE-LIFECYCLE-SETTLEMENT"
CH21_DEX = "MB4E-CH21-P728-731-DEX-PRICE-DISCOVERY-CLOB-AMM"
CH21_AGGREGATORS = "MB4E-CH21-P732-734-AGGREGATORS-CEX-DEX"


def level8_source_map() -> dict[str, dict[str, object]]:
    return {
        CH21_MARKETS: {
            "chapter": "Chapter 21",
            "section": "Financial markets, market classes, trading, exchanges, electronic order books, and order properties",
            "pdf_pages": _pages(713, 715),
        },
        CH21_ORDERS: {
            "chapter": "Chapter 21",
            "section": "Bid and offer prices, market/limit/stop orders, order routing, order books, trade tickets, and counterparties",
            "pdf_pages": _pages(715, 717),
        },
        CH21_LIFECYCLE: {
            "chapter": "Chapter 21",
            "section": "Trade lifecycle, order anticipation, market manipulation, execution, clearing, and settlement",
            "pdf_pages": _pages(717, 719),
        },
        CH21_DEX: {
            "chapter": "Chapter 21",
            "section": "CEX/DEX structure, DEX smart-contract functions, price discovery, AMM, CLOB order-book DEXs, and execution models",
            "pdf_pages": _pages(728, 731),
        },
        CH21_AGGREGATORS: {
            "chapter": "Chapter 21",
            "section": "DEX aggregators, on-chain/off-chain routing tradeoffs, DEX limitations, and CEX-versus-DEX comparison",
            "pdf_pages": _pages(732, 734),
        },
    }


def _target(
    concept: str,
    subconcept: str,
    principle: str,
    source_ref: str,
    *required_points: str,
    forbidden: Sequence[str] = (),
) -> Level8Target:
    source = level8_source_map()[source_ref]
    return Level8Target(
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


def level8_targets() -> tuple[Level8Target, ...]:
    return (
        _target("financial_markets", "market_definition_and_price", "A financial market is a venue or system in which financial instruments are traded between buyers and sellers; the source states that asset prices are determined by supply and demand and reflect market participants' expectations.", CH21_MARKETS, "A market is a trading venue/system.", "Supply and demand are central to price formation."),
        _target("financial_markets", "market_classes", "The source groups financial markets broadly into money markets, credit markets, and capital markets: money markets cover short-term lending and foreign exchange, credit markets center on borrowing and lending, and capital markets facilitate trading in instruments such as stocks and bonds.", CH21_MARKETS, "Keep money, credit, and capital market roles distinct."),
        _target("financial_markets", "primary_secondary_markets", "Capital markets include primary markets, where companies issue securities directly to investors, and secondary markets, where investors resell securities to other investors through exchanges.", CH21_MARKETS, "Primary issuance and secondary resale are different market functions."),
        _target("trading", "positions_and_venues", "Trading involves buying or selling financial instruments to pursue profit or hedge risk; the source distinguishes long positions from short positions and notes that trades may occur through brokers, exchanges, or OTC directly between counterparties.", CH21_MARKETS, "Long and short positions describe opposite exposure directions.", "Exchange, brokered, and OTC routes are distinct execution venues."),
        _target("exchange_structure", "exchange_role", "A traditional exchange is a centralized intermediary and regulated marketplace that brings buyers and sellers together, publishes market information, executes trades under defined rules, and facilitates settlement.", CH21_MARKETS, "Exchanges intermediate standardized trading and settlement."),
        _target("exchange_structure", "electronic_order_book", "Modern electronic exchanges receive orders into a central electronic order book and distribute orders, prices, and related market attributes electronically, creating a virtual marketplace.", CH21_MARKETS, "The central electronic order book organizes and publishes trading interest."),
        _target("orders", "order_attributes", "An order is an instruction to trade and generally specifies the instrument, quantity, direction such as buy or sell, and an order type that encodes conditions such as limit or stop behavior.", CH21_MARKETS, "Instrument, quantity, direction, and order type are core order attributes."),
        _target("orders", "bid_offer", "The bid price is the price at which a trader is willing to buy, while the offer price is the price at which a trader is willing to sell; these quotes express trading intent on opposite sides of the market.", CH21_ORDERS, "Bid is buy-side interest; offer is sell-side interest."),
        _target("orders", "market_order", "A market order instructs the trading system to execute at the best price currently available and is intended for immediate execution at prevailing spot prices.", CH21_ORDERS, "Market orders prioritize immediate execution over a specified limit price."),
        _target("orders", "limit_order", "A limit order constrains execution to a specified price or better; unlike an unconditional market order, it does not authorize execution outside the trader's limit condition.", CH21_ORDERS, "A limit price constrains acceptable execution.", forbidden=("Do not claim a limit order guarantees immediate execution.",)),
        _target("orders", "stop_order", "The source distinguishes a stop order from a visible limit order: the stop order becomes active as a market order only when its specified stop price is reached.", CH21_MARKETS, "A stop order is conditionally activated by the stop price.", forbidden=("Do not describe a stop order as identical to an always-visible limit order.",)),
        _target("orders", "routing_systems", "Order routing systems deliver orders to destinations according to business logic, allowing customers, brokers, dealers, clearing houses, and exchanges to participate in the execution path.", CH21_ORDERS, "Routing determines where an order is delivered for processing or execution."),
        _target("orders", "order_book_purpose", "An order book is the exchange-maintained list of trading intentions; it organizes buy and sell orders and supports matching based on prices and applicable rules.", CH21_ORDERS, "The order book records and organizes buy/sell interest."),
        _target("trade_structure", "trade_ticket", "A trade ticket collects the details needed to describe a trade, including instrument identification, status and timestamps, economics such as buy/sell value, price and quantity, and other attributes that vary with the instrument and asset class.", CH21_ORDERS, "Trade tickets bind identification and economic details of the executed trade."),
        _target("trade_structure", "counterparty", "The counterparty is the other party to a trade and is essential for settlement; related details can include identity, address, payment type, reference identifiers, settlement date, and delivery type.", CH21_ORDERS, "Counterparty information supports successful settlement."),
        _target("trade_lifecycle", "lifecycle_stages", "The source's general trade lifecycle proceeds through pre-execution order placement, execution and booking, confirmation, post-booking verification, settlement, and end-of-day processing such as reporting, profit-and-loss, and risk calculations.", CH21_LIFECYCLE, "Keep order placement, execution, confirmation, verification, settlement, and end-of-day processing distinct."),
        _target("trade_lifecycle", "execution_clearing_settlement", "The source distinguishes execution, clearing, and settlement: execution creates the trading commitment, clearing matches seller and buyer details such as price and quantity and identifies payment accounts, and settlement exchanges the security for payment and finalizes the trade.", CH21_LIFECYCLE, "Execution, clearing, and settlement are sequential but distinct functions."),
        _target("market_abuse", "order_anticipation", "Order anticipation is an attempt to profit before other traders by predicting how their activity will affect prices; the source lists frontrunners, sentiment-oriented technical traders, and squeezers as examples of order anticipators.", CH21_LIFECYCLE, "Order anticipation exploits knowledge or prediction of other trading activity."),
        _target("market_abuse", "manipulation", "Market manipulation uses deceptive or artificial trading activity or false information to move prices or create misleading market conditions for improper profit; the source treats such conduct as illegal financial crime.", CH21_LIFECYCLE, "Artificial activity and false information can distort price formation.", forbidden=("Do not present manipulation as legitimate price discovery.",)),
        _target("dex_structure", "cex_vs_dex_intermediation", "A centralized exchange acts as an intermediary and custodian, while a DEX operates on a blockchain and enables peer-to-peer token exchange without a central authority or centralized custodian; the source characterizes DEXs as decentralized, transparent, and non-custodial.", CH21_DEX, "Custody and intermediary structure distinguish CEX and DEX models."),
        _target("dex_structure", "dex_core_functions", "The source describes a DEX smart contract as providing three core exchange functions: price discovery, trade matching, and trade clearing.", CH21_DEX, "Price discovery, matching, and clearing are separate exchange functions."),
        _target("dex_structure", "price_discovery", "Price discovery determines a tradable market value through supply and demand and establishes the price at which buyers and sellers are willing to transact; the source notes that exchanges, OTC activity, derivatives, economic data, geopolitical events, and sentiment can influence this process.", CH21_DEX, "Price discovery is the process of forming market-clearing prices from market forces and information."),
        _target("dex_structure", "dex_models", "The source distinguishes liquidity-pool AMMs, order-book-based DEXs, and DEX aggregators as different decentralized exchange structures, each using a different mechanism to obtain liquidity, prices, or execution.", CH21_DEX, "AMM, CLOB, and aggregator models should not be collapsed into one mechanism."),
        _target("dex_structure", "amm_vs_clob", "An AMM automates market making against liquidity pools using smart-contract formulas, whereas a central limit order book matches explicit buy and sell orders according to predetermined rules and organized price levels.", CH21_DEX, "Pool-based pricing and order-book matching are different market structures."),
        _target("order_book_dex", "clob_matching", "An order-book DEX uses the traditional CLOB model: traders submit buy and sell orders, the book organizes them by price, and matching occurs according to predetermined rules when supply and demand permit execution.", CH21_DEX, "CLOB execution depends on submitted orders and matching rules."),
        _target("order_book_dex", "liquidity_and_execution", "The source describes order-book exchanges as suitable for highly liquid markets because they can determine market prices and handle large orders with relatively low slippage, offering capital-efficient and transparent execution.", CH21_DEX, "High liquidity supports efficient CLOB price discovery and larger-order execution.", forbidden=("Do not claim order books inherently guarantee deep liquidity in every market.",)),
        _target("dex_aggregation", "aggregator_role", "A DEX aggregator combines access to liquidity across exchanges and seeks routes with attributes such as deeper liquidity, better prices, lower fees, and lower slippage instead of requiring the user to inspect each DEX individually.", CH21_AGGREGATORS, "Aggregation is an execution-routing and venue-selection layer."),
        _target("dex_aggregation", "onchain_offchain_tradeoffs", "The source distinguishes off-chain aggregators, which can span many chains and optimize flexibly but introduce trusted-third-party and bias/front-running risks, from on-chain aggregators, which encode routing logic in smart contracts and reduce centralized bias but face scalability and venue-coverage limits.", CH21_AGGREGATORS, "Off-chain flexibility comes with trust tradeoffs; on-chain transparency comes with scaling constraints."),
        _target("market_structure", "cex_dex_comparison", "The source compares CEX and DEX structures across custody, entry barriers, regulation, infrastructure, user experience, liquidity, impermanent-loss exposure, fees, and identity verification; these dimensions show that decentralization changes multiple market-design tradeoffs rather than simply removing one intermediary.", CH21_AGGREGATORS, "Compare CEX and DEX across several structural dimensions rather than a single good/bad label."),
    )


ORDINARY_COUNT = len(level8_targets()) * ORDINARY_VARIANTS_PER_TARGET
TOTAL_COUNT = ORDINARY_COUNT + INTEGRITY_COUNT + 1


def _label(target: Level8Target) -> str:
    return f"{target.concept.replace('_', ' ')} / {target.subconcept.replace('_', ' ')}"


def build_level8_bank(curriculum_id: str = CURRICULUM_ID) -> tuple[Exercise, ...]:
    exercises: list[Exercise] = []
    sequence = 1
    targets = level8_targets()

    for target in targets:
        for template in QUESTION_TEMPLATES:
            exercises.append(
                Exercise(
                    exercise_id=f"MB4E-L08-{sequence:05d}",
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
            f"Integrity check: State the source-supported market-structure rule for {_label(target)} and reject any claim that changes the venue, order, matching, routing, clearing, settlement, or custody mechanism described by the book."
            if index % 2 == 0
            else f"Integrity check: An analyst makes an overconfident market-structure claim about {_label(target)}. Give the precise source-grounded correction without inventing order-book depth, live prices, routes, counterparties, or current venue behavior."
        )
        exercises.append(
            Exercise(
                exercise_id=f"MB4E-L08-{sequence:05d}",
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
            exercise_id=f"MB4E-L08-{sequence:05d}",
            curriculum_id=curriculum_id,
            level=LEVEL,
            concept="market_structure",
            subconcept="boss_synthesis",
            question=(
                "Boss: Explain an end-to-end source-grounded market structure from financial-market venues and order instructions through bid/offer formation, market/limit/stop behavior, routing, order-book matching, trade booking, clearing and settlement, then compare that structure with blockchain DEX mechanisms including AMMs, CLOB DEXs, aggregators, and CEX-versus-DEX custody and execution tradeoffs. Identify market-abuse risks without inventing live order books, prices, routes, or current venue behavior."
            ),
            expected_answer=(
                "Financial markets are venues or systems where instruments trade and prices form through supply and demand. Traditional exchanges centralize intermediation and commonly organize electronic orders in a central order book. Orders identify the instrument, quantity, direction, and order type; bids express buy interest and offers express sell interest. Market orders seek immediate execution at the best available price, limit orders constrain acceptable price, and stop orders activate when a trigger price is reached. Routing systems deliver orders to brokers, dealers, clearing houses, or exchanges. A CLOB organizes buy and sell orders by price and matches them under rules; after execution, the trade proceeds through confirmation, clearing and verification, and settlement, where assets and payment are exchanged. Order anticipation and manipulation can distort fair price formation. A DEX removes the centralized exchange/custodian role and uses smart contracts for price discovery, trade matching, and clearing. AMMs use pools and formulas rather than explicit opposite-side orders, while order-book DEXs preserve CLOB-style matching. Aggregators route across venues to seek favorable liquidity, price, fees, and slippage; off-chain and on-chain aggregation have different trust and scalability tradeoffs. CEX and DEX structures differ across custody, regulation, access, liquidity, fees, identity requirements, and other operational dimensions."
            ),
            source_refs=(SOURCE_KEY, *level8_source_map().keys()),
            question_type="boss",
            difficulty=3,
            required_reasoning_points=(
                "Explain financial-market venues, price formation, and primary exchange/order-book structure.",
                "Explain bid/offer, market/limit/stop orders, routing, and CLOB matching.",
                "Explain the trade lifecycle with distinct execution, clearing, and settlement functions.",
                "Explain market-abuse risks such as order anticipation and manipulation.",
                "Compare CEX, AMM DEX, order-book DEX, and aggregator structures without inventing live market state.",
            ),
            forbidden_inferences=(
                "Do not invent current order-book depth, prices, spreads, routes, counterparties, or venue status.",
                "Do not claim limit orders guarantee immediate execution.",
                "Do not collapse execution, clearing, and settlement into the same function.",
                "Do not treat AMM pools and CLOB order books as the same market-making mechanism.",
            ),
            grading_rubric_id=RUBRIC_ID,
            boss_question=True,
        )
    )

    if len(exercises) != TOTAL_COUNT:
        raise AssertionError(f"total Level-8 bank count drifted: {len(exercises)}")
    if sum(item.integrity_question for item in exercises) != INTEGRITY_COUNT:
        raise AssertionError("Level-8 integrity count drifted")
    if sum(item.boss_question for item in exercises) != 1:
        raise AssertionError("Level-8 Boss count drifted")
    if len({item.exercise_id for item in exercises}) != TOTAL_COUNT:
        raise AssertionError("Level-8 exercise IDs are not unique")
    return tuple(exercises)


def level8_provenance_records(
    exercises: Sequence[Exercise], *, source_key: str = SOURCE_KEY
) -> tuple[dict[str, object], ...]:
    if source_key != SOURCE_KEY:
        raise ValueError(f"Level-8 provenance source_key must be canonical {SOURCE_KEY!r}")
    targets = {(item.concept, item.subconcept): item for item in level8_targets()}
    source_map = level8_source_map()
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
                raise AssertionError(f"Level-8 provenance target mismatch: {exercise.exercise_id}")
        records.append(
            {
                "exercise_id": exercise.exercise_id,
                "source_key": SOURCE_KEY,
                "supports": ["question", "expected_answer", "required_reasoning_points"],
                "locations": locations,
            }
        )
    return tuple(records)
