import re
from typing import List, Tuple


class SafetyGuardrail:
    """Enforces prompt safety, disclaimer requirements, and prevents execution of trading actions."""

    DISALLOWED_PROMPT_PATTERNS = [
        re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+instructions", re.IGNORECASE),
        re.compile(r"you\s+are\s+now\s+dan", re.IGNORECASE),
        re.compile(r"reveal\s+(api\s+key|secret|password|token)", re.IGNORECASE),
        re.compile(r"(execute|place)\s+(.*?)(trade|order|buy|sell)", re.IGNORECASE),
    ]

    INVESTMENT_ADVICE_PATTERNS = [
        re.compile(r"should\s+i\s+(buy|sell|short|hold)", re.IGNORECASE),
        re.compile(r"give\s+me\s+a\s+(buy|sell)\s+recommendation", re.IGNORECASE),
        re.compile(r"is\s+it\s+a\s+good\s+time\s+to\s+invest", re.IGNORECASE),
        re.compile(r"guaranteed\s+(profit|return)", re.IGNORECASE),
    ]

    @classmethod
    def check_input_safety(cls, question: str) -> Tuple[bool, str]:
        for pattern in cls.DISALLOWED_PROMPT_PATTERNS:
            if pattern.search(question):
                return False, "Cannot execute requested operation. Input flagged by safety guardrail: trading actions, order executions, and prompt injection attempts are unsupported."
        return True, ""

    @classmethod
    def is_investment_advice_request(cls, question: str) -> bool:
        for pattern in cls.INVESTMENT_ADVICE_PATTERNS:
            if pattern.search(question):
                return True
        return False
