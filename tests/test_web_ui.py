from __future__ import annotations

import threading
import urllib.request

from langchain_core.messages import AIMessage

from roberta.bridge_http import RobertaBridge, create_server
from roberta.web_ui import ROBERTA_WEB_UI_HTML


class FakeGraph:
    def invoke(self, payload):
        return {"messages": [AIMessage(content="ok")], "status": "complete"}


def test_web_ui_is_conversation_first_investigation_experience():
    # Homepage: ROBERTA is taught in seconds through one universal question box.
    assert "Ask ROBERTA anything about X1." in ROBERTA_WEB_UI_HTML
    assert 'id="landingAsk"' in ROBERTA_WEB_UI_HTML
    assert 'id="landingSend"' in ROBERTA_WEB_UI_HTML
    assert "Should I buy $500 of AGI?" in ROBERTA_WEB_UI_HTML
    assert "What happened to this wallet?" in ROBERTA_WEB_UI_HTML
    assert "Compare XNT and AGI." in ROBERTA_WEB_UI_HTML
    assert "Why did this token price move?" in ROBERTA_WEB_UI_HTML
    assert "Trace this transaction." in ROBERTA_WEB_UI_HTML
    assert "Show me the safest liquid tokens on X1." in ROBERTA_WEB_UI_HTML
    assert "function askFromLanding" in ROBERTA_WEB_UI_HTML

    # Public navigation is outcome-oriented, not a technical service catalog.
    assert "What can ROBERTA help with?" in ROBERTA_WEB_UI_HTML
    assert ">Tokens<" in ROBERTA_WEB_UI_HTML
    assert ">Trades<" in ROBERTA_WEB_UI_HTML
    assert ">Wallets<" in ROBERTA_WEB_UI_HTML
    assert ">Compare<" in ROBERTA_WEB_UI_HTML
    assert ">Market<" in ROBERTA_WEB_UI_HTML
    assert ">Investigations<" in ROBERTA_WEB_UI_HTML
    assert "CMIS" not in ROBERTA_WEB_UI_HTML
    assert "X1 Scout" not in ROBERTA_WEB_UI_HTML
    assert "verification_evidence/v1" not in ROBERTA_WEB_UI_HTML
    assert "risk_check" not in ROBERTA_WEB_UI_HTML
    assert "market_report" not in ROBERTA_WEB_UI_HTML

    # First question transforms the product into the chat workspace.
    assert 'id="workspace"' in ROBERTA_WEB_UI_HTML
    assert "workspaceMode" in ROBERTA_WEB_UI_HTML
    assert "function enterWorkspace" in ROBERTA_WEB_UI_HTML
    assert "function leaveWorkspace" in ROBERTA_WEB_UI_HTML
    assert "robertaWorkspaceMode" in ROBERTA_WEB_UI_HTML

    # Left side: new chat, history, services drawer, and saved investigations.
    assert 'id="newChat"' in ROBERTA_WEB_UI_HTML
    assert 'id="historyList"' in ROBERTA_WEB_UI_HTML
    assert 'id="savedList"' in ROBERTA_WEB_UI_HTML
    assert "Saved investigations" in ROBERTA_WEB_UI_HTML
    assert 'id="servicesToggle"' in ROBERTA_WEB_UI_HTML
    assert 'id="sideServices"' in ROBERTA_WEB_UI_HTML
    assert 'id="clearHistory"' in ROBERTA_WEB_UI_HTML

    # Permanent browser-local history plus saved-investigation/recheck controls.
    assert "robertaChatHistoryV3" in ROBERTA_WEB_UI_HTML
    assert "robertaSavedInvestigationsV1" in ROBERTA_WEB_UI_HTML
    assert "localStorage.getItem" in ROBERTA_WEB_UI_HTML
    assert "localStorage.setItem" in ROBERTA_WEB_UI_HTML
    assert "Today" in ROBERTA_WEB_UI_HTML
    assert "Previous" in ROBERTA_WEB_UI_HTML
    assert "Save Investigation" in ROBERTA_WEB_UI_HTML
    assert "Recheck with current data" in ROBERTA_WEB_UI_HTML
    assert "function saveInvestigation" in ROBERTA_WEB_UI_HTML

    # Center stays conversational with a universal command bar and strong empty state.
    assert 'id="commandInput"' in ROBERTA_WEB_UI_HTML
    assert 'id="commandSend"' in ROBERTA_WEB_UI_HTML
    assert "What do you want to know?" in ROBERTA_WEB_UI_HTML
    assert "Analyze a token" in ROBERTA_WEB_UI_HTML
    assert "Check a trade" in ROBERTA_WEB_UI_HTML
    assert "Investigate a wallet" in ROBERTA_WEB_UI_HTML
    assert "Compare two assets" in ROBERTA_WEB_UI_HTML
    assert "Trace a transaction" in ROBERTA_WEB_UI_HTML
    assert "Find unusual activity" in ROBERTA_WEB_UI_HTML

    # Conversation continuity uses an explicit bridge thread id. The browser does
    # not paste prior assistant prose or historical market snapshots into a new
    # user message.
    assert "thread_id:chatId" in ROBERTA_WEB_UI_HTML
    assert "Continue this conversation using the recent context below." not in ROBERTA_WEB_UI_HTML
    assert "User follow-up:" not in ROBERTA_WEB_UI_HTML

    # Right side is optional / collapsible and evidence never becomes the primary interface.
    assert 'id="inspector"' in ROBERTA_WEB_UI_HTML
    assert 'id="inspectorToggle"' in ROBERTA_WEB_UI_HTML
    assert "Evidence &amp; details" in ROBERTA_WEB_UI_HTML
    assert "Optional — conversation remains primary" in ROBERTA_WEB_UI_HTML
    assert "The interface does not invent missing sources or time-series data." in ROBERTA_WEB_UI_HTML

    # Answers support human-first fact/judgment/confidence presentation.
    assert "Verified fact" in ROBERTA_WEB_UI_HTML
    assert "ROBERTA['’]s assessment" in ROBERTA_WEB_UI_HTML
    assert "Uncertain" in ROBERTA_WEB_UI_HTML
    assert "Confidence" in ROBERTA_WEB_UI_HTML
    assert "My recommendation" in ROBERTA_WEB_UI_HTML
    assert "Evidence quality" in ROBERTA_WEB_UI_HTML
    assert "What would change my mind" in ROBERTA_WEB_UI_HTML
    assert ".factLine" in ROBERTA_WEB_UI_HTML
    assert ".opinionLine" in ROBERTA_WEB_UI_HTML
    assert ".uncertainLine" in ROBERTA_WEB_UI_HTML
    assert ".confidenceLine" in ROBERTA_WEB_UI_HTML
    assert "ROBERTA judgment" in ROBERTA_WEB_UI_HTML
    assert "function decisionLabelFromText" in ROBERTA_WEB_UI_HTML
    assert "function primaryDriverFromText" in ROBERTA_WEB_UI_HTML
    assert "function unknownsFromText" in ROBERTA_WEB_UI_HTML
    assert "function changeMindFromText" in ROBERTA_WEB_UI_HTML

    # Risk, evidence quality, and freshness have separate presentation semantics.
    assert "function riskClass" in ROBERTA_WEB_UI_HTML
    assert "function evidenceQualityClass" in ROBERTA_WEB_UI_HTML
    assert "function freshnessClass" in ROBERTA_WEB_UI_HTML
    assert "['high','veryhigh','block','severe','critical'].indexOf(v)>=0)return'bad'" in ROBERTA_WEB_UI_HTML
    assert "['strong','verystrong','high','verified'].indexOf(v)>=0)return'good'" in ROBERTA_WEB_UI_HTML
    assert "machineStatusToken" in ROBERTA_WEB_UI_HTML

    # Evidence is progressively disclosed with native keyboard-safe details/summary.
    assert '<details class="answerEvidenceDisclosure">' in ROBERTA_WEB_UI_HTML
    assert "<summary>View evidence &amp; details</summary>" in ROBERTA_WEB_UI_HTML
    assert '<details class="inspectorBlock evidencePanel">' in ROBERTA_WEB_UI_HTML
    assert "View evidence &amp; technical detail" in ROBERTA_WEB_UI_HTML
    assert "This browser does not calculate risk, compliance, freshness, or market facts." in ROBERTA_WEB_UI_HTML
    assert "Ask ROBERTA for evidence" in ROBERTA_WEB_UI_HTML
    assert "Explain Simply" in ROBERTA_WEB_UI_HTML
    assert ">Chart<" in ROBERTA_WEB_UI_HTML
    assert "Compare Token" in ROBERTA_WEB_UI_HTML
    assert "Check Wallet" in ROBERTA_WEB_UI_HTML
    assert "function followupPrompt" in ROBERTA_WEB_UI_HTML

    # Long on-chain identifiers are clickable as generic identifiers without guessing their type.
    assert "entityLink" in ROBERTA_WEB_UI_HTML
    assert "data-entity" in ROBERTA_WEB_UI_HTML
    assert "Selected on-chain identifier" in ROBERTA_WEB_UI_HTML
    assert "function openEntity" in ROBERTA_WEB_UI_HTML
    assert "Investigate this identifier" in ROBERTA_WEB_UI_HTML
    assert "Trace related activity" in ROBERTA_WEB_UI_HTML

    # Waiting feels productive without exposing provider/RPC implementation details.
    assert "ROBERTA is investigating…" in ROBERTA_WEB_UI_HTML
    assert "Routing your question" in ROBERTA_WEB_UI_HTML
    assert "Checking available verified evidence" in ROBERTA_WEB_UI_HTML
    assert "Reviewing relevant activity and history" in ROBERTA_WEB_UI_HTML
    assert "Preparing a clear answer" in ROBERTA_WEB_UI_HTML
    assert "function startInvestigation" in ROBERTA_WEB_UI_HTML

    # Browser still talks only to the ROBERTA bridge.
    assert "POST /v1/roberta" in ROBERTA_WEB_UI_HTML
    assert "fetch(apiUrl('/v1/roberta')" in ROBERTA_WEB_UI_HTML
    assert "fetch(apiUrl('/healthz')" in ROBERTA_WEB_UI_HTML
    assert "ROBERTA does not execute transactions from this website." in ROBERTA_WEB_UI_HTML


