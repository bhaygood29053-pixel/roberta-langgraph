"""Read-only MCP transport edge for ChatGPT -> ROBERTA.

This module is public transport code. It does not import ROBERTA private-core
implementation, Chain Scouts, CMIS, or providers. It forwards exactly one
natural-language message to the already-authenticated loopback Gateway v1 seam.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from mcp.server import MCPServer
from mcp.types import ToolAnnotations

DEFAULT_MCP_HOST = "127.0.0.1"
DEFAULT_MCP_PORT = 8767
DEFAULT_MCP_PATH = "/mcp"
DEFAULT_UPSTREAM_URL = "http://127.0.0.1:8766/v1/gateway/ask"
DEFAULT_TIMEOUT_SECONDS = 90.0
GATEWAY_CONTRACT = "roberta-chat-gateway/v1"
_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
_EXPECTED_UPSTREAM_PATH = "/v1/gateway/ask"


class RobertaMCPGatewayError(RuntimeError):
    """The MCP edge could not safely obtain a valid Roberta gateway reply."""


def _api_key(value: str | None = None) -> str:
    key = str(value if value is not None else os.getenv("ROBERTA_API_KEY", "")).strip()
    if not key:
        raise RobertaMCPGatewayError(
            "ROBERTA_API_KEY must be configured before the MCP edge can call Roberta."
        )
    return key


def _validated_upstream_url(value: str | None = None) -> str:
    raw = str(
        value if value is not None else os.getenv(
            "ROBERTA_MCP_UPSTREAM_URL", DEFAULT_UPSTREAM_URL
        )
    ).strip()
    try:
        parsed = urllib.parse.urlsplit(raw)
    except ValueError as exc:
        raise RobertaMCPGatewayError("Invalid ROBERTA_MCP_UPSTREAM_URL.") from exc

    if parsed.scheme != "http":
        raise RobertaMCPGatewayError("MCP upstream must use loopback HTTP.")
    if (parsed.hostname or "").lower() not in _LOOPBACK_HOSTS:
        raise RobertaMCPGatewayError("MCP upstream must remain loopback-only.")
    if parsed.username is not None or parsed.password is not None:
        raise RobertaMCPGatewayError("MCP upstream URL must not contain credentials.")
    if parsed.path != _EXPECTED_UPSTREAM_PATH:
        raise RobertaMCPGatewayError(
            "MCP upstream must target the exact Gateway v1 ask path."
        )
    if parsed.query or parsed.fragment:
        raise RobertaMCPGatewayError(
            "MCP upstream URL must not contain a query string or fragment."
        )
    return raw


def _timeout_seconds(value: float | str | None = None) -> float:
    raw: float | str = (
        value
        if value is not None
        else os.getenv("ROBERTA_MCP_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS))
    )
    try:
        timeout = float(raw)
    except (TypeError, ValueError) as exc:
        raise RobertaMCPGatewayError(
            "ROBERTA_MCP_TIMEOUT_SECONDS must be numeric."
        ) from exc
    if timeout <= 0 or timeout > 300:
        raise RobertaMCPGatewayError(
            "ROBERTA_MCP_TIMEOUT_SECONDS must be greater than 0 and at most 300."
        )
    return timeout


def _validated_gateway_response(payload: Any) -> dict[str, object]:
    if not isinstance(payload, dict):
        raise RobertaMCPGatewayError("Roberta gateway returned an invalid response.")

    if payload.get("service") != "roberta_bridge":
        raise RobertaMCPGatewayError("Roberta gateway service identity mismatch.")
    if payload.get("status") != "ok":
        raise RobertaMCPGatewayError("Roberta gateway did not return status=ok.")
    if payload.get("gateway_contract") != GATEWAY_CONTRACT:
        raise RobertaMCPGatewayError("Roberta gateway contract mismatch.")
    if payload.get("mode") != "read_only":
        raise RobertaMCPGatewayError("Roberta gateway is not in read-only mode.")
    if payload.get("execution_authorized") is not False:
        raise RobertaMCPGatewayError(
            "Roberta gateway did not explicitly deny execution authority."
        )

    reply = payload.get("reply")
    if not isinstance(reply, str) or not reply.strip():
        raise RobertaMCPGatewayError("Roberta gateway returned no usable reply.")

    return {
        "gateway_contract": GATEWAY_CONTRACT,
        "mode": "read_only",
        "reply": reply.strip(),
        "execution_authorized": False,
    }


def ask_roberta_via_gateway(
    message: str,
    *,
    upstream_url: str | None = None,
    api_key: str | None = None,
    timeout_seconds: float | str | None = None,
) -> dict[str, object]:
    """Send one natural-language message to the exact loopback Gateway v1 seam."""

    user_text = str(message or "").strip()
    if not user_text:
        raise ValueError("message must be a non-empty string")

    url = _validated_upstream_url(upstream_url)
    key = _api_key(api_key)
    timeout = _timeout_seconds(timeout_seconds)

    body = json.dumps(
        {"message": user_text},
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "roberta-mcp-gateway/1",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        raise RobertaMCPGatewayError(
            f"Roberta gateway rejected the MCP request with HTTP {exc.code}."
        ) from exc
    except urllib.error.URLError as exc:
        raise RobertaMCPGatewayError("Roberta gateway is unavailable.") from exc

    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RobertaMCPGatewayError(
            "Roberta gateway returned invalid UTF-8 JSON."
        ) from exc

    return _validated_gateway_response(payload)


def build_mcp_server() -> MCPServer:
    """Build the one-tool read-only MCP surface for Roberta."""

    server = MCPServer(
        "ROBERTA — Verified On-Chain Intelligence",
        instructions=(
            "Use ask_roberta to send a natural-language question to Roberta. "
            "This server is read-only. It does not expose tool selection, direct "
            "CMIS/provider access, transaction execution, signing, custody, or "
            "autonomous value movement."
        ),
    )

    @server.tool(
        name="ask_roberta",
        title="Ask Roberta",
        description=(
            "Ask ROBERTA — Verified On-Chain Intelligence one natural-language "
            "question. Roberta keeps orchestration authority and may route through "
            "the appropriate Chain Scout and CMIS. The caller cannot select tools, "
            "providers, routes, Scouts, or CMIS operations."
        ),
        annotations=ToolAnnotations(
            read_only_hint=True,
            open_world_hint=True,
        ),
    )
    def ask_roberta(message: str) -> dict[str, object]:
        return ask_roberta_via_gateway(message)

    return server


def main() -> None:
    """Run the local Streamable HTTP MCP edge for a secure remote tunnel."""

    host = os.getenv("ROBERTA_MCP_HOST", DEFAULT_MCP_HOST).strip()
    if host.lower() not in _LOOPBACK_HOSTS:
        raise RobertaMCPGatewayError(
            "ROBERTA_MCP_HOST must remain loopback-only. Use a secure MCP tunnel "
            "or separately reviewed authenticated HTTPS edge for remote access."
        )

    try:
        port = int(os.getenv("ROBERTA_MCP_PORT", str(DEFAULT_MCP_PORT)))
    except ValueError as exc:
        raise RobertaMCPGatewayError("ROBERTA_MCP_PORT must be an integer.") from exc
    if not 1 <= port <= 65535:
        raise RobertaMCPGatewayError("ROBERTA_MCP_PORT must be between 1 and 65535.")

    # Validate fail-closed upstream configuration before opening a listener.
    _validated_upstream_url()
    _api_key()
    _timeout_seconds()

    build_mcp_server().run(
        transport="streamable-http",
        host=host,
        port=port,
        streamable_http_path=DEFAULT_MCP_PATH,
        stateless_http=True,
        json_response=True,
    )


if __name__ == "__main__":
    main()


__all__ = [
    "DEFAULT_MCP_HOST",
    "DEFAULT_MCP_PORT",
    "DEFAULT_MCP_PATH",
    "DEFAULT_UPSTREAM_URL",
    "GATEWAY_CONTRACT",
    "RobertaMCPGatewayError",
    "ask_roberta_via_gateway",
    "build_mcp_server",
    "main",
]
