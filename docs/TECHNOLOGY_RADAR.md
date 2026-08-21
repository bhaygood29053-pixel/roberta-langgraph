# Roberta Technology Radar — Design Specification

Status: **design/specification only — no runtime implementation authorized**

Tracking: Issue #100 under parent Issue #97.

This document specifies a future read-only Technology Radar specialist/service for Roberta. It defines the intended discovery, provenance, identity, evaluation, historical-trend, recommendation, and adoption boundaries without creating a Radar runtime, source adapter, scheduler, dependency, provider, autonomous agent, or execution capability.

The specification is governed by [`ENGINEERING_WORKFLOW.md`](./ENGINEERING_WORKFLOW.md), remains consistent with [`DURABLE_MEMORY.md`](./DURABLE_MEMORY.md), and does not modify the authority boundaries in [`LANGGRAPH_ROADMAP.md`](./LANGGRAPH_ROADMAP.md).

## 1. Purpose

The future Technology Radar may help Roberta discover software, AI, blockchain, security, testing, memory, deployment, provider, and developer-workflow technology that could materially improve Roberta, Chain Scouts, or CMIS.

The Radar is intended to reduce manual discovery while preventing trend-following from becoming roadmap drift, provider trust, production adoption, or new execution authority.

The Radar is a **research and recommendation capability**, not an implementation authority.

## 2. Non-goals of this specification

Issue #100 does not authorize or add:

- a production Radar service;
- a Radar specialist registered in the Roberta runtime;
- a GitHub, Hacker News, Product Hunt, RSS, search, or other live source adapter;
- background polling, cron, scheduling, or notifications;
- new Python packages or dependency changes;
- automated repository cloning or package installation;
- automated code changes;
- automated architecture changes;
- automated roadmap mutation;
- automated issue or pull-request creation;
- automated merges;
- CMIS provider-trust changes;
- a second market/blockchain evidence authority;
- transaction preparation, signing, broadcasting, custody, trading, bridge transfer, or autonomous value movement;
- any start or widening of Roberta Phase 11 Controlled Execution.

A future implementation requires a separate accepted roadmap gate and implementation issue after this design is accepted.

## 3. Authority model

The Technology Radar sits beside, not inside, the market/blockchain truth path.

Current market/blockchain authority remains:

```text
User / transport
  -> Roberta
    -> Chain Scout
      -> CMIS
        -> Chain Provider / verified source
```

The future technology-research path is conceptually separate:

```text
Approved public technology sources
  -> Radar source adapters
  -> candidate identity / deduplication
  -> provenance capture
  -> basic research verification
  -> multi-dimensional evaluation
  -> roadmap-aware recommendation
  -> Roberta research brief
  -> human / roadmap decision
```

Radar observations are **technology-research evidence only**. They do not become:

- CMIS market facts;
- CMIS Evidence Receipts;
- CMIS Proof Scores;
- deterministic market risk;
- chain capability truth;
- provider trust status;
- wallet/asset facts;
- execution authority.

The Radar may discuss whether a technology appears relevant to a CMIS or Roberta roadmap problem, but it may not modify CMIS facts, trust relationships, capabilities, risk, or proof.

## 4. Read-only pipeline

A future implementation should preserve this pipeline:

```text
approved public sources
  -> candidate collection
  -> canonical project identity / deduplication
  -> provenance capture
  -> basic verification
  -> multi-dimensional evaluation
  -> roadmap-aware category
  -> Roberta recommendation
```

Each stage must preserve explicit unknown, partial, ambiguous, stale, or conflicting states. Missing research evidence must not be converted into a positive score, a false certainty, or an LLM guess.

No pipeline stage may install, execute, import, benchmark, or modify a discovered project merely because it was observed.

## 5. Replaceable source adapters

The design permits multiple approved public source adapters. Initial candidates may include:

- GitHub discovery/trending/search surfaces;
- Hacker News;
- Product Hunt;
- other future explicitly approved technology-discovery sources.

The Radar must not depend on one proprietary ranking backend or one source's popularity semantics.

A source adapter should conceptually emit a bounded source observation containing fields such as:

```text
source_name
source_kind
source_item_id
source_url
observed_at
source_rank_or_position        optional
source_attention_signals       optional / source-specific
project_name_claim             optional
project_url_claim              optional
repository_url_claim           optional
publisher_or_owner_claim       optional
short_source_description       optional
raw_license_claim              optional
retrieval_status
limitations
```

