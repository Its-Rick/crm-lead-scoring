import json
from decimal import Decimal
from typing import Any


POSITIVE_LABELS = {"positive", "pos", "happy", "good", "interested", "satisfied"}
NEGATIVE_LABELS = {"negative", "neg", "angry", "bad", "unhappy", "frustrated", "churn"}


def coerce_json(value: Any) -> Any:
    if value is None or isinstance(value, dict | list):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def normalize_sentiment(value: Any) -> float:
    data = coerce_json(value)
    raw = _find_sentiment_value(data)
    if raw is None:
        return 0.0
    if isinstance(raw, Decimal):
        raw = float(raw)
    if isinstance(raw, int | float):
        if raw > 1:
            return max(-1.0, min(1.0, raw / 100))
        return max(-1.0, min(1.0, float(raw)))
    if isinstance(raw, str):
        lowered = raw.strip().lower()
        if lowered in POSITIVE_LABELS:
            return 1.0
        if lowered in NEGATIVE_LABELS:
            return -1.0
        if lowered in {"neutral", "mixed"}:
            return 0.0
        try:
            return normalize_sentiment(float(lowered))
        except ValueError:
            return 0.0
    return 0.0


def _find_sentiment_value(data: Any) -> Any:
    if isinstance(data, dict):
        for key in ("score", "sentiment_score", "sentiment", "label", "overall", "polarity"):
            if key in data:
                return data[key]
        for value in data.values():
            nested = _find_sentiment_value(value)
            if nested is not None:
                return nested
    if isinstance(data, list):
        values = [_find_sentiment_value(item) for item in data]
        numeric = [float(v) for v in values if isinstance(v, int | float | Decimal)]
        if numeric:
            return sum(numeric) / len(numeric)
        return next((v for v in values if v is not None), None)
    return data

