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
import time
from collections.abc import Mapping
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Optional

from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver

from roberta.evaluation_telemetry import (
    EVALUATION_TELEMETRY_V2,
    extend_evaluation_telemetry_v2,
)
from roberta.beta_product_proof import (
    BetaProductProofError,
    append_beta_record,
    build_automatic_outcome,
    build_user_feedback,
    configured_beta_path,
)
from roberta.private_core import build_graph
from roberta.web_ui import web_ui_bytes

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8766
MAX_REQUEST_BYTES = 65_536
EVALUATION_TELEMETRY_VERSION = "roberta_evaluation_telemetry/v1"
SUPPORTED_EVALUATION_TELEMETRY_VERSIONS = frozenset(
    {EVALUATION_TELEMETRY_VERSION, EVALUATION_TELEMETRY_V2}
)
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


def _mapping_value(value: object) -> dict[str, Any] | None:
    if isinstance(value, Mapping):
        return dict(value)
    return None


def _telemetry_freshness(decision: Mapping[str, Any] | None) -> dict[str, Any]:
    if decision is not None:
        profile = decision.get("evidence_profile")
        if isinstance(profile, list):
            for item in profile:
                if not isinstance(item, Mapping):
                    continue
                if str(item.get("dimension") or "").strip().lower() != "freshness":
                    continue
                return {
                    "state": item.get("state"),
                    "source_ref": item.get("source_ref"),
                    "source_value": item.get("source_value"),
                }
    return {
        "state": "UNAVAILABLE",
        "source_ref": None,
        "source_value": None,
    }


