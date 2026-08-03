"""Deterministic helpers for baseline-versus-quantized output comparison."""

from __future__ import annotations

import re
from collections import Counter
from statistics import mean
from typing import Iterable, Mapping


def tokens(text: str) -> list[str]:
    return re.findall(r"\w+|[^\w\s]", text.casefold())


def token_f1(reference: str, candidate: str) -> float:
    left, right = Counter(tokens(reference)), Counter(tokens(candidate))
    if not left and not right:
        return 1.0
    overlap = sum((left & right).values())
    precision = overlap / sum(right.values()) if right else 0.0
    recall = overlap / sum(left.values()) if left else 0.0
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def exact_match(reference: str, candidate: str) -> float:
    normalize = lambda value: " ".join(value.casefold().split())
    return float(normalize(reference) == normalize(candidate))


def compare_outputs(
    baseline: Mapping[str, str], quantized: Mapping[str, str], required_ids: Iterable[str] | None = None
) -> dict[str, object]:
    ids = sorted(required_ids if required_ids is not None else set(baseline) | set(quantized))
    missing_baseline = sorted(set(ids) - set(baseline))
    missing_quantized = sorted(set(ids) - set(quantized))
    if missing_baseline or missing_quantized:
        raise ValueError(f"unpaired outputs; missing_baseline={missing_baseline}, missing_quantized={missing_quantized}")
    rows = [
        {"id": key, "exact_match": exact_match(baseline[key], quantized[key]), "token_f1": token_f1(baseline[key], quantized[key])}
        for key in ids
    ]
    return {
        "count": len(rows),
        "exact_match": mean(row["exact_match"] for row in rows) if rows else None,
        "mean_token_f1": mean(row["token_f1"] for row in rows) if rows else None,
        "per_item": rows,
    }
