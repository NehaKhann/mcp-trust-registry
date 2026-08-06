"""
Persistence layer.

SQLite for now (zero setup, ships with Python) -- swaps for Postgres later
without changing anything above this file, since every caller only ever
talks to the functions below, never to raw SQL directly.

Milestone 3 adds two columns onto the original schema rather than a new
table: "source" (manual | docker-sandbox) and "behavior_flags" (JSON list
of anything the sandbox caught happening that the description never
mentioned). Existing rows just get source='manual', behavior_flags=NULL --
a scan that was never run through the sandbox has no behavioral opinion,
which is honest: absence of evidence isn't evidence of good behavior.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "registry.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    server_name TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    description TEXT NOT NULL,
    rule_score INTEGER NOT NULL,
    rule_flags TEXT NOT NULL,
    llm_risk_level TEXT,
    llm_targets_model TEXT,
    llm_flagged_phrases TEXT,
    llm_reasoning TEXT,
    grade TEXT NOT NULL,
    scanned_at TEXT NOT NULL
);
"""

# Additive migrations for columns introduced after the original schema.
# SQLite has no "ADD COLUMN IF NOT EXISTS", so we just try and swallow the
# "duplicate column" error on every subsequent run.
MIGRATIONS = [
    "ALTER TABLE scans ADD COLUMN source TEXT DEFAULT 'manual'",
    "ALTER TABLE scans ADD COLUMN behavior_flags TEXT",
]


def _ensure_schema(conn: sqlite3.Connection):
    conn.execute(SCHEMA)
    for migration in MIGRATIONS:
        try:
            conn.execute(migration)
        except sqlite3.OperationalError:
            pass  # column already exists
    conn.commit()


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    _ensure_schema(conn)
    return conn


def init_db():
    get_connection().close()


def get_latest_scan(server_name: str, tool_name: str) -> dict | None:
    """The most recent scan already on record for this server+tool, if any --
    used to detect a grade change ('rug pull') before we save the new one."""
    conn = get_connection()
    row = conn.execute(
        """SELECT * FROM scans WHERE server_name = ? AND tool_name = ?
           ORDER BY scanned_at DESC LIMIT 1""",
        (server_name, tool_name),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def save_scan(server_name: str, tool_name: str, description: str,
              rule_result: dict, llm_result: dict, grade: str,
              source: str = "manual", behavior_flags: list[str] | None = None) -> int:
    conn = get_connection()
    cur = conn.execute(
        """INSERT INTO scans
           (server_name, tool_name, description, rule_score, rule_flags,
            llm_risk_level, llm_targets_model, llm_flagged_phrases,
            llm_reasoning, grade, scanned_at, source, behavior_flags)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            server_name,
            tool_name,
            description,
            rule_result["risk_score"],
            json.dumps([f["reason"] for f in rule_result["flags"]]),
            llm_result.get("risk_level"),
            str(llm_result.get("targets_the_model")),
            json.dumps(llm_result.get("flagged_phrases", [])),
            llm_result.get("reasoning", ""),
            grade,
            datetime.now(timezone.utc).isoformat(),
            source,
            json.dumps(behavior_flags) if behavior_flags is not None else None,
        ),
    )
    conn.commit()
    scan_id = cur.lastrowid
    conn.close()
    return scan_id


def get_history(server_name: str = None, tool_name: str = None) -> list[dict]:
    conn = get_connection()
    if server_name and tool_name:
        rows = conn.execute(
            """SELECT * FROM scans WHERE server_name = ? AND tool_name = ?
               ORDER BY scanned_at ASC""",
            (server_name, tool_name),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM scans ORDER BY scanned_at ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_leaderboard() -> list[dict]:
    """Latest grade per distinct server+tool, plus how many times it's been scanned."""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT server_name, tool_name, grade, scanned_at, scan_count, source FROM (
            SELECT s.*,
                   ROW_NUMBER() OVER (PARTITION BY server_name, tool_name ORDER BY scanned_at DESC) AS rn,
                   COUNT(*) OVER (PARTITION BY server_name, tool_name) AS scan_count
            FROM scans s
        )
        WHERE rn = 1
        ORDER BY scanned_at DESC
        """
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
