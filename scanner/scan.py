"""
CLI: scan a single MCP tool description with both engines, save the result
to the registry, and print a combined trust report.

Usage:
    python scan.py ../samples/clean_calculator.json
    python scan.py ../samples/poisoned_calculator.json
    python scan.py ../samples/scope_creep_notes.json

Design note: the rule-based score and the LLM's judgment are shown
SEPARATELY, never blended into one fake number. A recruiter (or a real
user) should be able to see exactly which parts of the verdict are
deterministic code and which parts are the model's opinion.

Milestone 2 adds persistence: every scan is saved, and if this exact
server+tool was scanned before, a grade change is flagged automatically --
this is what would catch a "rug pull" (a server that behaves well at
first, then turns malicious in a later version).
"""

import json
import sys
from datetime import datetime, timezone

import rules
import llm_check
import db


def load_tool(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def grade(rule_score: int, llm_risk: str) -> str:
    llm_penalty = {"low": 0, "medium": 25, "high": 45, "unknown": 15}.get(llm_risk, 15)
    combined = min(rule_score + llm_penalty, 100)
    if combined >= 70:
        return "F"
    if combined >= 45:
        return "C"
    if combined >= 20:
        return "B"
    return "A"


def time_ago(iso_timestamp: str) -> str:
    then = datetime.fromisoformat(iso_timestamp)
    delta = datetime.now(timezone.utc) - then
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return f"{seconds}s ago"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    if seconds < 86400:
        return f"{seconds // 3600}h ago"
    return f"{seconds // 86400}d ago"


def print_report(tool: dict, rule_result: dict, llm_result: dict,
                  final_grade: str, previous: dict | None):
    print("=" * 60)
    print(f"  {tool['server_name']}  ->  {tool['tool_name']}")
    print("=" * 60)
    print(f"\nDeclared description:\n  \"{tool['description']}\"\n")

    print("--- Rule-based engine (deterministic) ---")
    print(f"  Risk score: {rule_result['risk_score']}/100")
    if rule_result["flags"]:
        for f in rule_result["flags"]:
            print(f"  [!] {f['reason']}")
    else:
        print("  No known-dangerous patterns matched.")

    print("\n--- AI engine (semantic judgment) ---")
    if "error" in llm_result:
        print(f"  [X] {llm_result['error']}")
    else:
        print(f"  Risk level: {llm_result['risk_level']}")
        print(f"  Targets the AI model, not the human? {llm_result['targets_the_model']}")
        if llm_result["flagged_phrases"]:
            print("  Flagged phrases:")
            for p in llm_result["flagged_phrases"]:
                print(f"    - \"{p}\"")
        print(f"  Reasoning: {llm_result['reasoning']}")

    print(f"\n{'=' * 60}")
    print(f"  TRUST GRADE: {final_grade}")

    if previous is None:
        print(f"  (first scan of this server/tool -- saved to registry)")
    elif previous["grade"] != final_grade:
        direction = "got WORSE" if final_grade > previous["grade"] else "got better"
        print(f"  *** GRADE CHANGED: {previous['grade']} -> {final_grade} ({direction}) ***")
        print(f"  Previous scan was {time_ago(previous['scanned_at'])}.")
        print(f"  This is exactly the pattern that catches a \"rug pull\":")
        print(f"    a server behaving differently than it did last time it was checked.")
    else:
        print(f"  (unchanged since last scan, {time_ago(previous['scanned_at'])})")
    print("=" * 60 + "\n")


def main():
    if len(sys.argv) != 2:
        print("Usage: python scan.py <path-to-tool-description.json>")
        sys.exit(1)

    tool = load_tool(sys.argv[1])
    rule_result = rules.scan_description(tool["description"])
    llm_result = llm_check.scan_description(tool["description"])
    llm_risk = llm_result.get("risk_level", "unknown") if "error" not in llm_result else "unknown"
    final_grade = grade(rule_result["risk_score"], llm_risk)

    previous = db.get_latest_scan(tool["server_name"], tool["tool_name"])
    db.save_scan(tool["server_name"], tool["tool_name"], tool["description"],
                 rule_result, llm_result, final_grade)

    print_report(tool, rule_result, llm_result, final_grade, previous)


if __name__ == "__main__":
    main()
