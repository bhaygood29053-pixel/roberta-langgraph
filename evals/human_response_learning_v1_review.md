# Human Response Learning v1 — Representative Manual Review

These are **synthetic evaluation fixtures**, not current blockchain or market facts. The corpus teaches response structure, evidence discipline, uncertainty handling, and continuity behavior only.

Corpus size: **100 scenarios** across **12 families**.

## token_assessment

Scenario: `token-01-x1x`

User:

> Give me a current assessment of X1X.
>
Reference ROBERTA response:

> I wouldn't trade X1X right now.
> 
> The biggest reason is that only about $13 of liquidity is verified. measured 24h activity is zero.
> 
> On the other side, freeze authority is disabled.
> 
> I'm still uncertain because market freshness is not fully verified.
> 
> What would change my mind: deeper verified liquidity. Analysis only — no trade execution.

Expected evaluator focus:

- recommendation: AVOID
- primary driver: only about $13 of liquidity is verified
- uncertainty required: true
- counterevidence required: true
- change-my-mind required: true
- continuity required: false
- live-market authority: false
- execution authorized: false

## risk_evidence

Scenario: `risk-01-high-strong`

User:

> How risky is THETA?
>
Reference ROBERTA response:

> I would avoid THETA.
> 
> The biggest reason is that the risk evidence is strong and points to a serious market weakness. risk is high while evidence quality is strong.
> 
> On the other side, a verified control reduces one narrow concern.
> 
> I'm still uncertain because higher risk is not the same thing as weak evidence.
> 
> What would change my mind: materially improved risk evidence. Analysis only — no trade execution.

Expected evaluator focus:

- recommendation: AVOID
- primary driver: the risk evidence is strong and points to a serious market weakness
- uncertainty required: true
- counterevidence required: true
- change-my-mind required: true
- continuity required: false
- live-market authority: false
- execution authorized: false

## pretrade

Scenario: `pretrade-01-agi-buy-500`

User:

> Should I buy $500 of AGI?
>
Reference ROBERTA response:

> I wouldn't make this $500 AGI buy.
> 
> The biggest reason is that the trade is too large relative to verified liquidity. the requested buy is $500.
> 
> On the other side, a smaller order would reduce the sizing problem.
> 
> I'm still uncertain because current execution conditions still need fresh evidence.
> 
> What would change my mind: a much smaller trade or deeper liquidity. Analysis only — no trade execution.

Expected evaluator focus:

- recommendation: AVOID
- primary driver: the trade is too large relative to verified liquidity
- uncertainty required: true
- counterevidence required: true
- change-my-mind required: true
- continuity required: false
- live-market authority: false
- execution authorized: false

## comparison

Scenario: `compare-01-xnt-agi`

User:

> Which looks safer to trade: XNT or AGI?
>
Reference ROBERTA response:

> I'd favor XNT over AGI for this trade.
> 
> The biggest reason is that XNT has materially deeper verified liquidity. AGI has thinner activity.
> 
> On the other side, AGI has some positive tokenomics evidence.
> 
> I'm still uncertain because freshness is not equally strong on both sides.
> 
> What would change my mind: AGI reaching comparable verified depth. Analysis only — no trade execution.

Expected evaluator focus:

- recommendation: WATCH
- primary driver: XNT has materially deeper verified liquidity
- uncertainty required: true
- counterevidence required: true
- change-my-mind required: true
- continuity required: false
- live-market authority: false
- execution authorized: false

## large_trade_price_impact

Scenario: `large-trade-01-agi`

User:

> Did that big AGI wallet cause the price spike?
>
Reference ROBERTA response:

> I can say the observed AGI swap moved the verified pool, but I can't prove it moved the whole market.
> 
> The biggest reason is that the swap mechanically changed the verified pool price by about 8.4%. the wallet and transaction time are verified within the accepted provider scope.
> 
> On the other side, the broader market may have had other trades or venues.
> 
> I'm still uncertain because whole-market causality is not verified.
> 
> What would change my mind: broader independently verified venue coverage. Analysis only — no trade execution.

Expected evaluator focus:

- recommendation: WATCH
- primary driver: the swap mechanically changed the verified pool price by about 8.4%
- uncertainty required: true
- counterevidence required: true
- change-my-mind required: true
- continuity required: false
- live-market authority: false
- execution authorized: false

## history_what_changed

Scenario: `history-01-agi`

User:

> What changed with AGI since the prior observation?
>
Reference ROBERTA response:

> I can verify a historical change for AGI, but I won't treat the older snapshot as current by itself.
> 
> The biggest reason is that verified liquidity fell by about 18% across the bounded comparison window. the earlier observation remains historical evidence.
> 
> On the other side, the current market may have changed again.
> 
> I'm still uncertain because the latest state still requires fresh verification.
> 
> What would change my mind: a fresh current snapshot tied to the same exact asset. Analysis only — no trade execution.

Expected evaluator focus:

- recommendation: WATCH
- primary driver: verified liquidity fell by about 18% across the bounded comparison window
- uncertainty required: true
- counterevidence required: true
- change-my-mind required: true
- continuity required: false
- live-market authority: false
- execution authorized: false

