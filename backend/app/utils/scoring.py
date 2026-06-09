SUCCESS_TERMS = {"success", "successful", "completed", "connected", "converted", "interested", "won"}
FAILED_TERMS = {"failed", "missed", "not connected", "busy", "rejected", "no answer", "negative", "lost"}


def clamp_score(value: float) -> int:
    return int(max(0, min(100, round(value))))


def categorize_score(score: int) -> str:
    if score >= 75:
        return "Hot"
    if score >= 45:
        return "Warm"
    return "Cold"


def contains_any(value: str | None, terms: set[str]) -> bool:
    normalized = (value or "").strip().lower()
    return any(term in normalized for term in terms)


def is_successful_call(status: str | None, outcome: str | None) -> bool:
    if is_failed_call(status, outcome):
        return False
    return contains_any(status, SUCCESS_TERMS) or contains_any(outcome, SUCCESS_TERMS)


def is_failed_call(status: str | None, outcome: str | None) -> bool:
    return contains_any(status, FAILED_TERMS) or contains_any(outcome, FAILED_TERMS)
