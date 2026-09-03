"""Loopback-first HTTP bridge for local transports such as MoltGrid/Signal.

The bridge accepts a user message, runs the normal Roberta graph, and returns
only Roberta's final assistant reply. It does not expose CMIS/provider tools or
accept tool-selection parameters from the caller.
"""

from __future__ import annotations

import argparse
import hmac
import json
import os
from collections.abc import Mapping
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Optional

from langchain_core.messages import AIMessage

from roberta.private_core import build_graph
from roberta.web_ui import web_ui_bytes

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8766
MAX_REQUEST_BYTES = 65_536
_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


def _json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _api_key(value: Optional[str] = None) -> str:
    if value is not None:
        return str(value).strip()
    return os.getenv("ROBERTA_API_KEY", "").strip()


def _validate_bind(host: str, api_key: str) -> None:
    if str(host).strip().lower() not in _LOOPBACK_HOSTS and not api_key:
        raise RuntimeError(
            "ROBERTA_API_KEY is required when the Roberta bridge binds to a "
            "non-loopback host."
        )


def _message_text(message: object) -> str:
    text = getattr(message, "text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()
    content = getattr(message, "content", "")
    return content.strip() if isinstance(content, str) else str(content).strip()


def build_runtime_graph():
    """Build the same live Roberta graph used by the CLI smoke test."""
    from roberta.models import create_runtime_model
    from roberta.tools import get_roberta_tools

    oracle_model = create_runtime_model()
    x1_planner_model = create_runtime_model()
    tools = get_roberta_tools(x1_planner_model=x1_planner_model)
    return build_graph(model=oracle_model, tools=tools)


class RobertaBridge:
    """Small application boundary around a compiled Roberta graph."""

    def __init__(self, graph: Any):
        self._graph = graph

    @classmethod
    def from_runtime(cls) -> "RobertaBridge":
        return cls(build_runtime_graph())

    def ask(self, message: str) -> str:
        user_text = str(message or "").strip()
        if not user_text:
            raise ValueError("A non-empty user message is required.")

        result = self._graph.invoke(
            {
                "messages": [{"role": "user", "content": user_text}],
                "status": "running",
            }
        )
        if not isinstance(result, Mapping):
            raise RuntimeError("Roberta graph returned an invalid result.")
        messages = result.get("messages")
        if not isinstance(messages, list):
            raise RuntimeError("Roberta graph returned no message list.")

        for item in reversed(messages):
            if isinstance(item, AIMessage) and not item.tool_calls:
                reply = _message_text(item)
                if reply:
                    return reply
        raise RuntimeError("Roberta graph returned no final assistant reply.")


def make_handler(bridge: RobertaBridge, *, api_key: str = ""):
    required_key = str(api_key or "").strip()

    class RobertaBridgeHandler(BaseHTTPRequestHandler):
        server_version = "RobertaBridge/1"

        def _send_json(self, status_code: int, payload: Any) -> None:
            body = _json_bytes(payload)
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _send_html(self, status_code: int, body: bytes) -> None:
            self.send_response(status_code)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _authorized(self) -> bool:
            if not required_key:
                return True
            header = str(self.headers.get("Authorization") or "")
            prefix = "Bearer "
            if not header.startswith(prefix):
                return False
            supplied = header[len(prefix):].strip()
            return bool(supplied) and hmac.compare_digest(supplied, required_key)

        def _require_authorized(self) -> bool:
            if self._authorized():
                return True
            self._send_json(
                401,
                {
                    "service": "roberta_bridge",
                    "status": "error",
                    "error": {
                        "code": "unauthorized",
                        "message": "A valid Roberta Bearer token is required.",
                    },
                },
            )
            return False

        def do_GET(self):  # noqa: N802 - BaseHTTPRequestHandler API
            if self.path in {"/", "/app", "/index.html"}:
                self._send_html(200, web_ui_bytes())
                return
            if self.path == "/healthz":
                self._send_json(
                    200,
                    {"service": "roberta_bridge", "status": "ok", "version": 1},
                )
                return
            self._send_json(
                404,
                {
                    "service": "roberta_bridge",
                    "status": "error",
                    "error": {"code": "not_found", "message": "Unknown Roberta path."},
                },
            )

        def do_POST(self):  # noqa: N802 - BaseHTTPRequestHandler API
            if self.path != "/v1/roberta":
                self._send_json(
                    404,
                    {
                        "service": "roberta_bridge",
                        "status": "error",
                        "error": {"code": "not_found", "message": "Unknown Roberta path."},
                    },
                )
                return
            if not self._require_authorized():
                return

            raw_length = self.headers.get("Content-Length")
            try:
                length = int(raw_length or "0")
            except ValueError:
                length = -1
            if length <= 0:
                self._send_json(
                    400,
                    {
                        "service": "roberta_bridge",
                        "status": "error",
                        "error": {
                            "code": "request_body_required",
                            "message": "A JSON request body is required.",
                        },
                    },
                )
                return
            if length > MAX_REQUEST_BYTES:
                self._send_json(
                    413,
                    {
                        "service": "roberta_bridge",
                        "status": "error",
                        "error": {
                            "code": "request_too_large",
                            "message": "Roberta request body exceeds the configured limit.",
                        },
                    },
                )
                return

            try:
                request = json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                self._send_json(
                    400,
                    {
                        "service": "roberta_bridge",
                        "status": "error",
                        "error": {
                            "code": "invalid_json",
                            "message": "Request body must contain valid UTF-8 JSON.",
                        },
                    },
                )
                return
            if not isinstance(request, Mapping):
                self._send_json(
                    400,
                    {
                        "service": "roberta_bridge",
                        "status": "error",
                        "error": {
                            "code": "invalid_request",
                            "message": "Request body must be a JSON object.",
                        },
                    },
                )
                return

            message = request.get("message")
            if not isinstance(message, str) or not message.strip():
                self._send_json(
                    400,
                    {
                        "service": "roberta_bridge",
                        "status": "error",
                        "error": {
                            "code": "message_required",
                            "message": "A non-empty string field named 'message' is required.",
                        },
                    },
                )
                return

            try:
                reply = bridge.ask(message)
            except Exception as exc:  # fail closed without leaking prompts/secrets
                self._send_json(
                    503,
                    {
                        "service": "roberta_bridge",
                        "status": "error",
                        "error": {
                            "code": "roberta_unavailable",
                            "message": f"Roberta could not complete the request ({type(exc).__name__}).",
                        },
                    },
                )
                return

            self._send_json(
                200,
                {
                    "service": "roberta_bridge",
                    "status": "ok",
                    "reply": reply,
                },
            )

        def log_message(self, format, *args):  # noqa: A003
            super().log_message(format, *args)

    return RobertaBridgeHandler


def create_server(
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    bridge: RobertaBridge | None = None,
    api_key: Optional[str] = None,
) -> ThreadingHTTPServer:
    key = _api_key(api_key)
    _validate_bind(host, key)
    handler = make_handler(bridge or RobertaBridge.from_runtime(), api_key=key)
    return ThreadingHTTPServer((host, int(port)), handler)


def serve(
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    bridge: RobertaBridge | None = None,
    api_key: Optional[str] = None,
) -> None:
    server = create_server(host=host, port=port, bridge=bridge, api_key=api_key)
    print(f"Roberta bridge listening on http://{host}:{server.server_port}/v1/roberta")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Serve the local Roberta message bridge for MoltGrid/Signal."
    )
    parser.add_argument(
        "--host",
        default=os.getenv("ROBERTA_HOST", DEFAULT_HOST),
        help="Bind host (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("ROBERTA_PORT", str(DEFAULT_PORT))),
        help=f"Bind port (default: {DEFAULT_PORT})",
    )
    args = parser.parse_args()
    serve(host=args.host, port=args.port)


if __name__ == "__main__":
    main()


__all__ = [
    "DEFAULT_HOST",
    "DEFAULT_PORT",
    "MAX_REQUEST_BYTES",
    "RobertaBridge",
    "build_runtime_graph",
    "create_server",
    "make_handler",
    "serve",
]
