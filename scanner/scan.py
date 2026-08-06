"""
Milestone 1 CLI: scan a single MCP tool description with both engines and
print a combined trust report.

Usage:
    python scan.py ../samples/clean_calculator.json
    python scan.py ../samples/poisoned_calculator.json
    python scan.py ../samples/scope_creep_notes.json

Design note: the rule-based score and the LLM's judgment are shown
SEPARATELY, never blended into one fake number. A recruiter (or a real
user) should be able to see exactly which parts of the verdict are
deterministic code and which parts are the model's opinion.
"""

import json
import sys

import rules
import llm_check


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


def print_report(tool: dict, rule_result: dict, llm_result: dict):
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
        llm_risk = "unknown"
    else:
        llm_risk = llm_result["risk_level"]
        print(f"  Risk level: {llm_result['risk_level']}")
        print(f"  Targets the AI model, not the human? {llm_result['targets_the_model']}")
        if llm_result["flagged_phrases"]:
            print("  Flagged phrases:")
            for p in llm_result["flagged_phrases"]:
                print(f"    - \"{p}\"")
        print(f"  Reasoning: {llm_result['reasoning']}")

    final_grade = grade(rule_result["risk_score"], llm_risk)
    print(f"\n{'=' * 60}")
    print(f"  TRUST GRADE: {final_grade}")
    print("=" * 60 + "\n")


def main():
    if len(sys.argv) != 2:
        print("Usage: python scan.py <path-to-tool-description.json>")
        sys.exit(1)

    tool = load_tool(sys.argv[1])
    rule_result = rules.scan_description(tool["description"])
    llm_result = llm_check.scan_description(tool["description"])
    print_report(tool, rule_result, llm_result)


if __name__ == "__main__":
    main()
