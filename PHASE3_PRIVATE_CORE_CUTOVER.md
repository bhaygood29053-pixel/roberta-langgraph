# Phase 3 — ROBERTA Private-Core Cutover

Status: **IN PROGRESS**

Public runtime entrypoints now depend on `roberta.private_core`, which targets the private facade contract `roberta-private-core/v1`.

The following user-facing paths have been redirected away from direct protected `roberta.graph` imports:

- HTTP bridge;
- chat CLI;
- live demo;
- readiness CLI;
- package-level `build_graph` export.

## Migration-only fallback

Until split validation is complete, `roberta.private_core` may call the current public graph implementation so the source repository remains testable.

That fallback is temporary.

Production cutover requires:

`ROBERTA_PRIVATE_CORE_REQUIRED=1`

With that flag enabled, an absent or incompatible private core fails closed.

## Removal gate

Do not delete protected orchestration, learning, memory, policy, prompt, specialist, or reasoning implementation from public HEAD until:

1. the private distribution builds and passes its doctor;
2. bridge/chat/live/readiness tests pass through `roberta-private-core/v1`;
3. ROBERTA -> Chain Scout -> CMIS end-to-end tests pass across the split;
4. required-private-core mode runs without the public fallback;
5. public package/test surfaces no longer depend on protected implementation being present locally.

Historical Git cleanup is separate and happens only after functional cutover.
