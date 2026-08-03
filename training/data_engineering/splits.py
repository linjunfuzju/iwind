"""Deterministic grouped dataset splitting."""

from __future__ import annotations

import hashlib
from collections import Counter
from typing import Iterable, Mapping


DEFAULT_RATIOS = {"train": 0.90, "validation": 0.05, "test": 0.05}


def _validate_ratios(ratios: Mapping[str, float]) -> None:
    if not ratios or any(not isinstance(v, (int, float)) or v < 0 for v in ratios.values()):
        raise ValueError("split ratios must be non-negative numbers")
    if abs(sum(ratios.values()) - 1.0) > 1e-9:
        raise ValueError("split ratios must sum to 1")


def grouped_split(
    group_sizes: Mapping[str, int] | Iterable[str],
    *,
    ratios: Mapping[str, float] = DEFAULT_RATIOS,
    seed: int = 42,
) -> dict[str, str]:
    """Assign whole groups while balancing record counts and preserving determinism."""
    _validate_ratios(ratios)
    sizes = Counter(group_sizes) if not isinstance(group_sizes, Mapping) else Counter(group_sizes)
    if any(not isinstance(size, int) or size <= 0 for size in sizes.values()):
        raise ValueError("group sizes must be positive integers")
    split_names = list(ratios)
    total = sum(sizes.values())
    targets = {name: total * ratios[name] for name in split_names}
    counts = Counter()
    assignments: dict[str, str] = {}
    groups = sorted(
        sizes,
        key=lambda group: (
            -sizes[group],
            hashlib.sha256(f"{seed}\0{group}".encode("utf-8")).hexdigest(),
        ),
    )
    for index, group in enumerate(groups):
        unfilled = [name for name in split_names if ratios[name] > 0 and counts[name] == 0]
        remaining = len(groups) - index
        candidates = unfilled if remaining <= len(unfilled) else split_names
        split = min(
            candidates,
            key=lambda name: (
                (counts[name] + sizes[group] - targets[name]) ** 2 - (counts[name] - targets[name]) ** 2,
                counts[name] / targets[name] if targets[name] else float("inf"),
                split_names.index(name),
            ),
        )
        assignments[group] = split
        counts[split] += sizes[group]
    return assignments


def assert_group_disjoint(records_by_split: Mapping[str, Iterable[Mapping[str, object]]], group_key: str) -> None:
    owners: dict[object, str] = {}
    for split, records in records_by_split.items():
        for record in records:
            group = record.get(group_key)
            if group is None:
                raise ValueError(f"record in {split!r} is missing {group_key!r}")
            previous = owners.setdefault(group, split)
            if previous != split:
                raise ValueError(f"group {group!r} appears in both {previous!r} and {split!r}")
