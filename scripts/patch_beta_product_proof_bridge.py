from pathlib import Path

path = Path("src/roberta/bridge_http.py")
text = path.read_text(encoding="utf-8")

text = text.replace("import os\n", "import os\nimport time\n", 1)
anchor = "from roberta.evaluation_telemetry import (\n    EVALUATION_TELEMETRY_V2,\n    extend_evaluation_telemetry_v2,\n)\n"
replacement = anchor + "from roberta.beta_product_proof import (\n    BetaProductProofError,\n    append_beta_record,\n    build_automatic_outcome,\n    build_user_feedback,\n    configured_beta_path,\n)\n"
if anchor not in text:
    raise SystemExit("evaluation telemetry import anchor drifted")
text = text.replace(anchor, replacement, 1)

post_anchor = "        def do_POST(self):  # noqa: N802 - BaseHTTPRequestHandler API\n            if self.path != \"/v1/roberta\":\n"
feedback_block = '''        def do_POST(self):  # noqa: N802 - BaseHTTPRequestHandler API
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
'''
if post_anchor not in text:
    raise SystemExit("POST anchor drifted")
text = text.replace(post_anchor, feedback_block, 1)

try_anchor = '''            try:
                telemetry = None
                if evaluation_mode in SUPPORTED_EVALUATION_TELEMETRY_VERSIONS:
                    reply, telemetry = bridge.ask_with_evaluation(
                        message,
                        thread_id=thread_id,
                        evaluation_mode=evaluation_mode,
                    )
                else:
                    reply = bridge.ask(message, thread_id=thread_id)
'''
try_replacement = '''            beta_started = time.perf_counter()
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
'''
if try_anchor not in text:
    raise SystemExit("request execution anchor drifted")
text = text.replace(try_anchor, try_replacement, 1)

response_anchor = '''            response_payload = {
                "service": "roberta_bridge",
                "status": "ok",
                "reply": reply,
            }
'''
response_replacement = '''            if beta_enabled and isinstance(beta_telemetry, Mapping):
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
'''
if response_anchor not in text:
    raise SystemExit("response payload anchor drifted")
text = text.replace(response_anchor, response_replacement, 1)

path.write_text(text, encoding="utf-8")
