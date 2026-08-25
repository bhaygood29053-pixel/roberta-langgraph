from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from uuid import uuid4

from .pyramid import LevelResult
from .source_mastery import SourceMasteryPlan


LEDGER_SCHEMA_VERSION = 2


class PyramidTrainingLedger:
    """Local training/evaluation ledger.

    This store is intentionally separate from RAG, HXMP, source truth, CMIS,
    and verified-lesson retention. It records Pyramid performance only.

    Schema v2 adds a source-mastery overlay. Historical ``level_results`` stay
    immutable; a frozen source plan can map those historical results to source
    stages and then record future stages whose global capability numbers are not
    necessarily contiguous.
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

                CREATE TABLE IF NOT EXISTS source_mastery_runs (
                    run_id TEXT PRIMARY KEY,
                    plan_hash TEXT NOT NULL,
                    source_key TEXT NOT NULL,
                    required_stage_count INTEGER NOT NULL CHECK(required_stage_count > 0),
                    completed_stage_count INTEGER NOT NULL DEFAULT 0 CHECK(completed_stage_count >= 0),
                    capstone_required INTEGER NOT NULL CHECK(capstone_required IN (0,1)),
                    capstone_passed INTEGER NOT NULL DEFAULT 0 CHECK(capstone_passed IN (0,1)),
                    status TEXT NOT NULL CHECK(status IN ('active','stages_complete','mastered','failed')),
                    bound_at TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES pyramid_runs(run_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS source_stage_results (
                    run_id TEXT NOT NULL,
                    stage INTEGER NOT NULL CHECK(stage > 0),
                    capability_level INTEGER NOT NULL CHECK(capability_level BETWEEN 1 AND 20),
                    plan_hash TEXT NOT NULL,
                    result_json TEXT NOT NULL,
                    passed INTEGER NOT NULL CHECK(passed IN (0,1)),
                    accuracy REAL NOT NULL,
                    integrity_accuracy REAL NOT NULL,
                    boss_passed INTEGER NOT NULL CHECK(boss_passed IN (0,1)),
                    critical_failures INTEGER NOT NULL,
                    historical_mapped INTEGER NOT NULL DEFAULT 0 CHECK(historical_mapped IN (0,1)),
                    recorded_at TEXT NOT NULL,
                    PRIMARY KEY(run_id, stage),
                    UNIQUE(run_id, capability_level),
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
        """Record a legacy/fixed-ladder result.

        The original contiguous-level invariant remains intact. Source-specific
        progression must use :meth:`record_source_stage_result` instead.
        """
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

    def preview_source_mastery_completed_stages(
        self,
        run_id: str,
        plan: SourceMasteryPlan,
    ) -> int:
        """Return the contiguous completed source-stage prefix without mutation."""
        plan.validate()
        with self._connect() as db:
            run = db.execute("SELECT * FROM pyramid_runs WHERE run_id=?", (run_id,)).fetchone()
            if run is None:
                raise ValueError("unknown run_id")
            if str(run["curriculum_id"]) != plan.curriculum_id:
                raise ValueError("source mastery plan curriculum does not match run")

            binding = db.execute(
                "SELECT * FROM source_mastery_runs WHERE run_id=?", (run_id,)
            ).fetchone()
            if binding is not None:
                if str(binding["plan_hash"]) != plan.plan_hash:
                    raise ValueError("active run is bound to a different source mastery plan")
                return int(binding["completed_stage_count"])

            completed = 0
            for stage in plan.stages:
                row = db.execute(
                    "SELECT passed FROM level_results WHERE run_id=? AND level=?",
                    (run_id, stage.capability_level),
                ).fetchone()
                if row is None or not bool(row["passed"]):
                    break
                completed = stage.stage
            return completed

    def bind_source_mastery_plan(
        self,
        run_id: str,
        plan: SourceMasteryPlan,
    ) -> dict[str, object]:
        """Bind an active run to one immutable source plan.

        Existing passed ``level_results`` are mapped only when they form the
        contiguous prefix of the frozen source plan. Their original rows and
        timestamps are not changed.
        """
        plan.validate()
        now = self._now()
        with self._connect() as db:
            run = db.execute("SELECT * FROM pyramid_runs WHERE run_id=?", (run_id,)).fetchone()
            if run is None:
                raise ValueError("unknown run_id")
            if str(run["curriculum_id"]) != plan.curriculum_id:
                raise ValueError("source mastery plan curriculum does not match run")
            if run["status"] != "active":
                raise ValueError("source mastery plan can only bind to an active run")

            binding = db.execute(
                "SELECT * FROM source_mastery_runs WHERE run_id=?", (run_id,)
            ).fetchone()
            if binding is not None:
                if str(binding["plan_hash"]) != plan.plan_hash:
                    raise ValueError("active run is already bound to a different source mastery plan")
                return dict(binding)

            db.execute(
                """
                INSERT INTO source_mastery_runs(
                    run_id, plan_hash, source_key, required_stage_count,
                    completed_stage_count, capstone_required, capstone_passed,
                    status, bound_at
                ) VALUES(?,?,?,?,?,?,?,?,?)
                """,
                (
                    run_id,
                    plan.plan_hash,
                    plan.source_key,
                    plan.required_stage_count,
                    0,
                    int(plan.source_capstone_required),
                    0,
                    "active",
                    now,
                ),
            )

            completed = 0
            for stage in plan.stages:
                historical = db.execute(
                    "SELECT * FROM level_results WHERE run_id=? AND level=?",
                    (run_id, stage.capability_level),
                ).fetchone()
                if historical is None or not bool(historical["passed"]):
                    break
                db.execute(
                    """
                    INSERT INTO source_stage_results(
                        run_id, stage, capability_level, plan_hash, result_json,
                        passed, accuracy, integrity_accuracy, boss_passed,
                        critical_failures, historical_mapped, recorded_at
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        run_id,
                        stage.stage,
                        stage.capability_level,
                        plan.plan_hash,
                        historical["result_json"],
                        historical["passed"],
                        historical["accuracy"],
                        historical["integrity_accuracy"],
                        historical["boss_passed"],
                        historical["critical_failures"],
                        1,
                        historical["recorded_at"],
                    ),
                )
                completed = stage.stage

            status = "active"
            if completed == plan.required_stage_count:
                status = "stages_complete" if plan.source_capstone_required else "mastered"
            db.execute(
                """
                UPDATE source_mastery_runs
                SET completed_stage_count=?, status=?
                WHERE run_id=?
                """,
                (completed, status, run_id),
            )
            if status == "mastered":
                db.execute(
                    "UPDATE pyramid_runs SET status='mastered', ended_at=? WHERE run_id=?",
                    (now, run_id),
                )
            row = db.execute(
                "SELECT * FROM source_mastery_runs WHERE run_id=?", (run_id,)
            ).fetchone()
            assert row is not None
            return dict(row)

    def source_mastery_progress(self, run_id: str) -> dict[str, object] | None:
        with self._connect() as db:
            binding = db.execute(
                "SELECT * FROM source_mastery_runs WHERE run_id=?", (run_id,)
            ).fetchone()
            if binding is None:
                return None
            stages = db.execute(
                """
                SELECT stage, capability_level, passed, accuracy, integrity_accuracy,
                       boss_passed, critical_failures, historical_mapped, recorded_at
                FROM source_stage_results
                WHERE run_id=?
                ORDER BY stage
                """,
                (run_id,),
            ).fetchall()
            value = dict(binding)
            value["stages"] = [dict(row) for row in stages]
            return value

    def record_source_stage_result(
        self,
        run_id: str,
        plan: SourceMasteryPlan,
        stage_number: int,
        result: LevelResult,
    ) -> dict[str, object]:
        """Record one result according to frozen source-stage order."""
        plan.validate()
        if not 1 <= stage_number <= plan.required_stage_count:
            raise ValueError("source mastery stage is outside the frozen plan")
        stage = plan.stages[stage_number - 1]
        if result.level != stage.capability_level:
            raise ValueError(
                f"source stage {stage_number} expects capability {stage.capability_level}, "
                f"received {result.level}"
            )
        payload = json.dumps(asdict(result), sort_keys=True, separators=(",", ":"))
        now = self._now()

        with self._connect() as db:
            run = db.execute("SELECT * FROM pyramid_runs WHERE run_id=?", (run_id,)).fetchone()
            if run is None:
                raise ValueError("unknown run_id")
            if run["status"] != "active":
                raise ValueError("cannot record a source stage for a completed run")
            binding = db.execute(
                "SELECT * FROM source_mastery_runs WHERE run_id=?", (run_id,)
            ).fetchone()
            if binding is None:
                raise ValueError("run is not bound to a source mastery plan")
            if str(binding["plan_hash"]) != plan.plan_hash:
                raise ValueError("source mastery plan hash does not match bound run")
            if str(binding["status"]) != "active":
                raise ValueError("source mastery stages are not accepting results")
            expected_stage = int(binding["completed_stage_count"]) + 1
            if stage_number != expected_stage:
                raise ValueError(
                    f"expected source stage {expected_stage}, received {stage_number}"
                )
            duplicate = db.execute(
                "SELECT 1 FROM level_results WHERE run_id=? AND level=?",
                (run_id, result.level),
            ).fetchone()
            if duplicate is not None:
                raise ValueError(
                    f"capability level {result.level} already has a recorded result for this run"
                )

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
            db.execute(
                """
                INSERT INTO source_stage_results(
                    run_id, stage, capability_level, plan_hash, result_json,
                    passed, accuracy, integrity_accuracy, boss_passed,
                    critical_failures, historical_mapped, recorded_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    run_id,
                    stage_number,
                    result.level,
                    plan.plan_hash,
                    payload,
                    int(result.passed),
                    result.accuracy,
                    result.integrity_accuracy,
                    int(result.boss_passed),
                    result.critical_failures,
                    0,
                    now,
                ),
            )

            if result.passed:
                completed = stage_number
                source_status = "active"
                if completed == plan.required_stage_count:
                    source_status = (
                        "stages_complete" if plan.source_capstone_required else "mastered"
                    )
                db.execute(
                    """
                    UPDATE source_mastery_runs
                    SET completed_stage_count=?, status=?
                    WHERE run_id=?
                    """,
                    (completed, source_status, run_id),
                )
                highest = max(int(run["highest_level_passed"]), result.level)
                if source_status == "mastered":
                    db.execute(
                        """
                        UPDATE pyramid_runs
                        SET highest_level_passed=?, status='mastered', ended_at=?
                        WHERE run_id=?
                        """,
                        (highest, now, run_id),
                    )
                else:
                    db.execute(
                        "UPDATE pyramid_runs SET highest_level_passed=? WHERE run_id=?",
                        (highest, run_id),
                    )
            else:
                db.execute(
                    "UPDATE source_mastery_runs SET status='failed' WHERE run_id=?",
                    (run_id,),
                )
                db.execute(
                    "UPDATE pyramid_runs SET status='failed', ended_at=? WHERE run_id=?",
                    (now, run_id),
                )

            row = db.execute(
                "SELECT * FROM source_mastery_runs WHERE run_id=?", (run_id,)
            ).fetchone()
            assert row is not None
            return dict(row)

    def mark_source_capstone_passed(self, run_id: str, plan_hash: str) -> None:
        """Finalize a source run after a separately evaluated source capstone passes."""
        now = self._now()
        with self._connect() as db:
            binding = db.execute(
                "SELECT * FROM source_mastery_runs WHERE run_id=?", (run_id,)
            ).fetchone()
            if binding is None:
                raise ValueError("run is not bound to a source mastery plan")
            if str(binding["plan_hash"]) != plan_hash:
                raise ValueError("source mastery plan hash does not match bound run")
            if str(binding["status"]) != "stages_complete":
                raise ValueError("source stages are not complete")
            if not bool(binding["capstone_required"]):
                raise ValueError("source plan does not require a capstone")
            db.execute(
                """
                UPDATE source_mastery_runs
                SET capstone_passed=1, status='mastered'
                WHERE run_id=?
                """,
                (run_id,),
            )
            db.execute(
                "UPDATE pyramid_runs SET status='mastered', ended_at=? WHERE run_id=?",
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
                    "source_mastery": None,
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
            source_binding = db.execute(
                "SELECT * FROM source_mastery_runs WHERE run_id=?",
                (latest["run_id"],),
            ).fetchone()
            return {
                "schema_version": LEDGER_SCHEMA_VERSION,
                "run_count": len(runs),
                "mastered_runs": sum(1 for row in runs if row["status"] == "mastered"),
                "highest_level": max(int(row["highest_level_passed"]) for row in runs),
                "latest_run": latest,
                "failure_modes": [dict(row) for row in failures],
                "level_scores": [dict(row) for row in scores],
                "source_mastery": dict(source_binding) if source_binding is not None else None,
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
