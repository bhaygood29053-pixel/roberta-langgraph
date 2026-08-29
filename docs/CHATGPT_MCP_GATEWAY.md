# ChatGPT Gateway Phase 2 — Secure MCP Edge

Status: implementation slice for Issue #265.

## Purpose

Phase 2 adds a Model Context Protocol (MCP) transport edge in front of the
accepted Gateway v1 HTTP seam. It is designed for a secure remote MCP tunnel or
a separately reviewed authenticated HTTPS edge while Roberta itself remains
loopback-only.

The authority path remains:

```text
User
  -> ChatGPT
    -> secure remote MCP transport / tunnel
      -> 127.0.0.1:8767/mcp
        -> ask_roberta
          -> 127.0.0.1:8766/v1/gateway/ask
            -> Roberta
              -> Chain Scout
                -> CMIS
                  -> Provider
```

The MCP process is a public transport adapter. It does not import
`roberta-core`, Chain Scout internals, CMIS internals, provider clients, prompts,
policies, or proprietary reasoning code.

## MCP surface

Phase 2 exposes exactly one MCP tool:

```text
ask_roberta(message: string)
```

The tool is declared read-only and forwards only the natural-language message
to the accepted Gateway v1 endpoint.

The caller cannot provide:

- tool names;
- provider names;
- Scout selection;
- CMIS operation names;
- route overrides;
- execution modes;
- wallet/signing controls.

Roberta remains responsible for orchestration behind the existing private-core
boundary.

## Install

Install the public shell with the MCP extra:

```bash
python -m pip install -e '.[mcp]'
```

The supported SDK line is the current stable MCP Python SDK 2.x:

```text
mcp>=2,<3
```

## Required runtime configuration

Use the same secret already protecting Gateway v1:

```bash
export ROBERTA_API_KEY='replace-with-a-long-random-secret'
```

Recommended settings:

```text
ROBERTA_MCP_HOST=127.0.0.1
ROBERTA_MCP_PORT=8767
ROBERTA_MCP_UPSTREAM_URL=http://127.0.0.1:8766/v1/gateway/ask
ROBERTA_MCP_TIMEOUT_SECONDS=90
```

The MCP edge fails closed if:

- `ROBERTA_API_KEY` is absent;
- the upstream scheme is not loopback HTTP;
- the upstream host is not loopback;
- the upstream path is not exactly `/v1/gateway/ask`;
- the upstream URL contains credentials, query parameters, or a fragment;
- the Gateway v1 response contract is weakened or malformed;
- `execution_authorized` is anything other than exactly `false`.

## Run

Start the existing Roberta bridge first:

```bash
roberta-serve
```

Then start the MCP edge:

```bash
roberta-mcp
```

Default MCP endpoint:

```text
http://127.0.0.1:8767/mcp
```

Do not bind the MCP server directly to a public interface. The command rejects
a non-loopback `ROBERTA_MCP_HOST`.

## Preferred remote connection

ChatGPT connects to remote MCP servers rather than directly to a local server.
For a private/on-premises/developer-machine deployment, use OpenAI's supported
Secure MCP Tunnel when available for the account/workspace. This keeps the MCP
listener private rather than publishing it directly to the Internet.

The safe topology is:

```text
ChatGPT
  -> Secure MCP Tunnel
    -> local 127.0.0.1:8767/mcp
```

If a different HTTPS edge is used, it requires a separate security review. Do
not make `127.0.0.1:8767/mcp` publicly reachable through an unauthenticated
port-forward or generic reverse proxy.

## Managed service

An example unit is provided at:

```text
deploy/systemd/roberta-mcp.service.example
```

It starts after `roberta-bridge.service`, keeps the MCP process loopback-only,
uses the same protected environment file, and restarts after failures.

## Verification

Before connecting any external client, verify:

```bash
curl -fsS http://127.0.0.1:8766/healthz
```

Then use an MCP Inspector/client locally against:

```text
http://127.0.0.1:8767/mcp
```

The discovered tool set must contain exactly:

```text
ask_roberta
```

and the tool must advertise the read-only annotation.

A successful end-to-end test must prove that the MCP result came from the live
Gateway v1 contract and contains:

```text
gateway_contract = roberta-chat-gateway/v1
mode = read_only
execution_authorized = false
```

## Public/private boundary

PUBLIC:

- MCP protocol adapter;
- loopback proxy;
- request/response validation;
- deployment examples;
- tests and documentation.

PRIVATE:

- graph/orchestration implementation;
- prompts/policy;
- specialist planning;
- learning implementation;
- proprietary reasoning logic.

The permanent public/private CI guard remains a merge gate. Phase 2 does not
move any private implementation back into the public repository.

## Non-goals

Phase 2 does not authorize or implement:

- direct ChatGPT -> CMIS access;
- direct provider access;
- caller-selected routing;
- write/modify MCP tools;
- transaction construction;
- signing or broadcasting;
- custody;
- swaps/trading;
- bridge transfer;
- autonomous value movement.

**The MCP edge is transport only. Roberta remains the orchestration authority,
and CMIS remains the deterministic fact/evidence/risk authority.**
