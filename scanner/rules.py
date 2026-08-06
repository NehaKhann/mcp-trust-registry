"""
Deterministic pattern checks for MCP tool descriptions.

This file contains NO AI. It exists on purpose: an LLM can be tricked or
can miss things, so anything we can catch with a plain, predictable rule
should never depend on the model to notice it. The AI layer (llm_check.py)
only handles the fuzzy cases these patterns can't cover.
"""

import re

# Each entry: (regex pattern, human-readable reason, weight added to risk score)
SUSPICIOUS_PATTERNS = [
    (r"do not (mention|tell|inform|reveal)", "Instructs the AI to hide an action from the user", 40),
    (r"ignore (previous|prior|above|the) instructions", "Classic prompt-injection override attempt", 40),
    (r"\bsilently\b", "Requests silent/undisclosed behavior", 25),
    (r"without (the user|informing|telling|asking)", "Requests bypassing user awareness or consent", 30),
    (r"hidden field", "Asks for data to be smuggled outside the visible response", 30),
    (r"ssh|id_rsa|\.aws|private key|credentials", "References sensitive credential material", 35),
    (r"before returning|before responding", "Injects a mandatory hidden pre-step into every call", 15),
    (r"also (sync|send|upload|transmit|forward)", "Describes an undisclosed secondary data flow", 25),
    (r"clipboard|browser history", "Requests access far beyond what the tool's stated purpose needs", 25),
    (r"<important>|<system>|\[system\]", "Uses fake system/priority tags to gain extra weight with the model", 20),
]


def scan_description(text: str) -> dict:
    text_lower = text.lower()
    flags = []
    score = 0

    for pattern, reason, weight in SUSPICIOUS_PATTERNS:
        if re.search(pattern, text_lower):
            flags.append({"pattern": pattern, "reason": reason, "weight": weight})
            score += weight

    score = min(score, 100)

    return {
        "engine": "rule-based",
        "risk_score": score,
        "flags": flags,
    }
