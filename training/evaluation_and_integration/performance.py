"""Aggregate latency, throughput, memory, and token-normalized measurements."""

from __future__ import annotations

from statistics import mean, median
from typing import Iterable, Mapping

def _percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = probability * (len(ordered) - 1)
    lower = int(position)
    fraction = position - lower
    return ordered[lower] if lower == len(ordered) - 1 else ordered[lower] * (1 - fraction) + ordered[lower + 1] * fraction


def aggregate_performance(records: Iterable[Mapping[str, float]]) -> dict[str, float | int | None]:
    rows = list(records)
    if not rows:
        return {"requests": 0, "generated_tokens": 0, "total_seconds": 0.0, "tokens_per_second": None}
    for row in rows:
        if row.get("latency_seconds", -1) < 0 or row.get("generated_tokens", -1) < 0:
            raise ValueError("latency_seconds and generated_tokens must be non-negative")
    latencies = [float(row["latency_seconds"]) for row in rows]
    tokens = sum(int(row["generated_tokens"]) for row in rows)
    elapsed = sum(latencies)
    memory = [float(row["peak_memory_bytes"]) for row in rows if row.get("peak_memory_bytes") is not None]
    return {
        "requests": len(rows),
        "generated_tokens": tokens,
        "total_seconds": elapsed,
        "tokens_per_second": tokens / elapsed if elapsed else None,
        "latency_mean_seconds": mean(latencies),
        "latency_median_seconds": median(latencies),
        "latency_p95_seconds": _percentile(latencies, 0.95),
        "peak_memory_bytes": max(memory) if memory else None,
    }