Source-specific ranking values remain source claims. A high rank on one service is not proof of quality, security, maintenance, adoption fitness, or roadmap relevance.

### 5.1 Source-adapter requirements

A future adapter must:

- identify its source explicitly;
- preserve source-native ids/URLs where available;
- timestamp the observation;
- preserve unavailable/partial fields as unavailable/partial;
- avoid treating marketing copy as verified technical capability;
- avoid silently substituting one source for another;
- remain replaceable without changing Radar category semantics.

A failed source read must degrade to unavailable source evidence rather than fabricate a candidate observation.

## 6. Canonical project identity and deduplication

The Radar must distinguish a technology **candidate** from the source item that mentioned it.

A future canonical candidate identity should prefer strong machine-readable identifiers, for example:

1. exact repository host + owner + repository identity;
2. exact canonical project URL controlled by the project/publisher;
3. exact package or registry coordinates when relevant and explicitly linked to the project;
4. source-native project identity linked to one of the above;
5. a bounded unresolved identity when deterministic matching is not possible.

### 6.1 Identity rules

The Radar must not merge two projects merely because they share:

- a similar name;
- a token or package symbol;
- a description;
- overlapping keywords;
- the same category;
- an LLM similarity judgment.

Cross-source observations may be deduplicated into one candidate only when identity evidence is sufficiently strong for the intended research purpose.

When identity is ambiguous, the result remains separate or explicitly `identity_status = unresolved` rather than forcing a merge.

Renames, repository transfers, forks, mirrors, package aliases, and successor projects should retain provenance linking the old and new observations without assuming they are equivalent unless the relationship is verified.

## 7. Provenance capture

Every candidate brief should preserve how the candidate was discovered and what evidence supports each research claim.

At minimum, provenance should include, where available:

- first observed timestamp;
- last observed timestamp;
- contributing source names;
- source-native ids;
- source URLs;
- canonical project/repository URL;
- observation count;
- cross-source appearance count;
- identity confidence/status;
- verification notes;
- unresolved conflicts;
- known limitations.

A summarized claim should be traceable to its research source. The Radar may synthesize multiple sources for a research brief, but synthesis does not convert source claims into CMIS-style verified market facts.

## 8. Basic verification

Before recommending action above `WATCH`, the future Radar should perform bounded research verification appropriate to the candidate.

Examples may include:

- confirming the repository/project actually exists;
- confirming canonical owner/project identity;
- checking whether the project appears maintained;
- identifying release/activity recency where available;
- verifying the declared license from an appropriate primary project artifact where possible;
- distinguishing a primary project source from a secondary mention;
- checking whether the claimed capability is documented by the project rather than inferred from popularity text;
- recording conflicting or missing information explicitly.

This is **technology-research verification**, not CMIS evidence verification.

The Radar must not call a technology safe, secure, production-ready, trusted, or compatible merely because basic verification succeeds.

## 9. Evaluation dimensions remain separate

The Radar must not collapse all evaluation into one opaque score.

A candidate brief should expose at least these independent dimensions:

1. **Trend strength / external attention**
2. **Roadmap relevance**
3. **Evidence / source quality**
4. **Adoption / maintenance risk**
5. **License compatibility**

A future implementation may use deterministic or policy-guided subrules inside a dimension, but the dimensions remain separately visible and separately explainable.

Unknown inputs remain unknown.

## 10. Trend strength / external attention

Trend strength describes observed external attention only. It does not mean quality or suitability.

Suggested policy states:

```text
unknown
low
moderate
high
```

Trend evidence may include, when source semantics are known:

- repeated appearances over time;
- cross-source appearances;
- source-native rank or attention signals;
- growth or persistence of observable attention;
- release/activity events that plausibly explain attention.

A one-day spike should remain distinguishable from a sustained trend.

The Radar should preserve source-specific meaning rather than normalizing incomparable source signals into fake precision.

## 11. Roadmap relevance

Roadmap relevance answers: **does this candidate plausibly address an accepted Roberta/CMIS problem?**

Suggested states:

```text
none
future_or_backlog
adjacent
active
unknown
```

`active` requires a concrete accepted roadmap item, issue, readiness gap, provider gap, engineering problem, or approved research question that the candidate plausibly addresses.

The Radar may cite the relevant issue/document and explain the match. It may not create an `active` roadmap item by itself.

Popularity without an accepted problem match is not active roadmap relevance.

## 12. Evidence / source quality

