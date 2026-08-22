from __future__ import annotations

import argparse
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sqlite3
from urllib.parse import parse_qs, urlparse


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8770


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
                "scores": [],
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
        return {
            "run_count": len(runs),
            "mastered_runs": sum(1 for row in runs if row["status"] == "mastered"),
            "highest_level": max(int(row["highest_level_passed"]) for row in runs),
            "latest_run": dict(runs[0]),
            "failure_modes": [dict(row) for row in failures],
            "scores": [dict(row) for row in scores],
            "runs": [dict(row) for row in runs[:20]],
        }


def _pyramid_rows(highest: int) -> str:
    rows: list[str] = []
    for level in range(20, 0, -1):
        state = "complete" if level <= highest else "locked"
        width = 28 + (20 - level) * 3.3
        rows.append(
            f'<div class="pyramid-row {state}" style="width:{width:.1f}%">'
            f'<span>L{level:02d}</span></div>'
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
            f'<div class="bar-row"><div class="bar-label">{code}</div>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{width:.1f}%"></div></div>'
            f'<div class="bar-value">{total}</div></div>'
        )
    return "".join(items)


def _score_svg(scores: list[dict[str, object]]) -> str:
    if not scores:
        return '<p class="muted">No level scores recorded yet.</p>'
    recent = scores[-30:]
    width, height, padding = 640, 220, 28
    if len(recent) == 1:
        xs = [width / 2]
    else:
        xs = [padding + i * (width - 2 * padding) / (len(recent) - 1) for i in range(len(recent))]
    ys = [height - padding - float(item["accuracy"]) * (height - 2 * padding) for item in recent]
    points = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    circles = "".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4"><title>Level {item["level"]}: {float(item["accuracy"])*100:.1f}%</title></circle>'
        for x, y, item in zip(xs, ys, recent)
    )
    return (
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Recent level accuracy">'
        f'<line x1="{padding}" y1="{height-padding}" x2="{width-padding}" y2="{height-padding}" />'
        f'<line x1="{padding}" y1="{padding}" x2="{padding}" y2="{height-padding}" />'
        f'<polyline points="{points}" />{circles}</svg>'
    )


