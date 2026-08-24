from __future__ import annotations

import argparse
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import sqlite3
from string import Template
from urllib.error import URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8770
DEFAULT_ROBERTA_BASE_URL = "http://127.0.0.1:8766"
ASSET_PATH = Path(__file__).with_name("assets") / "roberta_command_center.svg"


def _read_only_connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def load_dashboard_data(path: Path, curriculum_id: str | None = None) -> dict[str, object]:
    if not path.exists():
        raise FileNotFoundError(path)
    with _read_only_connect(path) as db:
        where = ""
        params: tuple[object, ...] = ()
        if curriculum_id:
            where = " WHERE curriculum_id=?"
            params = (curriculum_id,)
        runs = db.execute(f"SELECT * FROM pyramid_runs{where} ORDER BY started_at DESC", params).fetchall()
        run_ids = [row["run_id"] for row in runs]
        if not run_ids:
            return {
                "run_count": 0,
                "mastered_runs": 0,
                "highest_level": 0,
                "latest_run": None,
                "failure_modes": [],
                "failure_event_total": 0,
                "scores": [],
                "latest_accuracy": None,
                "latest_level": None,
                "runs": [],
            }
        marks = ",".join("?" for _ in run_ids)
        failures = db.execute(
            f"""
            SELECT failure_code, SUM(count) AS total
            FROM failure_events
            WHERE run_id IN ({marks})
            GROUP BY failure_code
            ORDER BY total DESC, failure_code
            LIMIT 10
            """,
            run_ids,
        ).fetchall()
        scores = db.execute(
            f"""
            SELECT run_id, level, accuracy, passed, recorded_at
            FROM level_results
            WHERE run_id IN ({marks})
            ORDER BY recorded_at
            """,
            run_ids,
        ).fetchall()
        latest_score = dict(scores[-1]) if scores else None
        return {
            "run_count": len(runs),
            "mastered_runs": sum(1 for row in runs if row["status"] == "mastered"),
            "highest_level": max(int(row["highest_level_passed"]) for row in runs),
            "latest_run": dict(runs[0]),
            "failure_modes": [dict(row) for row in failures],
            "failure_event_total": sum(int(row["total"]) for row in failures),
            "scores": [dict(row) for row in scores],
            "latest_accuracy": float(latest_score["accuracy"]) if latest_score else None,
            "latest_level": int(latest_score["level"]) if latest_score else None,
            "runs": [dict(row) for row in runs[:20]],
        }


def _probe_roberta(base_url: str, timeout: float = 0.35) -> dict[str, object]:
    url = base_url.rstrip("/") + "/healthz"
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "roberta-learning-command-center/1"})
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read(2048).decode("utf-8", errors="replace")
            ok = 200 <= int(response.status) < 300
            detail = "healthy" if ok else f"HTTP {response.status}"
            if body:
                try:
                    payload = json.loads(body)
                    if isinstance(payload, dict):
                        detail = str(payload.get("status") or payload.get("state") or detail)
                except json.JSONDecodeError:
                    pass
            return {"status": "online" if ok else "degraded", "detail": detail, "url": url}
    except (OSError, URLError, TimeoutError) as exc:
        return {"status": "offline", "detail": type(exc).__name__, "url": url}


def _service_status(roberta_base_url: str) -> dict[str, object]:
    return {
        "dashboard": {"status": "online", "detail": "serving telemetry"},
        "ledger": {"status": "online", "detail": "read-only SQLite"},
        "roberta": _probe_roberta(roberta_base_url),
    }


def _pyramid_rows(highest: int, latest_status: str) -> str:
    rows: list[str] = []
    frontier = min(20, highest + 1) if latest_status == "active" else highest
    for level in range(20, 0, -1):
        if level <= highest:
            state, label = "complete", "MASTERED"
        elif latest_status == "active" and level == frontier:
            state, label = "frontier", "TRAINING"
        else:
            state, label = "locked", "LOCKED"
        width = min(98.0, 42 + (20 - level) * 2.85)
        rows.append(
            f'<div class="pyramid-row {state}" data-level="{level}" tabindex="0" '
            f'data-tip="Level {level} of Roberta\'s 20-level Blockchain Reasoning Pyramid." '
            f'style="width:{width:.1f}%"><span>L{level:02d}</span><small>{label}</small></div>'
        )
    return "".join(rows)