Evidence quality describes the strength of the **technology research brief**, not CMIS Proof Score and not market truth.

Suggested states:

```text
insufficient
single_source
primary_source_supported
corroborated
conflicted
unknown
```

Examples:

- `single_source` — candidate exists only through one secondary discovery source;
- `primary_source_supported` — a canonical repository/project source supports key identity/capability claims;
- `corroborated` — multiple materially independent sources support the research claim;
- `conflicted` — relevant sources materially disagree;
- `insufficient` — the evidence cannot support the proposed recommendation.

These labels must never be called a CMIS Proof Score or reused as blockchain evidence quality.

## 13. Adoption / maintenance risk

Adoption risk is the project-level cost/risk of experimenting with or adopting the technology. It is not market risk and must remain separate from CMIS deterministic risk.

Suggested states:

```text
unknown
low
moderate
high
blocking
```

Possible considerations include:

- maintenance activity and release cadence;
- project maturity;
- dependency complexity;
- integration surface;
- security-sensitive privileges;
- operational burden;
- migration/reversal cost;
- bus-factor or abandonment signals;
- compatibility uncertainty;
- supply-chain/dependency exposure;
- whether evaluation requires privileged or production access.

A future implementation must document which observations support the risk state. Missing information remains `unknown` rather than assumed safe.

## 14. License compatibility

License compatibility remains its own dimension.

Suggested states:

```text
unknown
compatible_for_research
compatible_for_candidate_use
restricted
incompatible
requires_review
```

The Radar may identify an observed license and flag likely compatibility questions. It must not provide a binding legal conclusion unless a separately authorized legal-review process supplies one.

Missing or ambiguous licensing must remain explicit and can block movement into `EXPERIMENT` or `INVESTIGATE NOW` when the proposed use would depend on unresolved rights.

## 15. Roadmap-aware candidate categories

The Radar may recommend exactly one policy category while still exposing all evaluation dimensions separately.

Recommended categories:

- **INVESTIGATE NOW**
- **EXPERIMENT**
- **WATCH**
- **SKIP**

The category is a research/workflow recommendation, not permission to install, merge, deploy, or change production.

### 15.1 INVESTIGATE NOW

Meaning: the candidate plausibly addresses an active accepted roadmap problem and deserves a focused research issue/brief now.

Minimum expected evidence:

- resolved project identity;
- explicit active roadmap match;
- enough source quality to state the candidate's relevant capability without guessing;
- no known blocking license incompatibility for research;
- adoption risk identified, even if moderate/high;
- limitations and unknowns stated.

This category authorizes **research attention only**.

### 15.2 EXPERIMENT

Meaning: a bounded sandbox/prototype may be justified after a human/roadmap decision.

Expected conditions:

- candidate identity is resolved;
- relevant capability is supported by adequate research evidence;
- roadmap relevance is active or meaningfully adjacent;
- the proposed experiment can be isolated and reversible;
- license status permits the proposed experiment or has been explicitly cleared;
- risks/unknowns are bounded enough to design a safe experiment.

The Radar cannot start the experiment. An experiment requires a normal issue/spec and engineering gate.

### 15.3 WATCH

Meaning: retain the candidate as technology-research context without interrupting accepted work.

Typical reasons:

- potentially useful later but no active roadmap match;
- trend is early or volatile;
- evidence is not yet strong enough;
- maintenance/adoption risk is unresolved;
- license status is unresolved;
- the technology is promising but premature.

`WATCH` is not a negative judgment and does not imply future adoption.

### 15.4 SKIP

Meaning: no current research action is justified.

Typical reasons:

- no meaningful roadmap relevance;
- duplicate or superseded candidate;
- insufficient evidence after reasonable review;
- clearly incompatible use model;
- blocking maintenance/adoption risk;
- incompatible license for the intended use;
- capability does not materially improve the current system;
- the candidate would require prohibited authority expansion to be useful.

`SKIP` is a current recommendation, not a permanent blacklist. A materially changed candidate can be reevaluated from new evidence.

## 16. Category transition discipline

Categories must change because the underlying research evidence or roadmap context changed, not because an LLM preferred a different label.

Examples:

```text
WATCH -> INVESTIGATE NOW
  requires a newly accepted active roadmap match plus adequate evidence

WATCH -> EXPERIMENT
  requires a human/roadmap decision and a bounded experiment proposal

INVESTIGATE NOW -> EXPERIMENT
  requires research evidence sufficient to justify a reversible prototype

ANY -> SKIP
  may follow clear irrelevance, blocking risk, incompatible license, or failed identity/evidence

SKIP -> WATCH / INVESTIGATE NOW
  requires materially new evidence or roadmap context
```

