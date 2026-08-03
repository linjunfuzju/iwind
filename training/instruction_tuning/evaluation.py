"""Pure-Python helpers for SFT generation and aggregate evaluation."""

from __future__ import annotations

import math
from collections import Counter
from typing import Iterable, Mapping, Sequence


def supervised_token_count(labels: Sequence[int], ignore_index: int = -100) -> int:
    return sum(label != ignore_index for label in labels)


def masked_token_accuracy(logits_or_predictions: Sequence[int], labels: Sequence[int], ignore_index: int = -100) -> float:
    if len(logits_or_predictions) != len(labels):
        raise ValueError("predictions and labels must have equal lengths")
    pairs = [(prediction, label) for prediction, label in zip(logits_or_predictions, labels) if label != ignore_index]
    if not pairs:
        raise ValueError("labels contain no supervised tokens")
    return sum(prediction == label for prediction, label in pairs) / len(pairs)


def extract_generated_tokens(full_output: Sequence[int], prompt_length: int) -> list[int]:
    if prompt_length < 0 or prompt_length > len(full_output):
        raise ValueError("prompt_length is outside output bounds")
    return list(full_output[prompt_length:])


def aggregate_metrics(rows: Iterable[Mapping[str, float]], weight_key: str | None = None) -> dict[str, float]:
    values = list(rows)
    if not values:
        return {}
    metric_keys = sorted({key for row in values for key in row if key != weight_key})
    result = {}
    for key in metric_keys:
        weighted = [(row[key], row.get(weight_key, 1.0)) for row in values if key in row]
        denominator = sum(weight for _, weight in weighted)
        result[key] = sum(value * weight for value, weight in weighted) / denominator if denominator else math.nan
    return result


def task_counts(records: Iterable[Mapping[str, object]]) -> dict[str, int]:
    return dict(sorted(Counter(str(record.get("task", "unknown")) for record in records).items()))
