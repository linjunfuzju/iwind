"""Dependency-free benchmark scoring helpers."""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from typing import Iterable, Mapping


def normalize_answer(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).casefold()
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    return " ".join(text.split())


def exact_match(prediction: str, reference: str) -> float:
    return float(normalize_answer(prediction) == normalize_answer(reference))


def token_f1(prediction: str, reference: str) -> float:
    predicted = normalize_answer(prediction).split()
    expected = normalize_answer(reference).split()
    if not predicted or not expected:
        return float(predicted == expected)
    overlap = sum((Counter(predicted) & Counter(expected)).values())
    if overlap == 0:
        return 0.0
    precision, recall = overlap / len(predicted), overlap / len(expected)
    return 2 * precision * recall / (precision + recall)


def objective_choice(prediction: str, choices: Iterable[str]) -> str | None:
    choices = list(choices)
    normalized = normalize_answer(prediction)
    for index, choice in enumerate(choices):
        label = chr(ord("A") + index)
        if re.search(rf"\b{label.casefold()}\b", normalized) or normalize_answer(choice) == normalized:
            return choice
    return None


def summarize_scores(rows: Iterable[Mapping[str, object]]) -> dict[str, float]:
    values = list(rows)
    keys = sorted({key for row in values for key, value in row.items() if isinstance(value, (int, float))})
    return {key: sum(float(row.get(key, 0.0)) for row in values) / len(values) for key in keys} if values else {}