The Radar does not rewrite the roadmap in order to justify its own category.

## 17. Candidate brief contract

A future Radar should produce a compact machine-readable object that can also be rendered as a human-readable Roberta research brief.

Conceptual schema:

```yaml
radar_candidate_version: "1"
candidate_id: "host:owner/project"
identity:
  status: resolved | unresolved
  name: "example"
  canonical_url: "..."
  repository_url: "..."        # optional
  aliases: []
observed:
  first_at: "..."
  last_at: "..."
  observation_count: 0
  cross_source_count: 0
sources:
  - source_name: "..."
    source_item_id: "..."
    source_url: "..."
    observed_at: "..."
summary:
  description: "..."
  why_it_may_matter: "..."
roadmap:
  relevance: active | adjacent | future_or_backlog | none | unknown
  references: []
  rationale: "..."
evaluation:
  trend_strength: unknown | low | moderate | high
  evidence_quality: insufficient | single_source | primary_source_supported | corroborated | conflicted | unknown
  adoption_risk: unknown | low | moderate | high | blocking
  license_compatibility: unknown | compatible_for_research | compatible_for_candidate_use | restricted | incompatible | requires_review
recommendation:
  category: INVESTIGATE_NOW | EXPERIMENT | WATCH | SKIP
  action: "..."
  rationale: "..."
limitations: []
unknowns: []
authority:
  research_only: true
  roadmap_mutation_authorized: false
  dependency_install_authorized: false
  code_change_authorized: false
  provider_trust_change_authorized: false
  execution_authorized: false
```

The exact implementation schema may evolve through a later issue, but it must preserve the semantic separation and authority fields above.

## 18. Human-readable brief

Roberta should present a candidate in an answer-first research format such as:

```text
Recommendation: WATCH
Candidate: <canonical project identity>
Why it matters: <roadmap-specific rationale>
Roadmap match: <active/adjacent/future/none/unknown + reference>
Trend: <state + concise evidence>
Evidence quality: <state + provenance>
Adoption risk: <state + key risks>
License: <state + observed license/unknown>
Limitations / unknowns: <explicit list>
Next allowed action: <research only / propose bounded experiment / no action>
```

The brief should not use popularity language as a substitute for technical evidence.

## 19. Historical trend intelligence

A future Radar may retain bounded historical observations so Roberta can distinguish a one-day spike from sustained attention.

Historical Radar data is **technology-research context**.

It must not become:

- CMIS market/blockchain history;
- HXMP current-truth authority;
- a replacement for fresh source observations;
- a new Proof Score or market risk system.

A future implementation should preserve observation history such as:

```text
candidate_id
source_name
source_item_id
observed_at
source_attention_signals
identity_status
trend_dimension_state
roadmap_relevance_at_observation
```

Historical analysis may identify patterns such as:

- first appearance;
- repeated appearance;
- sustained attention;
- declining attention;
- re-emergence after dormancy;
- source disagreement;
- project rename/transfer/fork history.

The latest Radar recommendation should be derived from current accepted research evidence plus explicit historical context. Historical context cannot manufacture missing current evidence.

## 20. Relationship to HXMP durable memory

Technology Radar history must not be dumped wholesale into HXMP.

HXMP remains governed by the durable-memory contract. If a human accepts a hard-to-reverse architecture or roadmap decision arising from Radar research, HXMP may retain only the compact durable decision context/reference already allowed by [`DURABLE_MEMORY.md`](./DURABLE_MEMORY.md).

Examples of potentially valid compact durable context after a separate accepted decision:

- decision key;
- short decision summary;
- issue/ADR/PR reference;
- bounded rationale.

Raw Radar observations, trending lists, full candidate histories, source pages, and long research briefs are not automatically durable-memory writes.

Radar history and HXMP serve different purposes and must not be conflated.

## 21. Adoption path for promising discoveries

A Radar recommendation cannot directly become production work.

The required path is:

```text
Radar candidate
  -> Roberta research brief
  -> human / roadmap decision
  -> research issue
  -> bounded prototype / experiment if justified
  -> recorded evidence / results
  -> architecture / roadmap decision
  -> normal implementation issue(s)
  -> behavior-first implementation
  -> exact-head verification
  -> three-axis review
  -> merge
  -> roadmap reconciliation
```