def _failure_bars(failures: list[dict[str, object]]) -> str:
    if not failures:
        return '<p class="muted">No failure events recorded yet.</p>'
    maximum = max(int(item["total"]) for item in failures) or 1
    items: list[str] = []
    for item in failures:
        total = int(item["total"])
        width = total / maximum * 100
        code = escape(str(item["failure_code"]))
        items.append(
            f'<div class="bar-row" tabindex="0" data-tip="Failure code {code}: {total} recorded event(s).">'
            f'<span>{code}</span><div class="bar-track"><div class="bar-fill" style="width:{width:.1f}%"></div></div><b>{total}</b></div>'
        )
    return "".join(items)


def _score_svg(scores: list[dict[str, object]]) -> str:
    if not scores:
        return '<p class="muted">No level scores recorded yet.</p>'
    recent = scores[-30:]
    width, height, padding = 700, 250, 30
    xs = [width / 2] if len(recent) == 1 else [padding + i * (width - 2 * padding) / (len(recent) - 1) for i in range(len(recent))]
    ys = [height - padding - float(item["accuracy"]) * (height - 2 * padding) for item in recent]
    points = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    circles = "".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5"><title>Level {item["level"]}: {float(item["accuracy"])*100:.1f}%</title></circle>'
        for x, y, item in zip(xs, ys, recent)
    )
    return f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Recent Pyramid accuracy"><polyline points="{points}" />{circles}</svg>'


def _history_rows(runs: list[dict[str, object]]) -> str:
    if not runs:
        return '<tr><td colspan="5" class="muted">No runs recorded.</td></tr>'
    return "".join(
        "<tr>"
        f"<td>{escape(str(row['run_id']))}</td>"
        f"<td>{escape(str(row['curriculum_id']))}</td>"
        f"<td><span class=\"pill {escape(str(row['status']))}\">{escape(str(row['status']))}</span></td>"
        f"<td>{int(row['highest_level_passed'])}</td>"
        f"<td>{escape(str(row['started_at']))}</td>"
        "</tr>"
        for row in runs
    )


