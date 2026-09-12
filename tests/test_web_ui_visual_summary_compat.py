from __future__ import annotations

import json
import shutil
import subprocess

import pytest

from roberta import web_ui
from roberta.web_ui_visual_summary_compat import (
    VISUAL_SUMMARY_COMPAT_MARKER,
    VISUAL_SUMMARY_COMPAT_SURFACE,
    VISUAL_SUMMARY_FIDELITY_MARKER,
    _SCRIPT,
    apply_visual_summary_narrative_compat,
)


def test_visual_summary_narrative_compat_is_applied_to_live_html() -> None:
    html = web_ui.ROBERTA_WEB_UI_HTML
    assert VISUAL_SUMMARY_COMPAT_MARKER in html
    assert VISUAL_SUMMARY_FIDELITY_MARKER in html
    assert VISUAL_SUMMARY_COMPAT_SURFACE == "roberta-visual-summary-narrative-compat/v1"
    assert "function vscNarrativeDashboard" in html
    assert 'class=\"opt2Card\"' in html
    assert 'class=\"opt2PriceCard\"' in html
    assert "RISK READ" in html
    assert "Risk Components" in html
    assert "Live Market Freshness" in html
    assert "Holders / Concentration" in html
    assert "ROBERTA\\'S TAKE" in html
    assert "Evidence &amp; full ROBERTA response" in html


def test_visual_summary_parser_supports_current_human_answer_shape() -> None:
    html = web_ui.ROBERTA_WEB_UI_HTML
    assert "What (?:the )?evidence supports" in html
    assert "missing or unverified" in html
    assert "Deterministic risk recommendation" in html
    assert "Evidence quality" in html
    assert "Bottom line" in html
    assert "24h volume" in html
    assert "transactions" in html
    assert "Tokenomics" in html
    assert "Live Market Freshness" in html
    assert "Holders / Concentration" in html


def test_current_xnt_narrative_renders_approved_option2_not_fallback() -> None:
    node = shutil.which("node")
    if not node:
        pytest.skip("node is unavailable")

    sample = """XNT (X1) — what matters right now

The headline: XNT is a small, thinly-traded X1 asset with a clean authority profile, but the current market picture is only partially verified.

What the evidence supports:
- Price ~$0.34, up ~3.3% over the last 24h on the verified observation set; sampled max drawdown within that window was about -3.8%.
- Liquidity ~$82K across 310 LPs; 24h volume ~$11.8K and ~4,186 transactions. Volume is up ~25% versus the earliest stored observation, but that window is short.
- Tokenomics: total supply ~1.07B, circulating ~14.07M, and both mint and freeze authority are not applicable — no active mint/freeze authority was found. Maximum supply is not independently verified.
- Deterministic risk recommendation: WARN. Component statuses: Liquidity PASS, Activity PASS, History PASS, Tokenomics WARN (verified mint/burn activity not supplied), Freshness WARN. No verified numeric risk score is available.

What's missing or unverified:
- Live market freshness is not fully verified for price, liquidity, 24h volume, and 24h transactions — treat the current market numbers as provider-reported rather than freshly chain-confirmed.
- Holder count and top-account concentration are unavailable; distribution risk is therefore unknown.
- History is bounded to stored verified observations.
- Burn/discovery intelligence did not return usable results.

Evidence quality: WEAK — proof strength is low, freshness is unverified, and source independence is not established.

Bottom line: the only firm positives are the clean authority profile and a modest positive short-window price/liquidity picture; the WARN and unverified freshness mean I would not treat XNT's current market state as confirmed. Analysis only — no trade execution."""

    harness = f"""
function escapeHtml(v){{return String(v==null?'':v).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\"/g,'&quot;')}}
function formatIntelligenceCard(text){{return '<div>Verified snapshot fallback</div>'}}
{_SCRIPT}
const out=formatIntelligenceCard({json.dumps(sample)});
const required=[
  'class=\"opt2Card\"',
  'class=\"opt2PriceCard\"',
  'XNT (X1 native token)',
  '$0.34',
  '+3.3% (24h)',
  '$82K',
  '$11.8K',
  '4,186',
  'Max Drawdown (sampled)',
  'Tokenomics',
  'Risk Components',
  'Live Market Freshness',
  'Holders / Concentration',
  'ROBERTA\\'S TAKE',
  'Evidence &amp; full ROBERTA response'
];
for(const marker of required){{if(!out.includes(marker))throw new Error('missing '+marker+'\\n'+out)}}
if(out.includes('Verified snapshot fallback'))throw new Error('fell back to the old thin snapshot renderer');
console.log('OPTION2_RENDER_PASS');
"""
    run = subprocess.run(
        [node, "-e", harness],
        check=False,
        capture_output=True,
        text=True,
    )
    assert run.returncode == 0, run.stderr or run.stdout
    assert "OPTION2_RENDER_PASS" in run.stdout


def test_visual_summary_compat_is_idempotent() -> None:
    html = web_ui.ROBERTA_WEB_UI_HTML
    assert apply_visual_summary_narrative_compat(html) == html
    assert html.count(VISUAL_SUMMARY_COMPAT_MARKER) == 1
    assert html.count(VISUAL_SUMMARY_FIDELITY_MARKER) == 1


def test_visual_summary_compat_preserves_authority_boundary() -> None:
    html = web_ui.ROBERTA_WEB_UI_HTML
    assert "fetch(apiUrl('/v1/cmis" not in html
    assert "calculateRisk" not in html
    assert "executeTrade" not in html
    assert "var _robertaVisualSummaryBaseFormatter=formatIntelligenceCard" in html
