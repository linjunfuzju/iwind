"""Metrics for pairwise reward prediction tensors."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import numpy as np


def pairwise_reward_metrics(eval_prediction: Any) -> dict[str, float]:
    predictions = np.asarray(eval_prediction.predictions)
    labels = np.asarray(eval_prediction.label_ids)
    if predictions.ndim != 2 or predictions.shape[1] != 2:
        raise ValueError(f"Expected pair scores [n, 2], received {predictions.shape}")
    if labels.ndim != 2 or labels.shape[1] != 2:
        raise ValueError(f"Expected labels [preferred_index, quality_gap], received {labels.shape}")
    margins = predictions[:, 0] - predictions[:, 1]
    correct = margins > 0
    metrics = {
        "accuracy": float(correct.mean()) if len(correct) else 0.0,
        "tie_rate": float((margins == 0).mean()) if len(margins) else 0.0,
        "mean_margin": float(margins.mean()) if len(margins) else 0.0,
    }
    by_gap: dict[int, list[bool]] = defaultdict(list)
    for gap, is_correct in zip(labels[:, 1], correct):
        by_gap[int(gap)].append(bool(is_correct))
    for gap, values in sorted(by_gap.items()):
        metrics[f"accuracy_gap_{gap}"] = sum(values) / len(values)
    return metrics