def render_dashboard(data: dict[str, object], db_path: Path, services: dict[str, object] | None = None) -> str:
    latest = data.get("latest_run") or {}
    highest = int(data.get("highest_level", 0))
    latest_status = str(latest.get("status", "no runs")) if isinstance(latest, dict) else "no runs"
    status = escape(latest_status)
    curriculum = escape(str(latest.get("curriculum_id", "—"))) if isinstance(latest, dict) else "—"
    latest_accuracy = data.get("latest_accuracy")
    accuracy = "—" if latest_accuracy is None else f"{float(latest_accuracy) * 100:.1f}%"
    latest_level = data.get("latest_level")
    level_text = "—" if latest_level is None else f"L{int(latest_level):02d}"
    services = services or {"roberta": {"status": "unknown", "detail": "not probed"}}
    roberta = services.get("roberta") or {}
    roberta_status = escape(str(roberta.get("status", "unknown"))) if isinstance(roberta, dict) else "unknown"
    roberta_detail = escape(str(roberta.get("detail", "unknown"))) if isinstance(roberta, dict) else "unknown"

    template = Template(r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Roberta Learning Command Center</title>
<style>
:root{--bg:#02080d;--panel:rgba(5,24,33,.9);--line:rgba(57,231,255,.34);--text:#ebffff;--muted:#79a9b4;--cyan:#39e7ff;--green:#4dffb8;--amber:#ffd166;--red:#ff6f80}*{box-sizing:border-box}html,body{margin:0;background:#02080d;color:var(--text);font-family:"Segoe UI",system-ui,sans-serif}body{background-image:linear-gradient(rgba(57,231,255,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(57,231,255,.035) 1px,transparent 1px),radial-gradient(circle at 75% 8%,rgba(57,231,255,.13),transparent 30%);background-size:28px 28px,28px 28px,auto}main{max-width:1480px;margin:auto;padding:20px;position:relative;isolation:isolate}.ghost{position:absolute;z-index:-1;right:0;top:80px;width:min(48%,640px);height:690px;background:linear-gradient(90deg,#02080d,rgba(2,8,13,.12) 45%,transparent),url('/assets/roberta.svg') center top/cover no-repeat;opacity:.18;filter:saturate(.7) contrast(1.2);mask-image:linear-gradient(to bottom,transparent,#000 10%,#000 80%,transparent)}.system{font:800 9px ui-monospace,monospace;letter-spacing:.2em;color:#72eaf6;border-left:2px solid var(--cyan);padding:7px 10px;margin-bottom:12px;background:linear-gradient(90deg,rgba(57,231,255,.12),transparent 45%)}header,.card,.metric,.health-item{background:linear-gradient(150deg,rgba(7,30,41,.92),rgba(2,13,19,.95));border:1px solid var(--line);clip-path:polygon(9px 0,100% 0,100% calc(100% - 9px),calc(100% - 9px) 100%,0 100%,0 9px);box-shadow:inset 0 0 28px rgba(57,231,255,.03),0 8px 24px rgba(0,0,0,.2)}header{display:flex;align-items:center;justify-content:space-between;gap:15px;flex-wrap:wrap;padding:15px}.brand{display:flex;align-items:center;gap:15px}.avatar{width:72px;height:72px;border-radius:50%;background:url('/assets/roberta.svg') 78% 12%/290% no-repeat,#061922;border:2px solid #77f3ff;box-shadow:0 0 0 6px rgba(57,231,255,.05),0 0 30px rgba(57,231,255,.35)}h1{font:900 clamp(22px,3vw,34px) ui-monospace,monospace;letter-spacing:.08em;text-transform:uppercase;margin:0;background:linear-gradient(#fff,#8ef5ff);-webkit-background-clip:text;color:transparent}.subtitle,.muted{color:var(--muted);font-size:10px}.meta{text-align:right;color:var(--muted);font:700 10px/1.7 ui-monospace,monospace}.meta strong{color:#dffcff}.health,.metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:14px 0}.health-item{padding:11px 12px;display:flex;justify-content:space-between}.health-item span:first-child,.metric-label{font:800 9px ui-monospace,monospace;letter-spacing:.11em;color:#6be2ef}.health-state{font:900 9px ui-monospace,monospace;text-transform:uppercase}.health-state:before{content:"";display:inline-block;width:8px;height:8px;border-radius:50%;background:currentColor;box-shadow:0 0 10px currentColor;margin-right:6px}.online{color:var(--green)}.offline{color:var(--red)}.degraded{color:var(--amber)}.unknown{color:#728f98}.metric{padding:16px}.metric-value{font:900 29px ui-monospace,monospace;margin:10px 0 4px}.grid{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));gap:14px}.card{padding:17px}.pyramid-card{grid-column:span 5}.curve-card{grid-column:span 7}.failure-card{grid-column:span 5}.history-card{grid-column:span 7}.ops-card{grid-column:span 5}.boundary-card{grid-column:span 7}.head{display:flex;justify-content:space-between;gap:12px;border-bottom:1px solid rgba(57,231,255,.14);padding-bottom:11px;margin-bottom:14px}.head h2{font:900 14px ui-monospace,monospace;letter-spacing:.09em;text-transform:uppercase;color:#79effa;margin:0}.tag{font:900 8px ui-monospace,monospace;padding:5px 6px;border:1px solid var(--line);color:#95f7ff}.pyramid{display:flex;flex-direction:column;align-items:center;gap:4px}.pyramid-row{height:18px;display:flex;justify-content:space-between;align-items:center;padding:0 8px;border:1px solid rgba(57,231,255,.2);font:800 8px ui-monospace,monospace}.pyramid-row.complete{background:rgba(31,128,99,.67);border-color:rgba(77,255,184,.55)}.pyramid-row.frontier{background:rgba(8,99,119,.8);border-color:#74f3ff;box-shadow:0 0 14px rgba(57,231,255,.12)}.pyramid-row.locked{background:rgba(8,28,36,.7);color:#557983}.pyramid-row small{font-size:7px}.bar-row{display:grid;grid-template-columns:130px 1fr 40px;gap:9px;align-items:center;margin:11px 0;font:700 9px ui-monospace,monospace}.bar-track{height:8px;background:#09232d}.bar-fill{height:100%;background:linear-gradient(90deg,#08798f,#6af3ff);box-shadow:0 0 8px rgba(57,231,255,.3)}svg{width:100%;height:260px;background:rgba(1,9,14,.5);border:1px solid rgba(57,231,255,.12)}svg polyline{fill:none;stroke:#6af1fc;stroke-width:3}svg circle{fill:#4dffb8}table{width:100%;border-collapse:collapse;font-size:9px}th,td{text-align:left;padding:8px 6px;border-bottom:1px solid rgba(57,231,255,.11);white-space:nowrap}th{color:#65dce8;font:800 8px ui-monospace,monospace}.table{overflow:auto}.pill{font:900 7px ui-monospace,monospace;text-transform:uppercase}.pill.active{color:var(--cyan)}.pill.mastered{color:var(--green)}.pill.failed{color:var(--red)}.list{display:grid;gap:8px}.item{padding:10px;border:1px solid rgba(57,231,255,.18);background:rgba(3,17,24,.65);display:flex;justify-content:space-between;gap:10px}.item strong{font:800 9px ui-monospace,monospace;color:#dffcff;text-transform:uppercase}.item span{font-size:9px;color:var(--muted)}code{color:#86f4ff}[data-tip]{position:relative;cursor:help}[data-tip]:hover:after,[data-tip]:focus-visible:after{content:attr(data-tip);position:absolute;z-index:50;left:50%;bottom:calc(100% + 7px);transform:translateX(-50%);width:min(300px,calc(100vw - 30px));padding:9px 10px;background:#031219;border:1px solid #5debf8;color:#d6fcff;font:500 9px/1.45 ui-monospace,monospace;box-shadow:0 12px 28px rgba(0,0,0,.5);white-space:normal}.footer{margin-top:14px;border-top:1px solid rgba(57,231,255,.15);padding:10px;color:#608791;font:700 9px ui-monospace,monospace}@media(max-width:950px){.health,.metrics{grid-template-columns:repeat(2,1fr)}.pyramid-card,.curve-card,.failure-card,.history-card,.ops-card,.boundary-card{grid-column:1/-1}}@media(max-width:580px){main{padding:12px}.health,.metrics{grid-template-columns:1fr}.avatar{width:58px;height:58px}.meta{text-align:left}.ghost{right:-25%;width:100%;opacity:.12}.bar-row{grid-template-columns:95px 1fr 32px}}
</style></head><body><main><div class="ghost" aria-hidden="true"></div><div class="system">ROBERTA // COGNITIVE SYSTEM // LIVE READ-ONLY TELEMETRY</div>
<header><div class="brand"><div class="avatar" aria-label="Roberta avatar"></div><div><h1>Learning Command Center</h1><div class="subtitle">Blockchain Reasoning Pyramid • Training Ledger • Diagnostics</div></div></div><div class="meta">CURRICULUM <strong>$curriculum</strong><br>LEDGER <strong>$db_path</strong><br>LAST SYNC <strong id="sync">server render</strong></div></header>
<section class="health"><div class="health-item" tabindex="0" data-tip="The dashboard server is running and serving telemetry."><span>DASHBOARD</span><span class="health-state online">ONLINE</span></div><div class="health-item" tabindex="0" data-tip="The Pyramid SQLite ledger was opened read-only. Viewing this dashboard cannot mutate training state."><span>PYRAMID LEDGER</span><span class="health-state online">ONLINE</span></div><div class="health-item" tabindex="0" data-tip="This probes Roberta's real /healthz endpoint. Green means roberta-serve answered successfully."><span>ROBERTA</span><span id="robHealth" class="health-state $rob_status">$rob_status</span></div><div class="health-item" tabindex="0" data-tip="The page polls /api/summary every five seconds and reloads when training state changes."><span>TELEMETRY</span><span class="health-state online">5 SEC</span></div></section>
<section class="metrics"><div class="metric" tabindex="0" data-tip="Highest Pyramid level actually passed in the selected training ledger scope."><div class="metric-label">Highest Pyramid Level</div><div id="highest" class="metric-value">$highest / 20</div><div class="subtitle">real ledger value</div></div><div class="metric" tabindex="0" data-tip="Accuracy from the most recently recorded Pyramid level result."><div class="metric-label">Latest Accuracy</div><div class="metric-value">$accuracy</div><div class="subtitle">latest evaluated level $latest_level</div></div><div class="metric" tabindex="0" data-tip="Total number of Pyramid training runs in the current scope."><div class="metric-label">Pyramid Runs</div><div id="runs" class="metric-value">$run_count</div><div class="subtitle">$mastered_runs mastered</div></div><div class="metric" tabindex="0" data-tip="Total counts represented by the recorded top failure modes."><div class="metric-label">Failure Events</div><div class="metric-value">$failure_total</div><div class="subtitle">latest status $status</div></div></section>
<section class="grid"><article class="card pyramid-card"><div class="head"><div><h2>20-Level Pyramid</h2><div class="subtitle">Real Blockchain Reasoning Pyramid progression</div></div><span id="frontier" class="tag">HIGHEST $highest</span></div><div id="pyramid" class="pyramid">$pyramid_rows</div></article><article class="card curve-card"><div class="head"><div><h2>Learning Curve</h2><div class="subtitle">Recent level accuracy from recorded evaluations</div></div><span class="tag">$score_count RESULTS</span></div>$score_svg</article><article class="card failure-card"><div class="head"><div><h2>Top Failure Modes</h2><div class="subtitle">Weakness counts from failure_events</div></div><span class="tag">REMEDIATION INPUT</span></div>$failure_bars</article><article class="card history-card"><div class="head"><div><h2>Recent Runs</h2><div class="subtitle">Training history from pyramid_runs</div></div><span class="tag">READ ONLY</span></div><div class="table"><table><thead><tr><th>Run</th><th>Curriculum</th><th>Status</th><th>Highest</th><th>Started</th></tr></thead><tbody>$history_rows</tbody></table></div></article><article class="card ops-card"><div class="head"><div><h2>Roberta Operations</h2><div class="subtitle">Telemetry is live; training remains an explicit action</div></div><span class="tag">SAFE CONTROL</span></div><div class="list"><div class="item" tabindex="0" data-tip="Starts the accepted Pyramid exam, grading, and checkpoint loop."><div><strong>Run Pyramid training</strong><br><code>roberta-pyramid-run</code></div><span>explicit</span></div><div class="item" tabindex="0" data-tip="Turns detected weaknesses into fresh targeted practice."><div><strong>Build remediation</strong><br><code>roberta-pyramid-remediate</code></div><span>weakness loop</span></div><div class="item" tabindex="0" data-tip="Regrades historical checkpoints without regenerating Roberta's answers."><div><strong>Regrade checkpoint</strong><br><code>roberta-pyramid-regrade</code></div><span>verification</span></div></div></article><article class="card boundary-card"><div class="head"><div><h2>Learning System Boundaries</h2><div class="subtitle">Only metrics with a real backend source are shown as live</div></div><span class="tag">NO FAKE GREEN</span></div><div class="list"><div class="item" tabindex="0" data-tip="Runs, levels, scores, failures and history are live because the Pyramid ledger exposes them."><div><strong>Pyramid telemetry</strong><br><span>Connected now.</span></div><span class="online">LIVE</span></div><div class="item" tabindex="0" data-tip="RAG chunk counts, source counts, retrieval latency and coverage are not exposed by this backend yet."><div><strong>RAG telemetry</strong><br><span>No placeholder numbers are shown.</span></div><span class="degraded">PENDING</span></div><div class="item" tabindex="0" data-tip="Verified lesson retention is separately gated; Pyramid success does not automatically create durable trusted lessons."><div><strong>Verified retention</strong><br><span>Separate authority boundary.</span></div><span>SEPARATE</span></div><div class="item" tabindex="0" data-tip="Fresh blockchain facts remain under the Scout to CMIS to Provider authority path."><div><strong>CMIS / live truth</strong><br><span>Outside this training dashboard.</span></div><span>SEPARATE</span></div></div></article></section>
<div class="footer">ROBERTA HEALTH: <strong id="robDetail">$rob_detail</strong> • Dashboard API: <strong>/api/summary</strong> • Latest run: <strong>$status</strong></div>
</main><script>(function(){var rc=$run_count,hs=$highest,st='$status_js';function cls(s){return ['online','offline','degraded','unknown'].indexOf(s)>=0?s:'unknown'}function paint(h,s){var f=s==='active'?Math.min(20,h+1):h;document.querySelectorAll('.pyramid-row').forEach(function(r){var l=Number(r.dataset.level),sm=r.querySelector('small');r.classList.remove('complete','frontier','locked');if(l<=h){r.classList.add('complete');sm.textContent='MASTERED'}else if(s==='active'&&l===f){r.classList.add('frontier');sm.textContent='TRAINING'}else{r.classList.add('locked');sm.textContent='LOCKED'}})}function poll(){fetch('/api/summary',{cache:'no-store'}).then(function(r){if(!r.ok)throw Error(r.status);return r.json()}).then(function(d){var rob=(d.services||{}).roberta||{},rs=String(rob.status||'unknown'),el=document.getElementById('robHealth');el.className='health-state '+cls(rs);el.textContent=rs.toUpperCase();document.getElementById('robDetail').textContent=String(rob.detail||'unknown');document.getElementById('sync').textContent=new Date().toLocaleTimeString();var latest=d.latest_run||{},ns=String(latest.status||'no runs'),nh=Number(d.highest_level||0),nr=Number(d.run_count||0);document.getElementById('highest').textContent=nh+' / 20';document.getElementById('runs').textContent=String(nr);document.getElementById('frontier').textContent='HIGHEST '+nh;paint(nh,ns);if(nr!==rc||nh!==hs||ns!==st)location.reload()}).catch(function(){document.getElementById('sync').textContent='poll failed'})}paint(hs,st);setInterval(poll,5000);poll()})();</script></body></html>''')
    return template.safe_substitute(
        curriculum=curriculum,
        db_path=escape(str(db_path)),
        rob_status=roberta_status,
        rob_detail=roberta_detail,
        highest=str(highest),
        accuracy=accuracy,
        latest_level=level_text,
        run_count=str(int(data.get("run_count", 0))),
        mastered_runs=str(int(data.get("mastered_runs", 0))),
        failure_total=str(int(data.get("failure_event_total", 0))),
        status=status,
        status_js=status.replace("'", "\\'"),
        pyramid_rows=_pyramid_rows(highest, latest_status),
        score_count=str(len(data.get("scores", []))),
        score_svg=_score_svg(data.get("scores", [])),
        failure_bars=_failure_bars(data.get("failure_modes", [])),
        history_rows=_history_rows(data.get("runs", [])),
    )


class DashboardHandler(BaseHTTPRequestHandler):
    db_path: Path
    roberta_base_url: str = DEFAULT_ROBERTA_BASE_URL

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/assets/roberta.svg":
            try:
                body = ASSET_PATH.read_bytes()
            except OSError as exc:
                self.send_error(404, f"Roberta portrait unavailable: {exc}")
                return
            self.send_response(200)
            self.send_header("Content-Type", "image/svg+xml; charset=utf-8")
            self.send_header("Cache-Control", "public, max-age=3600")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        curriculum = parse_qs(parsed.query).get("curriculum", [None])[0]
        try:
            data = load_dashboard_data(self.db_path, curriculum)
        except (FileNotFoundError, sqlite3.Error) as exc:
            self.send_error(503, f"Training ledger unavailable: {exc}")
            return

        services = _service_status(self.roberta_base_url)
        if parsed.path == "/api/summary":
            payload = dict(data)
            payload["services"] = services
            body = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
        elif parsed.path == "/healthz":
            body = json.dumps(
                {"status": "ok", "ledger": "online", "roberta": (services.get("roberta") or {}).get("status", "unknown")},
                sort_keys=True,
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
        elif parsed.path in ("/", "/index.html"):
            body = render_dashboard(data, self.db_path, services).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
        else:
            self.send_error(404)
            return
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the read-only Roberta Pyramid Learning Command Center")
    parser.add_argument("--db", default=".roberta/pyramid_training.sqlite3", help="Pyramid training ledger path")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument(
        "--roberta-base-url",
        default=os.getenv("ROBERTA_BASE_URL", DEFAULT_ROBERTA_BASE_URL),
        help="Roberta HTTP bridge used for /healthz diagnostics",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    DashboardHandler.db_path = Path(args.db).resolve()
    DashboardHandler.roberta_base_url = str(args.roberta_base_url).rstrip("/")
    server = ThreadingHTTPServer((args.host, args.port), DashboardHandler)
    print(f"Roberta Learning Command Center: http://{args.host}:{args.port}")
    print(f"Read-only ledger: {DashboardHandler.db_path}")
    print(f"Roberta health target: {DashboardHandler.roberta_base_url}/healthz")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
