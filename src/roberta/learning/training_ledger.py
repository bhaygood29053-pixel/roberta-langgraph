from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Iterable
from uuid import uuid4

from .pyramid import LevelResult


LEDGER_SCHEMA_VERSION = 1


class PyramidTrainingLedger:
    """Local training/evaluation ledger.

    This store is intentionally separate from RAG, HXMP, source truth, CMIS,
    and verified-lesson retention. It records Pyramid performance only.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS pyramid_runs (
                    run_id TEXT PRIMARY KEY,
                    curriculum_id TEXT NOT NULL,
                    run_seed TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('active','failed','mastered')),
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    highest_level_passed INTEGER NOT NULL DEFAULT 0 CHECK(highest_level_passed BETWEEN 0 AND 20)
                );

                CREATE TABLE IF NOT EXISTS level_results (
                    run_id TEXT NOT NULL,
                    level INTEGER NOT NULL CHECK(level BETWEEN 1 AND 20),
                    result_json TEXT NOT NULL,
                    passed INTEGER NOT NULL CHECK(passed IN (0,1)),
                    accuracy REAL NOT NULL,
                    integrity_accuracy REAL NOT NULL,
                    boss_passed INTEGER NOT NULL CHECK(boss_passed IN (0,1)),
                    critical_failures INTEGER NOT NULL,
                    recorded_at TEXT NOT NULL,
                    PRIMARY KEY(run_id, level),
                    FOREIGN KEY(run_id) REFERENCES pyramid_runs(run_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS failure_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    level INTEGER NOT NULL CHECK(level BETWEEN 1 AND 20),
                    failure_code TEXT NOT NULL,
                    count INTEGER NOT NULL CHECK(count > 0),
                    recorded_at TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES pyramid_runs(run_id) ON DELETE CASCADE
                );
                """
            )
            db.execute(
                "INSERT OR REPLACE INTO metadata(key, value) VALUES('schema_version', ?)",
                (str(LEDGER_SCHEMA_VERSION),),
            )

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def start_run(self, curriculum_id: str, run_seed: str | int, run_id: str | None = None) -> str:
        curriculum_id = curriculum_id.strip()
        if not curriculum_id:
            raise ValueError("curriculum_id is required")
        run_id = run_id or f"rp_{uuid4().hex}"
        with self._connect() as db:
            active = db.execute(
                "SELECT run_id FROM pyramid_runs WHERE curriculum_id=? AND status='active'",
                (curriculum_id,),
            ).fetchone()
            if active is not None:
                raise ValueError(f"curriculum already has an active run: {active['run_id']}")
            db.execute(
                """
                INSERT INTO pyramid_runs(run_id, curriculum_id, run_seed, status, started_at)
                VALUES(?,?,?,?,?)
                """,
                (run_id, curriculum_id, str(run_seed), "active", self._now()),
            )
        return run_id

    def record_level_result(self, run_id: str, result: LevelResult) -> None:
        payload = json.dumps(asdict(result), sort_keys=True, separators=(",", ":"))
        now = self._now()
        with self._connect() as db:
            run = db.execute("SELECT * FROM pyramid_runs WHERE run_id=?", (run_id,)).fetchone()
            if run is None:
                raise ValueError("unknown run_id")
            if run["status"] != "active":
                raise ValueError("cannot record a level result for a completed run")
            expected_level = int(run["highest_level_passed"]) + 1
            if result.level != expected_level:
                raise ValueError(f"expected level {expected_level}, received {result.level}")

            db.execute(
                """
                INSERT INTO level_results(
                    run_id, level, result_json, passed, accuracy, integrity_accuracy,
                    boss_passed, critical_failures, recorded_at
                ) VALUES(?,?,?,?,?,?,?,?,?)
                """,
                (
                    run_id,
                    result.level,
                    payload,
                    int(result.passed),
                    result.accuracy,
                    result.integrity_accuracy,
                    int(result.boss_passed),
                    result.critical_failures,
                    now,
                ),
            )

            if result.passed and result.level < 20:
                db.execute(
                    "UPDATE pyramid_runs SET highest_level_passed=? WHERE run_id=?",
                    (result.level, run_id),
                )
            elif result.passed and result.level == 20:
                db.execute(
                    """
                    UPDATE pyramid_runs
                    SET highest_level_passed=20, status='mastered', ended_at=?
                    WHERE run_id=?
                    """,
                    (now, run_id),
                )
            else:
                db.execute(
                    "UPDATE pyramid_runs SET status='failed', ended_at=? WHERE run_id=?",
                    (now, run_id),
                )

    def record_failures(self, run_id: str, level: int, failures: dict[str, int]) -> None:
        now = self._now()
        rows = [(run_id, level, code, count, now) for code, count in failures.items() if count > 0]
        if not rows:
            return
        with self._connect() as db:
            if db.execute("SELECT 1 FROM pyramid_runs WHERE run_id=?", (run_id,)).fetchone() is None:
                raise ValueError("unknown run_id")
            db.executemany(
                """
                INSERT INTO failure_events(run_id, level, failure_code, count, recorded_at)
                VALUES(?,?,?,?,?)
                """,
                rows,
            )

    def summary(self, curriculum_id: str | None = None) -> dict[str, object]:
        where = ""
        params: tuple[object, ...] = ()
        if curriculum_id is not None:
            where = " WHERE curriculum_id=?"
            params = (curriculum_id,)

        with self._connect() as db:
            runs = db.execute(
                f"SELECT * FROM pyramid_runs{where} ORDER BY started_at DESC", params
            ).fetchall()
            run_ids = [row["run_id"] for row in runs]
            if not run_ids:
                return {
                    "schema_version": LEDGER_SCHEMA_VERSION,
                    "run_count": 0,
                    "mastered_runs": 0,
                    "highest_level": 0,
                    "latest_run": None,
                    "failure_modes": [],
                    "level_scores": [],
                }

            placeholders = ",".join("?" for _ in run_ids)
            failures = db.execute(
                f"""
                SELECT failure_code, SUM(count) AS total
                FROM failure_events
                WHERE run_id IN ({placeholders})
                GROUP BY failure_code
                ORDER BY total DESC, failure_code
                """,
                run_ids,
            ).fetchall()
            scores = db.execute(
                f"""
                SELECT run_id, level, accuracy, passed, recorded_at
                FROM level_results
                WHERE run_id IN ({placeholders})
                ORDER BY recorded_at
                """,
                run_ids,
            ).fetchall()
            latest = dict(runs[0])
            return {
                "schema_version": LEDGER_SCHEMA_VERSION,
                "run_count": len(runs),
                "mastered_runs": sum(1 for row in runs if row["status"] == "mastered"),
                "highest_level": max(int(row["highest_level_passed"]) for row in runs),
                "latest_run": latest,
                "failure_modes": [dict(row) for row in failures],
                "level_scores": [dict(row) for row in scores],
            }

    def run_history(self, curriculum_id: str | None = None) -> list[dict[str, object]]:
        query = "SELECT * FROM pyramid_runs"
        params: tuple[object, ...] = ()
        if curriculum_id is not None:
            query += " WHERE curriculum_id=?"
            params = (curriculum_id,)
        query += " ORDER BY started_at DESC"
        with self._connect() as db:
            return [dict(row) for row in db.execute(query, params).fetchall()]