def test_bridge_serves_web_ui_and_keeps_roberta_api_path():
    server = create_server(
        host="127.0.0.1",
        port=0,
        bridge=RobertaBridge(FakeGraph()),
        api_key="",
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        with urllib.request.urlopen(base + "/", timeout=2) as response:
            html = response.read().decode("utf-8")
            assert response.status == 200
            assert response.headers["Content-Type"] == "text/html; charset=utf-8"
            assert "ROBERTA — Verified On-Chain Intelligence" in html
            assert 'id="landingAsk"' in html
            assert 'id="workspace"' in html
            assert "/v1/roberta" in html

        with urllib.request.urlopen(base + "/healthz", timeout=2) as response:
            assert response.status == 200
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_web_ui_progressive_disclosure_never_calculates_risk_or_bypasses_roberta():
    html = ROBERTA_WEB_UI_HTML

    # Human labels are presentation projections of ROBERTA-returned wording only.
    assert "function decisionLabelFromText" in html
    assert "function updateInspector" in html
    assert "extractField(text,'Risk')" in html
    assert "evidenceQualityFromText(text)" in html
    assert "freshnessClass(fresh)" in html

    # The browser must not call CMIS/provider endpoints or implement risk/compliance arithmetic.
    assert "fetch(apiUrl('/v1/roberta')" in html
    assert "fetch(apiUrl('/healthz')" in html
    assert "fetch(apiUrl('/v1/cmis" not in html
    assert "fetch(apiUrl('/cmis" not in html
    assert "riskScore" not in html
    assert "complianceScore" not in html
    assert "calculateRisk" not in html
    assert "calculateCompliance" not in html

    # HIGH has field-specific semantics: bad for risk, good only for evidence quality.
    risk_block = html[html.index("function riskClass"):html.index("function evidenceQualityClass")]
    evidence_block = html[
        html.index("function evidenceQualityClass"):html.index("function freshnessClass")
    ]
    assert "'high'" in risk_block and "return'bad'" in risk_block
    assert "'high'" in evidence_block and "return'good'" in evidence_block


def test_web_ui_evidence_disclosure_is_native_keyboard_accessible():
    html = ROBERTA_WEB_UI_HTML

    # Native details/summary controls are keyboard operable without custom key handlers.
    assert '<details class="answerEvidenceDisclosure">' in html
    assert "<summary>View evidence &amp; details</summary>" in html
    assert '<details class="inspectorBlock evidencePanel">' in html
    assert ".answerEvidenceDisclosure summary:focus-visible" in html
    assert ".evidencePanel>summary:focus-visible" in html

    # Collapsible side inspector publishes its expanded state for assistive technology.
    assert "setAttribute('aria-expanded','true')" in html
    assert "Expand evidence panel" in html
    assert "Collapse evidence panel" in html
