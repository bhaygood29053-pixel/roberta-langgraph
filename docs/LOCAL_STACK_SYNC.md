# Local ROBERTA/CMIS stack synchronization

Use the canonical stack sync utility after accepted GitHub changes.

The utility updates:

- cmis
- cmis-core
- roberta-langgraph
- roberta-core

It then refreshes the local runtimes:

- reinstalls the current cmis-core private package into cmis/.venv;
- restarts cmis-gateway.service on 127.0.0.1:8765;
- rebuilds the assembled public/private ROBERTA runtime;
- restarts roberta-bridge.service on 127.0.0.1:8766;
- verifies both /healthz endpoints;
- verifies the live website served by 8766 contains the accepted Human Intelligence #381 UI.

## Run

From WSL:

    cd ~/roberta-dev/roberta-langgraph
    git fetch --prune origin
    git switch main
    git pull --ff-only origin main
    bash scripts/sync_local_stack.sh

If the repository root is not ~/roberta-dev, set:

    ROBERTA_STACK_ROOT=/absolute/path/to/stack bash scripts/sync_local_stack.sh

## Safety

The utility refuses to overwrite local changes.

If any of the four repositories has an uncommitted change, it stops and prints
that repository's status. Resolve or checkpoint those changes before rerunning.

Repository updates use only:

    git pull --ff-only origin main

The utility does not merge feature branches or open pull requests.

CMIS #549 remains intentionally deferred and is not merged by this script.

## PASS condition

A successful run ends with:

    LOCAL_STACK_SYNC=PASS

That means:

- all four local repository HEADs equal their corresponding origin/main;
- the CMIS private-core contract imports successfully;
- CMIS health on 8765 passed;
- ROBERTA health on 8766 passed;
- the live website contains the accepted progressive evidence UI.

The script does not print local provider or model secrets.
