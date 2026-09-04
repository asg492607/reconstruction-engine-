import re
from typing import Optional

PROHIBITED_PATTERNS = [
    r"\bwho (is|was) the thief\b",
    r"\bwho (is|was) guilty\b",
    r"\bwho (did|committed) (it|the theft|the crime)\b",
    r"\bis .* guilty\b",
    r"\bdid .* steal\b",
    r"\bidentify the (thief|criminal|perpetrator)\b",
    r"\bwho stole\b",
]

def check_prohibited_query(query: str) -> bool:
    q_lower = query.lower()
    for pat in PROHIBITED_PATTERNS:
        if re.search(pat, q_lower):
            return True
    return False

def get_prohibited_query_response() -> dict:
    return {
        "answer": (
            "RRE cannot determine guilt, assign culpability, or identify a suspect as the thief. "
            "The system presents traceable observations, candidate entity linkages, and evidence-constrained hypotheses. "
            "The authorized human investigator retains sole responsibility and authority for evaluating guilt and identity."
        ),
        "mode": "SYSTEM_SAFEGUARD",
        "evidence_references": [],
        "confidence_note": "N/A — Judicial and ethical safeguard enforced.",
        "uncertainty_note": "System is architecturally prohibited from making judicial determinations.",
        "disclaimer": "RRE provides evidence intelligence, not legal verdicts.",
        "is_prohibited_query": True
    }
