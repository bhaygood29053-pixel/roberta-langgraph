# Roberta LangGraph — X1 Scout Integration

This task extends the proven DeepSeek-backed Roberta loop with the first
chain-specialist boundary.

```text
User
  -> Roberta (Oracle / Coordinator)
    -> x1_scout_investigate
      -> X1 Scout LangGraph subgraph
        -> CMIS contract
          -> Mock CMIS (TEST_ONLY in this task)
      <- structured X1 Scout report
    <- ToolMessage
  <- Roberta synthesis
```

## What this proves

- Roberta delegates an X1 investigation to X1 Scout.
- Roberta does **not** receive a direct CMIS/market-report tool.
- X1 Scout scopes its CMIS call explicitly to `chain="x1"`.
- CMIS returns structured deterministic facts.
- X1 Scout returns a structured specialist report to Roberta.
- Roberta can synthesize the report while preserving TEST_ONLY uncertainty.

The X1 Scout graph is deliberately deterministic in this milestone. Agentic
Scout planning and real CMIS/provider access come after the boundary is proven.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev,deepseek]'
```

## Deterministic tests

```bash
python -m pytest -v -m 'not live'
```

Expected coverage includes:

- direct Roberta answer without specialist
- Roberta -> X1 Scout -> Roberta loop
- X1 Scout -> CMIS chain scoping and report contract
- registry boundary proving CMIS is not exposed to Roberta

## Live DeepSeek smoke test

Set the key in your shell (do not commit it):

```bash
export DEEPSEEK_API_KEY='...'
```

Then:

```bash
roberta-live "On X1, check AGI market risk"
```

The expected tool selected by Roberta is:

```text
x1_scout_investigate
```

The returned specialist report is still TEST_ONLY because Task 4 uses a mock
CMIS adapter.

Run the paid opt-in integration test with:

```bash
RUN_LIVE_MODEL_TESTS=1 python -m pytest -v -m live
```

See `docs/X1_SCOUT_BOUNDARY.md` for the architecture boundary.
