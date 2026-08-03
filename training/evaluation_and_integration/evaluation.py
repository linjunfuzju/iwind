"""Benchmark scoring, expert-rating aggregation, and model comparison."""

from __future__ import annotations

import math
import re
import unicodedata
from collections import defaultdict
from statistics import mean
from typing import Any, Iterable, Mapping

try:
    from .schemas import BenchmarkItem, Prediction, RATING_DIMENSIONS
    from .statistics import bootstrap_interval, paired_comparison, wilson_interval
except ImportError:
    from schemas import BenchmarkItem, Prediction, RATING_DIMENSIONS
    from statistics import bootstrap_interval, paired_comparison, wilson_interval


def normalize_objective(value: Any) -> str:
    """Normalize scalar answers without hiding meaningful punctuation or units."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if not math.isfinite(float(value)):
            raise ValueError("objective answers must be finite")
        return format(float(value), ".15g")
    text = unicodedata.normalize("NFKC", str(value)).casefold().strip()
    return re.sub(r"\s+", " ", text)


def objective_correct(predicted: Any, item: BenchmarkItem) -> bool:
    expected = ((item.answer,) if item.answer is not None else ()) + item.acceptable_answers
    normalized = normalize_objective(predicted)
    return normalized in {normalize_objective(value) for value in expected}


def aggregate_expert_ratings(predictions: Iterable[Prediction], seed: int = 0) -> dict[str, object]:
    values: dict[str, list[float]] = defaultdict(list)
    raters: set[str] = set()
    protocols: set[str] = set()
    blind_count = 0
    rating_count = 0
    for prediction in predictions:
        for rating in prediction.ratings:
            rating_count += 1
            blind_count += int(rating.blind)
            raters.add(rating.rater_id)
            protocols.add(rating.protocol_version)
            for dimension in RATING_DIMENSIONS:
                values[dimension].append(float(rating.scores[dimension]))
    dimensions = {}
    for index, dimension in enumerate(RATING_DIMENSIONS):
        samples = values[dimension]
        dimensions[dimension] = {
            "n": len(samples),
            "mean": mean(samples) if samples else None,
            "bootstrap_95": bootstrap_interval(samples, seed=seed + index) if samples else None,
        }
    return {
        "rating_records": rating_count,
        "unique_raters": len(raters),
        "protocol_versions": sorted(protocols),
        "blind_fraction": blind_count / rating_count if rating_count else None,
        "dimensions": dimensions,
    }


def evaluate(items: Iterable[BenchmarkItem], predictions: Mapping[str, Prediction], seed: int = 0) -> dict[str, object]:
    benchmark = list(items)
    ids = [item.question_id for item in benchmark]
    if len(ids) != len(set(ids)):
        raise ValueError("benchmark contains duplicate question_id values")
    missing = sorted(set(ids) - set(predictions))
    extra = sorted(set(predictions) - set(ids))
    if missing:
        raise ValueError(f"missing predictions: {missing[:10]}")
    objective = [item for item in benchmark if item.question_type == "objective"]
    correct = sum(objective_correct(predictions[item.question_id].answer, item) for item in objective)
    open_predictions = [predictions[item.question_id] for item in benchmark if item.question_type == "open_ended"]
    if any(not prediction.ratings for prediction in open_predictions):
        raise ValueError("every open-ended prediction requires at least one expert rating")
    return {
        "coverage": {"benchmark": len(benchmark), "predictions": len(predictions), "extra_prediction_ids": extra},
        "objective": {
            "correct": correct,
            "total": len(objective),
            "accuracy": correct / len(objective) if objective else None,
            "wilson_95": wilson_interval(correct, len(objective)) if objective else None,
        },
        "open_ended": aggregate_expert_ratings(open_predictions, seed),
    }


def compare_sft_grpo(
    items: Iterable[BenchmarkItem],
    sft: Mapping[str, Prediction],
    grpo: Mapping[str, Prediction],
    seed: int = 0,
) -> dict[str, object]:
    benchmark = list(items)
    objective = [item for item in benchmark if item.question_type == "objective"]
    objective_pair = paired_comparison(
        [float(objective_correct(sft[item.question_id].answer, item)) for item in objective],
        [float(objective_correct(grpo[item.question_id].answer, item)) for item in objective],
        seed,
    ) if objective else None
    rating_pairs: dict[str, dict[str, object]] = {}
    for index, dimension in enumerate(RATING_DIMENSIONS):
        left, right = [], []
        for item in benchmark:
            if item.question_type != "open_ended":
                continue
            left.append(mean(r.scores[dimension] for r in sft[item.question_id].ratings))
            right.append(mean(r.scores[dimension] for r in grpo[item.question_id].ratings))
        if left:
            rating_pairs[dimension] = paired_comparison(left, right, seed + index + 1)
    return {
        "direction": "GRPO minus SFT",
        "sft": evaluate(benchmark, sft, seed),
        "grpo": evaluate(benchmark, grpo, seed),
        "paired_objective": objective_pair,
        "paired_ratings": rating_pairs,
    }
