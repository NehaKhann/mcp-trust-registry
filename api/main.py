"""
Milestone 4: web API for the MCP Trust Registry.

Wraps the exact same scanning + persistence code the CLI uses
(scanner/engine.py, scanner/db.py) behind HTTP endpoints, so the Next.js
frontend and the CLI are always looking at the same data and the same
grading logic - there is no separate "web version" of the rules.
"""

import sys
from pathlib import Path

# scanner/ uses simple script-style imports (e.g. "import rules"), the same
# way scan.py runs it as a CLI - so we add that folder itself to the path,
# rather than importing it as a "scanner." package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scanner"))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import db
import engine

app = FastAPI(title="MCP Trust Registry API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ScanRequest(BaseModel):
    server_name: str
    tool_name: str
    description: str


@app.get("/api/leaderboard")
def leaderboard():
    return db.get_leaderboard()


@app.get("/api/history/{server_name}/{tool_name}")
def history(server_name: str, tool_name: str):
    rows = db.get_history(server_name, tool_name)
    if not rows:
        raise HTTPException(status_code=404, detail="No scans found for this server/tool")
    return rows


@app.post("/api/scan")
def scan(req: ScanRequest):
    previous = db.get_latest_scan(req.server_name, req.tool_name)

    rule_result, llm_result, final_grade = engine.run_scan(req.description)

    scan_id = db.save_scan(
        req.server_name, req.tool_name, req.description,
        rule_result, llm_result, final_grade,
    )

    return {
        "scan_id": scan_id,
        "server_name": req.server_name,
        "tool_name": req.tool_name,
        "description": req.description,
        "grade": final_grade,
        "rule_result": rule_result,
        "llm_result": llm_result,
        "previous_grade": previous["grade"] if previous else None,
        "grade_changed": previous is not None and previous["grade"] != final_grade,
    }


@app.get("/api/health")
def health():
    return {"status": "ok"}
