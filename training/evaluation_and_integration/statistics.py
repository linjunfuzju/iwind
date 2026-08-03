"""Deterministic statistical helpers suitable for small benchmark reports."""

from __future__ import annotations

import math
import random
from collections.abc import Callable, Sequence
from statistics import NormalDist, mean
from typing import TypeVar

T = TypeVar("T")


def wilson_interval(successes: int, total: int, confidence: float = 0.95) -> tuple[float, float]:
    if total <= 0 or not 0 <= successes <= total:
        raise ValueError("require 0 <= successes <= total and total > 0")
    if not 0 < confidence < 1:
        raise ValueError("confidence must be between 0 and 1")
    z = NormalDist().inv_cdf(0.5 + confidence / 2)
    p = successes / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    radius = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return max(0.0, centre - radius), min(1.0, centre + radius)


def percentile(values: Sequence[float], probability: float) -> float:
    if not values or not 0 <= probability <= 1:
        raise ValueError("values must be non-empty and probability in [0, 1]")
    ordered = sorted(values)
    position = probability * (len(ordered) - 1)
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def bootstrap_interval(
    values: Sequence[T],
    statistic: Callable[[Sequence[T]], float] = mean,
    confidence: float = 0.95,
    iterations: int = 2000,
    seed: int = 0,
) -> tuple[float, float]:
    if not values or iterations <= 0 or not 0 < confidence < 1:
        raise ValueError("bootstrap requires values, positive iterations, and confidence in (0, 1)")
    rng = random.Random(seed)
    estimates = [statistic([values[rng.randrange(len(values))] for _ in values]) for _ in range(iterations)]
    alpha = (1 - confidence) / 2
    return percentile(estimates, alpha), percentile(estimates, 1 - alpha)


def paired_comparison(left: Sequence[float], right: Sequence[float], seed: int = 0) -> dict[str, object]:
    if len(left) != len(right) or not left:
        raise ValueError("paired comparison requires equally sized, non-empty samples")
    differences = [b - a for a, b in zip(left, right)]
    wins = sum(value > 0 for value in differences)
    losses = sum(value < 0 for value in differences)
    ties = len(differences) - wins - losses
    return {
        "pairs": len(differences),
        "mean_delta": mean(differences),
        "bootstrap_95": bootstrap_interval(differences, seed=seed),
        "wins": wins,
        "losses": losses,
        "ties": ties,
    }
