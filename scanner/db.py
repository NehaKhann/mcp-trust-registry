"""
Persistence layer.

Postgres, connected via DATABASE_URL. Locally that points at the Docker
container in docker-compose.yml (docker compose up -d); deployed, it
points at a real hosted Postgres (Neon free tier) instead - same schema,
same SQL, same functions below. No local/deployed code branch here, unlike
the LLM provider split in llm_check.py: that genuinely needs two
implementations because Ollama and Groq are different APIs, whereas this
is identical SQL either way, just a different connection string.

Every caller only ever talks to the functions below, never to raw SQL
directly - that boundary is what let this move from SQLite to Postgres
without touching scan.py, scan_live.py, scan_package.py, history.py, or
api/main.py at all.

Milestone 3 added two columns onto the original schema rather than a new
table: "source" (manual | docker-sandbox) and "behavior_flags" (JSON list
of anything the sandbox caught happening that the description never
mentioned). Existing rows just get source='manual', behavior_flags=NULL --
a scan that was never run through the sandbox has no behavioral opinion,
which is honest: absence of evidence isn't evidence of good behavior.
"""

import json
import os
from datetime import datetime, timezone

import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/mcp_registry"
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS scans (
    id SERIAL PRIMARY KEY,
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
# Postgres supports IF NOT EXISTS directly, unlike SQLite - no try/except
# dance needed here.
MIGRATIONS = [
    "ALTER TABLE scans ADD COLUMN IF NOT EXISTS source TEXT DEFAULT 'manual'",
    "ALTER TABLE scans ADD COLUMN IF NOT EXISTS behavior_flags TEXT",
]


def _ensure_schema(conn: psycopg.Connection):
    conn.execute(SCHEMA)
    for migration in MIGRATIONS:
        conn.execute(migration)
    conn.commit()


def get_connection() -> psycopg.Connection:
    conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    _ensure_schema(conn)
    return conn


def init_db():
    get_connection().close()


def get_latest_scan(server_name: str, tool_name: str) -> dict | None:
    """The most recent scan already on record for this server+tool, if any --
    used to detect a grade change ('rug pull') before we save the new one."""
    conn = get_connection()
    row = conn.execute(
        """SELECT * FROM scans WHERE server_name = %s AND tool_name = %s
           ORDER BY scanned_at DESC LIMIT 1""",
        (server_name, tool_name),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def save_scan(server_name: str, tool_name: str, description: str,
              rule_result: dict, llm_result: dict, grade: str,
              source: str = "manual", behavior_flags: list[str] | None = None) -> int:
    conn = get_connection()
    row = conn.execute(
        """INSERT INTO scans
           (server_name, tool_name, description, rule_score, rule_flags,
            llm_risk_level, llm_targets_model, llm_flagged_phrases,
            llm_reasoning, grade, scanned_at, source, behavior_flags)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
           RETURNING id""",
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
    ).fetchone()
    conn.commit()
    scan_id = row["id"]
    conn.close()
    return scan_id


def get_history(server_name: str = None, tool_name: str = None) -> list[dict]:
    conn = get_connection()
    if server_name and tool_name:
        rows = conn.execute(
            """SELECT * FROM scans WHERE server_name = %s AND tool_name = %s
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
        ) ranked
        WHERE rn = 1
        ORDER BY scanned_at DESC
        """
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