Each transition requires the normal authority owner. The Radar cannot skip steps because a candidate is highly ranked or trending.

## 22. Authority and safety invariants

The future Radar may:

- discover public technology candidates;
- read approved public sources;
- compare source observations;
- deduplicate when identity evidence supports it;
- summarize research evidence;
- classify under an approved Radar policy;
- recommend research;
- recommend that a human consider a bounded experiment;
- preserve technology-research history under an approved future storage design.

The Radar must not autonomously:

- install dependencies;
- execute discovered code;
- clone arbitrary repositories into trusted runtime paths;
- modify production code;
- modify CMIS or Scout logic;
- change architecture;
- add providers;
- change provider trust/verification status;
- change the roadmap;
- create or merge PRs as an adoption shortcut;
- weaken tests or readiness gates;
- widen Roberta/Scout/CMIS permissions;
- treat technology popularity as market/blockchain evidence;
- create CMIS facts, Evidence Receipts, Proof Scores, or deterministic market risk;
- create transaction/execution authority;
- prepare, sign, broadcast, custody, trade, bridge, or move value.

Every candidate result should preserve:

```text
research_only = true
roadmap_mutation_authorized = false
dependency_install_authorized = false
code_change_authorized = false
provider_trust_change_authorized = false
execution_authorized = false
```

## 23. Failure and degraded-evidence behavior

The future Radar must fail closed at research boundaries.

Examples:

- unresolved identity -> do not merge candidate histories;
- missing license -> `unknown` / `requires_review`, not compatible;
- unavailable source -> preserve unavailable source evidence;
- conflicting project ownership -> record conflict, do not guess canonical owner;
- stale observation -> preserve age and request refresh before strong recommendation;
- missing roadmap match -> not `INVESTIGATE NOW` merely because trend is high;
- missing maintenance evidence -> adoption risk remains unknown;
- one source claiming security/quality -> do not upgrade to verified safety;
- unavailable source rank -> no zero rank or synthetic score;
- LLM uncertainty -> explicit unknown, not fabricated precision.

## 24. Future implementation slices

Acceptance of this design does **not** authorize these slices. If a later roadmap gate approves implementation, prefer narrow independent issues such as:

1. candidate/result contract and deterministic policy types;
2. one approved source adapter as a tracer bullet;
3. canonical identity/deduplication behavior;
4. provenance capture;
5. roadmap-reference lookup boundary;
6. independent dimension evaluation policy;
7. historical observation store and trend persistence;
8. Roberta research-brief presentation;
9. bounded operator evaluation/readiness gate;
10. optional additional source adapters after the public seam is stable.

Do not build all adapters and storage layers before one bounded end-to-end research behavior is proved.

## 25. Acceptance checklist for Issue #100

The design is complete when reviewers can answer yes to all applicable statements:

```text
SPECIFICATION
[ ] A repository-authoritative Technology Radar design exists.
[ ] No production Radar implementation is included.
[ ] Replaceable source-adapter semantics are defined.
[ ] Canonical identity and fail-closed deduplication are defined.
[ ] Provenance and timestamps are required.
[ ] Trend, roadmap relevance, evidence quality, adoption risk, and license remain separate dimensions.
[ ] INVESTIGATE NOW / EXPERIMENT / WATCH / SKIP are defined.
[ ] Category movement depends on evidence/roadmap changes, not LLM preference.
[ ] Candidate brief contains provenance, rationale, limitations, unknowns, and authority flags.
[ ] Historical trend tracking is research context, not CMIS truth or HXMP authority.
[ ] Promising discoveries re-enter the normal engineering workflow.

AUTHORITY / SAFETY
[ ] Popularity is not treated as quality, trust, security, or roadmap relevance.
[ ] Radar cannot install dependencies or modify code automatically.
[ ] Radar cannot alter architecture or roadmap automatically.
[ ] Radar cannot change CMIS provider trust or verification state.
[ ] Radar cannot manufacture CMIS facts, risk, Evidence Receipts, or Proof Scores.
[ ] Controlled Execution remains locked.
[ ] No transaction preparation, signing, broadcasting, custody, trading, bridge transfer, or autonomous value movement is introduced.
```

## 26. Design rule

**The Radar may discover what deserves attention; it never decides by itself what Roberta or CMIS must adopt. Evidence stays attributable, dimensions stay separate, roadmap authority stays human/governed, and implementation must re-enter the normal engineering workflow.**