def render_dashboard(data: dict[str, object], db_path: Path) -> str:
    latest = data.get("latest_run") or {}
    highest = int(data.get("highest_level", 0))
    status = escape(str(latest.get("status", "no runs"))) if isinstance(latest, dict) else "no runs"
    curriculum = escape(str(latest.get("curriculum_id", "—"))) if isinstance(latest, dict) else "—"
    runs = data.get("runs", [])
    history_rows = "".join(
        "<tr>"
        f"<td>{escape(str(row['run_id']))}</td>"
        f"<td>{escape(str(row['curriculum_id']))}</td>"
        f"<td>{escape(str(row['status']))}</td>"
        f"<td>{int(row['highest_level_passed'])}</td>"
        f"<td>{escape(str(row['started_at']))}</td>"
        "</tr>"
        for row in runs
    ) or '<tr><td colspan="5" class="muted">No runs recorded.</td></tr>'

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Roberta Learning Command Center</title>
<style>
:root{{--bg:#0b1020;--panel:#151c31;--panel2:#10172a;--text:#edf2ff;--muted:#9aa6c2;--accent:#70a5ff;--good:#55d187;--line:#28334e;}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--text);font-family:Inter,system-ui,sans-serif}}
main{{max-width:1280px;margin:auto;padding:28px}} h1{{margin:0 0 5px;font-size:30px}} h2{{font-size:18px;margin:0 0 18px}}
.sub{{color:var(--muted);margin-bottom:24px}} .grid{{display:grid;grid-template-columns:repeat(12,1fr);gap:16px}}
.card{{background:linear-gradient(180deg,var(--panel),var(--panel2));border:1px solid var(--line);border-radius:16px;padding:18px}}
.metric{{grid-column:span 3}} .metric b{{display:block;font-size:30px;margin-top:8px}} .metric span,.muted{{color:var(--muted)}}
.pyramid-card{{grid-column:span 5}} .chart-card{{grid-column:span 7}} .failure-card{{grid-column:span 6}} .history-card{{grid-column:span 6}}
.pyramid{{display:flex;flex-direction:column;align-items:center;gap:3px;min-height:370px;justify-content:center}}
.pyramid-row{{height:14px;border-radius:4px;display:flex;justify-content:center;align-items:center;font-size:9px;font-weight:800;transition:.2s}}
.pyramid-row.complete{{background:var(--good);color:#07130d}} .pyramid-row.locked{{background:#26314b;color:#7f8aa5}}
.bar-row{{display:grid;grid-template-columns:150px 1fr 44px;gap:10px;align-items:center;margin:11px 0;font-size:12px}}
.bar-track{{height:11px;background:#26314b;border-radius:999px;overflow:hidden}} .bar-fill{{height:100%;background:var(--accent)}} .bar-value{{text-align:right}}
svg{{width:100%;height:260px;background:#0c1325;border-radius:12px}} svg line{{stroke:#3b4866;stroke-width:1}} svg polyline{{fill:none;stroke:var(--accent);stroke-width:3}} svg circle{{fill:var(--good)}}
table{{width:100%;border-collapse:collapse;font-size:12px}} th,td{{text-align:left;padding:9px 7px;border-bottom:1px solid var(--line)}} th{{color:var(--muted)}}
.code{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11px;color:var(--muted)}}
@media(max-width:850px){{.metric{{grid-column:span 6}} .pyramid-card,.chart-card,.failure-card,.history-card{{grid-column:1/-1}}}}
</style>
</head>
<body><main>
<h1>Roberta Learning Command Center</h1>
<div class="sub">Read-only Pyramid training dashboard · ledger <span class="code">{escape(str(db_path))}</span></div>
<section class="grid">
<div class="card metric"><span>Highest level</span><b>{highest}/20</b></div>
<div class="card metric"><span>Pyramid runs</span><b>{int(data.get('run_count',0))}</b></div>
<div class="card metric"><span>Mastered runs</span><b>{int(data.get('mastered_runs',0))}</b></div>
<div class="card metric"><span>Latest status</span><b style="font-size:22px">{status}</b><span>{curriculum}</span></div>
<div class="card pyramid-card"><h2>20-Level Pyramid</h2><div class="pyramid">{_pyramid_rows(highest)}</div></div>
<div class="card chart-card"><h2>Learning curve · recent level accuracy</h2>{_score_svg(data.get('scores', []))}</div>
<div class="card failure-card"><h2>Top failure modes</h2>{_failure_bars(data.get('failure_modes', []))}</div>
<div class="card history-card"><h2>Recent runs</h2><div style="overflow:auto"><table><thead><tr><th>Run</th><th>Curriculum</th><th>Status</th><th>Highest</th><th>Started</th></tr></thead><tbody>{history_rows}</tbody></table></div></div>
</section>
</main></body></html>"""


class DashboardHandler(BaseHTTPRequestHandler):
    db_path: Path

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        curriculum = parse_qs(parsed.query).get("curriculum", [None])[0]
        try:
            data = load_dashboard_data(self.db_path, curriculum)
        except (FileNotFoundError, sqlite3.Error) as exc:
            self.send_error(503, f"Training ledger unavailable: {exc}")
            return

        if parsed.path == "/api/summary":
            body = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
        elif parsed.path in ("/", "/index.html"):
            body = render_dashboard(data, self.db_path).encode("utf-8")
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
    parser = argparse.ArgumentParser(description="Run the read-only Roberta Pyramid training dashboard")
    parser.add_argument("--db", default=".roberta/pyramid_training.sqlite3", help="Pyramid training ledger path")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    DashboardHandler.db_path = Path(args.db).resolve()
    server = ThreadingHTTPServer((args.host, args.port), DashboardHandler)
    print(f"Roberta Learning Command Center: http://{args.host}:{args.port}")
    print(f"Read-only ledger: {DashboardHandler.db_path}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
