"""
Shared scanning logic used by BOTH the CLI (scan.py) and the web API
(api/main.py), so there is exactly one place that defines what a scan
actually does -- no risk of the CLI and the API silently disagreeing.
"""

import rules
import llm_check


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


def run_scan(description: str):
    """Runs both engines on a description and returns
    (rule_result, llm_result, final_grade)."""
    rule_result = rules.scan_description(description)
    llm_result = llm_check.scan_description(description)
    llm_risk = llm_result.get("risk_level", "unknown") if "error" not in llm_result else "unknown"
    final_grade = grade(rule_result["risk_score"], llm_risk)
    return rule_result, llm_result, final_grade