## bridge_cross_chain

Scenario: `bridge-01-usdcx-flow`

User:

> What does the bridge data say about USDC.X?
>
Reference ROBERTA response:

> I'd treat the USDC.X evidence as bounded cross-chain intelligence, not a broader adoption claim.
> 
> The biggest reason is that bridge activity increased on the verified route. that is route utilization, not proof of adoption.
> 
> On the other side, the route evidence still tells us something useful about movement.
> 
> I'm still uncertain because coverage outside the verified route is not established.
> 
> What would change my mind: broader verified route and market coverage. Analysis only — no trade execution.

Expected evaluator focus:

- recommendation: WATCH
- primary driver: bridge activity increased on the verified route
- uncertainty required: true
- counterevidence required: true
- change-my-mind required: true
- continuity required: false
- live-market authority: false
- execution authorized: false

## concentration

Scenario: `concentration-01-agi`

User:

> Should I worry about AGI holder concentration?
>
Reference ROBERTA response:

> I'd be cautious with AGI because concentration is high.
> 
> The biggest reason is that the verified top-holder concentration is about 72% within the accepted scope. that is a concentration measurement, not a real-world identity label.
> 
> On the other side, some concentrated holdings may belong to contracts or infrastructure.
> 
> I'm still uncertain because holder intent and real-world ownership are not verified.
> 
> What would change my mind: a sustained reduction in verified concentration. Analysis only — no trade execution.

Expected evaluator focus:

- recommendation: WAIT
- primary driver: the verified top-holder concentration is about 72% within the accepted scope
- uncertainty required: true
- counterevidence required: true
- change-my-mind required: true
- continuity required: false
- live-market authority: false
- execution authorized: false

## burn

Scenario: `burn-01-agi`

User:

> What can you verify about the AGI burn?
>
Reference ROBERTA response:

> I can verify the AGI burn event in this fixture, but I wouldn't claim it caused the market price to move.
> 
> The biggest reason is that the verified burn amount is 100,000 AGI. the burn transaction is distinct from any later price action.
> 
> On the other side, a real burn can still matter to supply mechanics.
> 
> I'm still uncertain because price causality is not established.
> 
> What would change my mind: independent evidence linking a bounded market response to the event. Analysis only — no trade execution.

Expected evaluator focus:

- recommendation: WATCH
- primary driver: the verified burn amount is 100,000 AGI
- uncertainty required: true
- counterevidence required: true
- change-my-mind required: true
- continuity required: false
- live-market authority: false
- execution authorized: false

## regulatory

Scenario: `regulatory-01-genius-usdcx`

User:

> What does the GENIUS Act evidence mean for USDC.X?
>
Reference ROBERTA response:

> I can explain what the regulatory evidence says about USDC.X, but I can't label it compliant or non-compliant.
> 
> The biggest reason is that the GENIUS Act framework is relevant to payment-stablecoin analysis. that does not establish legal compliance for this exact bridged representation.
> 
> On the other side, the verified framework evidence is still useful context.
> 
> I'm still uncertain because this is evidence analysis, not legal advice.
> 
> What would change my mind: updated primary-law or regulator evidence tied to the exact asset. Analysis only — no trade execution.

Expected evaluator focus:

- recommendation: not applicable
- primary driver: the GENIUS Act framework is relevant to payment-stablecoin analysis
- uncertainty required: true
- counterevidence required: true
- change-my-mind required: true
- continuity required: false
- live-market authority: false
- execution authorized: false

## data_quality

Scenario: `data-quality-01-stale`

User:

> What do you think about AGI right now?
>
Reference ROBERTA response:

> I don't have enough verified evidence to make a strong AGI call yet.
> 
> The biggest reason is that the live market snapshot is stale. stale evidence cannot be called current.
> 
> On the other side, some useful partial evidence is available.
> 
> I'm still uncertain because the evidence limitation is material.
> 
> What would change my mind: fresh, independently verified evidence for the missing point. Analysis only — no trade execution.

Expected evaluator focus:

- recommendation: INSUFFICIENT_EVIDENCE
- primary driver: the live market snapshot is stale
- uncertainty required: true
- counterevidence required: true
- change-my-mind required: true
- continuity required: false
- live-market authority: false
- execution authorized: false

## followup_continuity

Scenario: `followup-01-why`

User:

> Should I buy $500 of AGI?
>
> Why?
>
Reference ROBERTA response:

> I'd still explain my earlier caution the same way: the prior verified liquidity was thin.
> 
> The biggest reason is that the earlier judgment was driven by thin verified liquidity. that earlier snapshot is historical context, not newly verified current data.
> 
> On the other side, the smaller positives from the prior answer still matter.
> 
> I'm still uncertain because I have not re-verified the market in this follow-up.
> 
> What would change my mind: new current evidence showing materially deeper liquidity. Analysis only — no trade execution.

Expected evaluator focus:

- recommendation: WAIT
- primary driver: the earlier judgment was driven by thin verified liquidity
- uncertainty required: true
- counterevidence required: true
- change-my-mind required: true
- continuity required: true
- live-market authority: false
- execution authorized: false

