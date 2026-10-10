from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import AnalysisResult


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, path: str | Path = ":memory:") -> None:
        self.connection = sqlite3.connect(str(path), check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS analyses (
              analysis_id TEXT PRIMARY KEY,
              fingerprint TEXT NOT NULL UNIQUE,
              verdict TEXT NOT NULL,
              payload TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS audit_events (
              event_id INTEGER PRIMARY KEY AUTOINCREMENT,
              analysis_id TEXT NOT NULL,
              event_type TEXT NOT NULL,
              actor TEXT NOT NULL,
              reason TEXT,
              payload TEXT NOT NULL,
              created_at TEXT NOT NULL,
              FOREIGN KEY(analysis_id) REFERENCES analyses(analysis_id)
            );
            """
        )

    def save_analysis(self, result: AnalysisResult) -> None:
        payload = json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True)
        with self.connection:
            inserted = self.connection.execute(
                "INSERT OR IGNORE INTO analyses VALUES (?, ?, ?, ?, ?)",
                (result.analysis_id, result.fingerprint, result.verdict, payload, _now()),
            )
            if inserted.rowcount:
                self.connection.execute(
                    "INSERT INTO audit_events (analysis_id, event_type, actor, reason, payload, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (result.analysis_id, "analysis.created", "system", None, "{}", _now()),
                )

    def close(self) -> None:
        self.connection.close()

    def __del__(self) -> None:  # pragma: no cover - interpreter cleanup
        connection = getattr(self, "connection", None)
        if connection is not None:
            connection.close()

    def get_analysis(self, analysis_id: str) -> dict[str, Any] | None:
        row = self.connection.execute(
            "SELECT payload FROM analyses WHERE analysis_id = ?", (analysis_id,)
        ).fetchone()
        return json.loads(row["payload"]) if row else None

    def approve(self, analysis_id: str, actor: str, reason: str, *, break_glass: bool = False) -> None:
        row = self.connection.execute(
            "SELECT verdict FROM analyses WHERE analysis_id = ?", (analysis_id,)
        ).fetchone()
        if row is None:
            raise KeyError("analysis not found")
        if row["verdict"] == "BLOCK" and not break_glass:
            raise PermissionError("BLOCK requires explicit break-glass approval")
        if not reason.strip():
            raise ValueError("approval reason is required")
        event_type = "approval.break_glass" if break_glass else "approval.granted"
        with self.connection:
            self.connection.execute(
                "INSERT INTO audit_events (analysis_id, event_type, actor, reason, payload, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (analysis_id, event_type, actor, reason, "{}", _now()),
            )

    def record_outcome(self, analysis_id: str, actor: str, outcome: str) -> None:
        if outcome not in {"success", "rollback", "incident"}:
            raise ValueError("outcome must be success, rollback or incident")
        if self.get_analysis(analysis_id) is None:
            raise KeyError("analysis not found")
        with self.connection:
            self.connection.execute(
                "INSERT INTO audit_events (analysis_id, event_type, actor, reason, payload, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (analysis_id, "deployment.outcome", actor, None, json.dumps({"outcome": outcome}), _now()),
            )

    def timeline(self, analysis_id: str) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT event_type, actor, reason, payload, created_at FROM audit_events WHERE analysis_id = ? ORDER BY event_id",
            (analysis_id,),
        ).fetchall()
        return [dict(row) for row in rows]

