# X1 Scout Integration Boundary

Task 4 proves the first chain-specialist boundary without connecting to live
market infrastructure.

## Authority flow

```text
Roberta
  -> X1 Scout
    -> CMIS
      -> X1 Provider (future live implementation)
```

Roberta sees only the `x1_scout_investigate` capability. CMIS operations are
not registered as Roberta tools.

## Verified-data flow

```text
Mock CMIS (Task 4)
  -> X1 Scout structured report
    -> Roberta ToolMessage
      -> Roberta final synthesis
```

The mock CMIS returns `TEST_ONLY` data with null market fields. This verifies
that uncertainty and service ownership survive the full graph path without
inventing market values.

## Deliberately deferred

- Real CMIS transport/API integration
- X1 Provider / X1 RPC / XDEX calls
- Agentic X1 Scout planning across multiple CMIS operations
- Persistence/checkpointing
- HMPX permanent memory
- Human approval gates
