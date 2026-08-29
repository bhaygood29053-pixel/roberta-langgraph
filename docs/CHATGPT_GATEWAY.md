# ChatGPT Gateway v1

Status: implementation slice for Issue #261.

## Purpose

This gateway lets an external conversational client such as ChatGPT send a user message to the real Roberta runtime without bypassing Roberta, X1 Scout, CMIS, or provider authority.

The authority path remains:

```text
User
  -> ChatGPT transport
    -> HTTPS gateway edge
      -> Roberta public bridge
        -> roberta-private-core
          -> Chain Scout
            -> CMIS
              -> Provider
```

The gateway is a transport seam only. It does not expose CMIS/provider tools, allow caller-selected routing, or authorize execution.

## Contract

Gateway contract:

```text
roberta-chat-gateway/v1
```

Endpoints:

```text
GET  /v1/gateway/capabilities
POST /v1/gateway/ask
```

The legacy local integration endpoint remains available:

```text
POST /v1/roberta
```

The dedicated gateway endpoint accepts exactly:

```json
{"message":"Investigate AGI"}
```

Unknown structured fields are rejected. A caller cannot choose tools, providers, Scouts, CMIS operations, routes, execution modes, or authority.

Successful gateway response:

```json
{
  "service": "roberta_bridge",
  "status": "ok",
  "gateway_contract": "roberta-chat-gateway/v1",
  "mode": "read_only",
  "reply": "Roberta's final response",
  "execution_authorized": false
}
```

## Authentication

Set a long random Bearer token in the runtime environment:

```bash
export ROBERTA_API_KEY="$(openssl rand -hex 32)"
```

Store the value in a local secret file or secret manager. Do not commit it.

When the bridge binds to any non-loopback interface, `ROBERTA_API_KEY` is mandatory and startup fails closed if it is missing. The dedicated `/v1/gateway/*` endpoints also fail closed with `gateway_auth_not_configured` when no API key is configured, even on loopback. The legacy local `/v1/roberta` endpoint keeps its existing loopback behavior.

For the recommended deployment, keep the Python bridge on loopback:

```text
127.0.0.1:8766
```

and require the same Bearer token for gateway requests.

## HTTPS deployment

Do not expose the Python HTTP server directly to the Internet.

Recommended topology:

```text
ChatGPT
  -> HTTPS reverse proxy / secure tunnel / WAF
    -> 127.0.0.1:8766
```

The external edge should:

- terminate TLS;
- forward only the dedicated gateway paths needed by the connector;
- preserve the `Authorization: Bearer ...` header;
- reject plaintext Internet access;
- apply request-size and rate limits;
- avoid logging Bearer tokens or full sensitive prompts;
- keep `/healthz` public only if operationally necessary;
- avoid exposing the legacy `/v1/roberta` endpoint externally unless separately required.

## ChatGPT connector/action preparation

The repository includes:

```text
docs/roberta_gateway_openapi.yaml
```

Before importing that contract into an external connector/action:

1. replace the placeholder server host with the real HTTPS gateway hostname;
2. configure Bearer authentication using the runtime `ROBERTA_API_KEY`;
3. verify `GET /v1/gateway/capabilities` returns `execution_authorized=false`;
4. test one request against `POST /v1/gateway/ask`;
5. confirm the response is from the live Roberta service rather than a local mock.

## MCP transport

Gateway v1 is the authenticated Roberta HTTP seam. Gateway Phase 2 adds a
separate loopback-only MCP transport process that forwards exactly one
read-only `ask_roberta(message)` tool to this seam.

See:

```text
docs/CHATGPT_MCP_GATEWAY.md
```

The MCP edge does not create a second Roberta runtime and does not bypass this
Gateway v1 contract.

## Public/private boundary

This feature belongs in the public shell because it defines transport, authentication, schemas, and deployment contracts.

The following remain private:

- graph/orchestration implementation;
- prompts and policy logic;
- specialist planning;
- learning implementation;
- proprietary reasoning logic.

The public repository's mandatory CI boundary gate must remain green. A gateway change must not move private-core implementation back into the public repository.

## Non-goals

This contract does not authorize:

- direct ChatGPT -> CMIS access;
- direct provider access;
- caller-selected tools or routes;
- wallet signing;
- transaction construction or broadcasting;
- custody;
- swaps or trading;
- bridge value movement;
- autonomous value movement.

**The gateway transports a message to Roberta. Roberta keeps orchestration authority, and CMIS keeps deterministic fact/evidence/risk authority.**
