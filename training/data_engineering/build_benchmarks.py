"""Validate, assign stable IDs, and materialize multilingual benchmarks."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

try:
    from .core import stable_id
    from .schemas import BENCHMARK_TASKS, BenchmarkRecord, SchemaError
    from .statistics import build_manifest, write_json
except ImportError:  # Support direct execution from this directory.
    from core import stable_id
    from schemas import BENCHMARK_TASKS, BenchmarkRecord, SchemaError
    from statistics import build_manifest, write_json


def read_records(path: Path) -> Iterable[tuple[int, dict[str, Any]]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON at {path}:{line_number}: {exc}") from exc
            if not isinstance(record, dict):
                raise ValueError(f"Expected an object at {path}:{line_number}")
            yield line_number, record


def normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    value = dict(record)
    if not value.get("question_id"):
        value["question_id"] = stable_id(
            "question",
            value.get("benchmark"),
            value.get("task"),
            value.get("language"),
            value.get("question"),
            value.get("evidence_document_ids"),
        )
    value.setdefault("choices", [])
    value.setdefault("answer", None)
    value.setdefault("reference_answer", None)
    value.setdefault("metadata", {})
    return BenchmarkRecord.from_dict(value).to_dict()


def build_benchmarks(args: argparse.Namespace) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    identifiers: set[str] = set()
    for line_number, raw in read_records(args.input):
        try:
            record = normalize_record(raw)
        except SchemaError as exc:
            raise ValueError(f"Invalid benchmark record at line {line_number}: {exc}") from exc
        if record["question_id"] in identifiers:
            raise ValueError(f"Duplicate question_id at line {line_number}: {record['question_id']}")
        identifiers.add(record["question_id"])
        records.append(record)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_paths = []
    for benchmark in BENCHMARK_TASKS:
        path = args.output_dir / f"{benchmark}.jsonl"
        temporary = path.with_suffix(path.suffix + ".tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            for record in records:
                if record["benchmark"] == benchmark:
                    handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        temporary.replace(path)
        output_paths.append(path)

    coverage = Counter((r["benchmark"], r["task"], r["language"], r["question_type"], r["difficulty"]) for r in records)
    stats = {
        "records": len(records),
        "coverage": {"|".join(key): value for key, value in sorted(coverage.items())},
        "evidence_documents": len({item for record in records for item in record["evidence_document_ids"]}),
    }
    manifest = build_manifest(
        command="build_benchmarks",
        seed=0,
        inputs=[args.input],
        outputs=output_paths,
        parameters={},
        statistics=stats,
    )
    write_json(args.output_dir / "manifest.json", manifest)
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


if __name__ == "__main__":
    build_benchmarks(parse_args())
