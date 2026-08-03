"""Numerically safe language-model evaluation helpers."""

from __future__ import annotations

import math
from typing import Iterable


def perplexity(loss: float) -> float:
    if not math.isfinite(loss):
        return float("inf")
    try:
        return math.exp(loss)
    except OverflowError:
        return float("inf")


def weighted_mean_loss(losses: Iterable[tuple[float, int]]) -> float:
    total_loss = 0.0
    total_tokens = 0
    for loss, tokens in losses:
        if tokens < 0 or not math.isfinite(loss):
            raise ValueError("losses must be finite and token counts non-negative")
        total_loss += loss * tokens
        total_tokens += tokens
    if total_tokens == 0:
        raise ValueError("at least one evaluated token is required")
    return total_loss / total_tokens
