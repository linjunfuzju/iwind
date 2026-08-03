"""Validate, split, expand, and manifest rubric-annotated question groups."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable

try:
    from .rubric import RUBRIC_LEVELS, validate_question_groups
except ImportError:  # Support direct execution from this directory.
    from rubric import RUBRIC_LEVELS, validate_question_groups


def deterministic_group_split(
    question_id: str,
    seed: int,
    train_fraction: float,
    validation_fraction: float,
) -> str:
    if train_fraction <= 0 or validation_fraction < 0 or train_fraction + validation_fraction >= 1:
        raise ValueError("Split fractions must satisfy train > 0, validation >= 0, and train + validation < 1")
    digest = hashlib.sha256(f"{seed}:{question_id}".encode("utf-8")).digest()
    value = int.from_bytes(digest[:8], "big") / float(1 << 64)
    if value < train_fraction:
        return "train"
    if value < train_fraction + validation_fraction:
        return "validation"
    return "test"


def expand_question_group(group: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate every cross-level pair once; tied levels are intentionally omitted."""
    metadata = {key: value for key, value in group.items() if key != "responses"}
    pairs = []
    for left, right in combinations(group["responses"], 2):
        if left["level"] == right["level"]:
            continue
        chosen, rejected = (left, right) if left["level"] > right["level"] else (right, left)
        pair = dict(metadata)
        pair.update(
            {
                "pair_id": f"{group['question_id']}:{chosen['response_id']}>{rejected['response_id']}",
                "chosen_response_id": chosen["response_id"],
                "rejected_response_id": rejected["response_id"],
                "chosen": chosen["text"],
                "rejected": rejected["text"],
                "chosen_level": chosen["level"],
                "rejected_level": rejected["level"],
                "quality_gap": chosen["level"] - rejected["level"],
                "chosen_annotation": {key: value for key, value in chosen.items() if key not in ("text", "level")},
                "rejected_annotation": {key: value for key, value in rejected.items() if key not in ("text", "level")},
            }
        )
        pairs.append(pair)
    if not pairs:
        raise ValueError(f"Question {group['question_id']!r} produced no ordered pairs")
    return pairs


def dataset_statistics(groups: Iterable[dict[str, Any]], pairs: Iterable[dict[str, Any]]) -> dict[str, Any]:
    groups = list(groups)
    pairs = list(pairs)
    levels = Counter(response["level"] for group in groups for response in group["responses"])
    gaps = Counter(pair["quality_gap"] for pair in pairs)
    tasks = Counter(str(group.get("task", "unspecified")) for group in groups)
    languages = Counter(str(group.get("language", "unspecified")) for group in groups)
    return {
        "question_groups": len(groups),
        "responses": sum(len(group["responses"]) for group in groups),
        "pairs": len(pairs),
        "rubric_level_counts": {str(level): levels[level] for level in RUBRIC_LEVELS},
        "quality_gap_counts": {str(key): value for key, value in sorted(gaps.items())},
        "task_counts": dict(sorted(tasks.items())),
        "language_counts": dict(sorted(languages.items())),
    }


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if line.strip():
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as error:
                    raise ValueError(f"Invalid JSON at {path}:{line_number}: {error}") from error
    return records


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def prepare(input_path: Path, output_dir: Path, seed: int, train_fraction: float, validation_fraction: float) -> dict[str, Any]:
    groups = validate_question_groups(read_jsonl(input_path))
    partitions: dict[str, list[dict[str, Any]]] = {"train": [], "validation": [], "test": []}
    for group in groups:
        partitions[deterministic_group_split(group["question_id"], seed, train_fraction, validation_fraction)].append(group)
    manifest = {
        "schema_version": 1,
        "source": {"path": str(input_path), "sha256": file_sha256(input_path)},
        "seed": seed,
        "split_fractions": {"train": train_fraction, "validation": validation_fraction, "test": 1 - train_fraction - validation_fraction},
        "partitions": {},
    }
    for split, split_groups in partitions.items():
        pairs = [pair for group in split_groups for pair in expand_question_group(group)]
        split_path = output_dir / split / "preference_dataset.jsonl"
        write_jsonl(split_path, pairs)
        manifest["partitions"][split] = dataset_statistics(split_groups, pairs)
        manifest["partitions"][split]["question_ids"] = sorted(group["question_id"] for group in split_groups)
        manifest["partitions"][split]["path"] = str(split_path)
        manifest["partitions"][split]["sha256"] = file_sha256(split_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True, help="JSONL containing one rubric-annotated question group per line")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--train-fraction", type=float, default=0.8)
    parser.add_argument("--validation-fraction", type=float, default=0.1)
    args = parser.parse_args()
    prepare(args.input, args.output_dir, args.seed, args.train_fraction, args.validation_fraction)


if __name__ == "__main__":
    main()