def _telemetry_claims(decision: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    if decision is None:
        return []

    claims: list[dict[str, Any]] = []
    for key in ("subject", "recommendation", "conviction", "evidence_quality"):
        if key not in decision:
            continue
        claims.append(
            {
                "name": key,
                "evidence_path": f"human_response_decision.{key}",
                "value": decision.get(key),
            }
        )

    primary = decision.get("primary_decision_driver")
    if isinstance(primary, Mapping) and "source_value" in primary:
        claims.append(
            {
                "name": "primary_decision_driver",
                "evidence_path": (
                    "human_response_decision.primary_decision_driver.source_value"
                ),
                "value": primary.get("source_value"),
            }
        )
    return claims


def _evaluation_telemetry(message: AIMessage) -> dict[str, Any]:
    additional = (
        message.additional_kwargs
        if isinstance(message.additional_kwargs, Mapping)
        else {}
    )
    decision = _mapping_value(additional.get("roberta_human_response_decision"))
    opinion = _mapping_value(additional.get("roberta_opinion"))
    integrity = _mapping_value(additional.get("roberta_claim_integrity"))
    renderer = _mapping_value(additional.get("roberta_human_renderer"))

    evidence: dict[str, Any] = {}
    if decision is not None:
        evidence["human_response_decision"] = decision
    if opinion is not None:
        evidence["opinion"] = opinion
    if integrity is not None:
        evidence["claim_integrity"] = integrity
    if renderer is not None:
        evidence["human_renderer"] = renderer

    authority_sources = [
        item
        for item in (decision, integrity, opinion, renderer)
        if isinstance(item, Mapping)
    ]
    facts_authority = next(
        (
            item.get("facts_authority")
            for item in authority_sources
            if item.get("facts_authority") is not None
        ),
        None,
    )
    judgment_authority = next(
        (
            item.get("judgment_authority")
            for item in authority_sources
            if item.get("judgment_authority") is not None
        ),
        None,
    )
    source_contracts = (
        list(integrity.get("source_contracts"))
        if integrity is not None
        and isinstance(integrity.get("source_contracts"), list)
        else []
    )

    execution_values = [
        item.get("execution_authorized")
        for item in authority_sources
        if "execution_authorized" in item
    ]
    execution_authorized = any(value is True for value in execution_values)

    return {
        "evaluation_telemetry_version": EVALUATION_TELEMETRY_VERSION,
        "evaluation_evidence": evidence,
        "claims": _telemetry_claims(decision),
        "evidence_provenance": {
            "facts_authority": facts_authority,
            "judgment_authority": judgment_authority,
            "source_contracts": source_contracts,
            "telemetry_scope": "accepted_final_message_structures_only",
        },
        "evidence_freshness": _telemetry_freshness(decision),
        "execution_authorized": execution_authorized,
    }


def build_runtime_graph(*, checkpointer: Any | None = None):
    """Build one live ROBERTA graph with optional checkpoint persistence."""
    from roberta.models import create_runtime_model
    from roberta.tools import get_roberta_tools

    oracle_model = create_runtime_model()
    x1_planner_model = create_runtime_model()
    tools = get_roberta_tools(x1_planner_model=x1_planner_model)
    # Local bridge continuity uses the already-accepted LangGraph checkpoint
    # boundary. The in-memory backend intentionally does not survive process
    # restarts; it is thread state, not durable memory.
    kwargs: dict[str, Any] = {
        "model": oracle_model,
        "tools": tools,
    }
    if checkpointer is not None:
        kwargs["checkpointer"] = checkpointer
    return build_graph(**kwargs)


class RobertaBridge:
    """Small application boundary around a compiled Roberta graph."""

    def __init__(self, graph: Any, *, threaded_graph: Any | None = None):
        self._graph = graph
        self._threaded_graph = threaded_graph or graph

    @classmethod
    def from_runtime(cls) -> "RobertaBridge":
        return cls(
            build_runtime_graph(),
            threaded_graph=build_runtime_graph(checkpointer=InMemorySaver()),
        )

    def _final_message_with_messages(
        self,
        message: str,
        *,
        thread_id: str | None = None,
    ) -> tuple[AIMessage, list[object]]:
        user_text = str(message or "").strip()
        if not user_text:
            raise ValueError("A non-empty user message is required.")
        normalized_thread_id = None
        if thread_id is not None:
            if not isinstance(thread_id, str):
                raise TypeError("thread_id must be a string when provided")
            normalized_thread_id = thread_id.strip()
            if not normalized_thread_id:
                raise ValueError("thread_id must not be empty when provided")
            if len(normalized_thread_id) > 128:
                raise ValueError("thread_id must be 128 characters or fewer")

        inputs = {
            "messages": [{"role": "user", "content": user_text}],
            "status": "running",
        }
        if normalized_thread_id is not None:
            result = self._threaded_graph.invoke(
                inputs,
                config={"configurable": {"thread_id": normalized_thread_id}},
            )
        else:
            result = self._graph.invoke(inputs)
        if not isinstance(result, Mapping):
            raise RuntimeError("Roberta graph returned an invalid result.")
        messages = result.get("messages")
        if not isinstance(messages, list):
            raise RuntimeError("Roberta graph returned no message list.")

        for item in reversed(messages):
            if isinstance(item, AIMessage) and not item.tool_calls:
                if _message_text(item):
                    return item, list(messages)
        raise RuntimeError("Roberta graph returned no final assistant reply.")

    def _final_message(
        self,
        message: str,
        *,
        thread_id: str | None = None,
    ) -> AIMessage:
        final, _messages = self._final_message_with_messages(
            message,
            thread_id=thread_id,
        )
        return final

    def ask(self, message: str, *, thread_id: str | None = None) -> str:
        final = self._final_message(message, thread_id=thread_id)
        return _message_text(final)

    def ask_with_evaluation(
        self,
        message: str,
        *,
        thread_id: str | None = None,
        evaluation_mode: str = EVALUATION_TELEMETRY_VERSION,
    ) -> tuple[str, dict[str, Any]]:
        final, messages = self._final_message_with_messages(
            message,
            thread_id=thread_id,
        )
        telemetry = _evaluation_telemetry(final)
        if evaluation_mode == EVALUATION_TELEMETRY_V2:
            telemetry = extend_evaluation_telemetry_v2(telemetry, messages)
        elif evaluation_mode != EVALUATION_TELEMETRY_VERSION:
            raise ValueError(f"Unsupported evaluation telemetry mode: {evaluation_mode}")
        return _message_text(final), telemetry


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
            if self.path == "/v1/beta-feedback":
                if not self._require_authorized():
                    return
                raw_length = self.headers.get("Content-Length")
                try:
                    length = int(raw_length or "0")
                except ValueError:
                    length = -1
                if length <= 0 or length > MAX_REQUEST_BYTES:
                    self._send_json(400, {"service": "roberta_bridge", "status": "error", "error": {"code": "invalid_beta_feedback", "message": "A bounded JSON feedback body is required."}})
                    return
                try:
                    request = json.loads(self.rfile.read(length).decode("utf-8"))
                    if not isinstance(request, Mapping):
                        raise BetaProductProofError("feedback body must be an object")
                    allowed = {"response_id", "helpful", "clarity", "evidence_drill_down", "would_use_again", "willingness_to_pay", "interest_surface"}
                    if set(request) - allowed:
                        raise BetaProductProofError("unsupported beta feedback fields")
                    record = build_user_feedback(
                        response_id=request.get("response_id"),
                        helpful=request.get("helpful"),
                        clarity=request.get("clarity"),
                        evidence_drill_down=request.get("evidence_drill_down", False),
                        would_use_again=request.get("would_use_again"),
                        willingness_to_pay=request.get("willingness_to_pay"),
                        interest_surface=request.get("interest_surface"),
                    )
                    recorded = append_beta_record(record)
                except (UnicodeDecodeError, json.JSONDecodeError, BetaProductProofError, TypeError) as exc:
                    self._send_json(400, {"service": "roberta_bridge", "status": "error", "error": {"code": "invalid_beta_feedback", "message": f"Beta feedback was rejected ({type(exc).__name__})."}})
                    return
                self._send_json(200, {"service": "roberta_bridge", "status": "ok", "recorded": recorded})
                return

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

            evaluation_mode = request.get("evaluation_mode")
            if (
                evaluation_mode is not None
                and evaluation_mode not in SUPPORTED_EVALUATION_TELEMETRY_VERSIONS
            ):
                self._send_json(
                    400,
                    {
                        "service": "roberta_bridge",
                        "status": "error",
                        "error": {
                            "code": "invalid_evaluation_mode",
                            "message": (
                                "evaluation_mode must be one of "
                                f"{sorted(SUPPORTED_EVALUATION_TELEMETRY_VERSIONS)!r} "
                                "when provided."
                            ),
                        },
                    },
                )
                return

            thread_id = request.get("thread_id")
            if thread_id is not None:
                if not isinstance(thread_id, str) or not thread_id.strip():
                    self._send_json(
                        400,
                        {
                            "service": "roberta_bridge",
                            "status": "error",
                            "error": {
                                "code": "invalid_thread_id",
                                "message": "thread_id must be a non-empty string when provided.",
                            },
                        },
                    )
                    return
                if len(thread_id.strip()) > 128:
                    self._send_json(
                        400,
                        {
                            "service": "roberta_bridge",
                            "status": "error",
                            "error": {
                                "code": "invalid_thread_id",
                                "message": "thread_id must be 128 characters or fewer.",
                            },
                        },
                    )
                    return

            beta_started = time.perf_counter()
            beta_enabled = configured_beta_path() is not None
            beta_telemetry = None
            beta_response_id = None
            try:
                telemetry = None
                if evaluation_mode in SUPPORTED_EVALUATION_TELEMETRY_VERSIONS:
                    reply, telemetry = bridge.ask_with_evaluation(
                        message,
                        thread_id=thread_id,
                        evaluation_mode=evaluation_mode,
                    )
                    beta_telemetry = telemetry
                elif beta_enabled:
                    reply, beta_telemetry = bridge.ask_with_evaluation(
                        message,
                        thread_id=thread_id,
                        evaluation_mode=EVALUATION_TELEMETRY_VERSION,
                    )
                else:
                    reply = bridge.ask(message, thread_id=thread_id)
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

            if beta_enabled and isinstance(beta_telemetry, Mapping):
                try:
                    beta_record = build_automatic_outcome(
                        beta_telemetry,
                        duration_ms=(time.perf_counter() - beta_started) * 1000,
                    )
                    if append_beta_record(beta_record):
                        beta_response_id = beta_record["response_id"]
                except (BetaProductProofError, OSError, TypeError, ValueError):
                    # Product telemetry must never alter answer availability.
                    beta_response_id = None

            response_payload = {
                "service": "roberta_bridge",
                "status": "ok",
                "reply": reply,
            }
            if isinstance(beta_response_id, str):
                response_payload["beta_response_id"] = beta_response_id
            if isinstance(thread_id, str) and thread_id.strip():
                response_payload["thread_id"] = thread_id.strip()
            if isinstance(telemetry, Mapping):
                response_payload.update(telemetry)
            self._send_json(200, response_payload)

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
    "EVALUATION_TELEMETRY_VERSION",
    "EVALUATION_TELEMETRY_V2",
    "SUPPORTED_EVALUATION_TELEMETRY_VERSIONS",
    "RobertaBridge",
    "build_runtime_graph",
    "create_server",
    "make_handler",
    "serve",
]
