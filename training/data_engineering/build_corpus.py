"""Normalize, chunk, filter, deduplicate, split, and describe a domain corpus."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

try:
    from .core import NearDuplicateIndex, chunk_text, normalize_text, sha256_text, stable_document_id
    from .schemas import CorpusRecord, DOMAINS, LANGUAGES, SchemaError
    from .splits import grouped_split
    from .statistics import build_manifest, corpus_statistics, write_json
except ImportError:  # Support direct execution from this directory.
    from core import NearDuplicateIndex, chunk_text, normalize_text, sha256_text, stable_document_id
    from schemas import CorpusRecord, DOMAINS, LANGUAGES, SchemaError
    from splits import grouped_split
    from statistics import build_manifest, corpus_statistics, write_json


TEXT_FIELDS = ("text", "content", "article", "Article", "body")


def read_jsonl(path: Path) -> Iterable[tuple[int, dict[str, Any]]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON at {path}:{line_number}: {exc}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"Expected an object at {path}:{line_number}")
            yield line_number, value


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    temporary.replace(path)


def first_text(record: dict[str, Any]) -> str:
    for field in TEXT_FIELDS:
        value = record.get(field)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def normalize_source_record(record: dict[str, Any]) -> dict[str, Any]:
    text = normalize_text(first_text(record))
    metadata = record.get("metadata", {})
    if not isinstance(metadata, dict):
        raise SchemaError("metadata must be an object")
    return {
        "document_id": stable_document_id(record, text),
        "text": text,
        "language": str(record.get("language", "en")).strip().lower(),
        "domain": str(record.get("domain", "offshore_wind")).strip().lower(),
        "task": str(record.get("task", "domain_knowledge")).strip(),
        "source_type": str(record.get("source_type", "unknown")).strip(),
        "source_uri": str(record.get("source_uri", "unknown")).strip(),
        "metadata": metadata,
    }


def build_corpus(args: argparse.Namespace) -> dict[str, Any]:
    if args.min_chars < 1 or args.max_chars < args.min_chars:
        raise ValueError("require 1 <= min_chars <= max_chars")
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()
    near_index = NearDuplicateIndex(args.near_dedup_threshold, args.shingle_size)
    keywords = [normalize_text(value).casefold() for value in args.keyword if value.strip()]

    for line_number, raw in read_jsonl(args.input):
        try:
            source = normalize_source_record(raw)
        except (SchemaError, TypeError, ValueError) as exc:
            rejected.append({"line_number": line_number, "reasons": ["invalid_schema"], "detail": str(exc)})
            continue
        source_reasons = []
        if not source["text"]:
            source_reasons.append("empty_text")
        if source["language"] not in LANGUAGES:
            source_reasons.append("unsupported_language")
        if source["domain"] not in DOMAINS:
            source_reasons.append("unsupported_domain")
        if args.require_provenance and (source["source_type"] == "unknown" or source["source_uri"] == "unknown"):
            source_reasons.append("missing_provenance")
        if keywords and not any(keyword in source["text"].casefold() for keyword in keywords):
            source_reasons.append("keyword_filter")
        if source_reasons:
            rejected.append({"line_number": line_number, "reasons": source_reasons, "record": source})
            continue

        chunks = chunk_text(source["text"], args.max_tokens, args.overlap_tokens)
        for chunk in chunks:
            digest = sha256_text(chunk.text)
            chunk_id = f"{source['document_id']}:{chunk.index:05d}"
            reasons = []
            if len(chunk.text) < args.min_chars:
                reasons.append("too_short")
            if len(chunk.text) > args.max_chars:
                reasons.append("too_long")
            if digest in seen_hashes:
                reasons.append("exact_duplicate")
            near_match = None if reasons or args.near_dedup_threshold >= 1.0 else near_index.find(chunk.text)
            if near_match is not None:
                reasons.append("near_duplicate")
            candidate = {
                **source,
                "chunk_id": chunk_id,
                "text": chunk.text,
                "content_sha256": digest,
                "token_count": chunk.token_count,
                "chunk_index": chunk.index,
            }
            try:
                validated = CorpusRecord.from_dict(candidate).to_dict()
            except SchemaError as exc:
                reasons.append("invalid_schema")
                candidate["schema_error"] = str(exc)
            if reasons:
                rejected.append(
                    {
                        "line_number": line_number,
                        "reasons": reasons,
                        "near_duplicate_of": near_match[0] if near_match else None,
                        "near_duplicate_score": near_match[1] if near_match else None,
                        "record": candidate,
                    }
                )
                continue
            seen_hashes.add(digest)
            near_index.add(chunk_id, chunk.text)
            accepted.append(validated)

    group_sizes = Counter(record["document_id"] for record in accepted)
    assignments = grouped_split(group_sizes, seed=args.seed)
    output_dir: Path = args.output_dir
    output_paths = []
    records_by_split: dict[str, list[dict[str, Any]]] = {}
    for split in ("train", "validation", "test"):
        records_by_split[split] = [record for record in accepted if assignments[record["document_id"]] == split]
        path = output_dir / f"corpus_{split}.jsonl"
        write_jsonl(path, records_by_split[split])
        output_paths.append(path)
    rejected_path = output_dir / "rejected.jsonl"
    write_jsonl(rejected_path, rejected)
    output_paths.append(rejected_path)

    stats = {
        "accepted": corpus_statistics(accepted),
        "rejected_records": len(rejected),
        "rejection_reasons": dict(sorted(Counter(reason for row in rejected for reason in row["reasons"]).items())),
        "splits": {split: corpus_statistics(records) for split, records in records_by_split.items()},
    }
    manifest = build_manifest(
        command="build_corpus",
        seed=args.seed,
        inputs=[args.input],
        outputs=output_paths,
        parameters={
            "min_chars": args.min_chars,
            "max_chars": args.max_chars,
            "max_tokens": args.max_tokens,
            "overlap_tokens": args.overlap_tokens,
            "near_dedup_threshold": args.near_dedup_threshold,
            "shingle_size": args.shingle_size,
            "keywords": args.keyword,
            "require_provenance": args.require_provenance,
        },
        statistics=stats,
    )
    write_json(output_dir / "manifest.json", manifest)
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--min-chars", type=int, default=200)
    parser.add_argument("--max-chars", type=int, default=100_000)
    parser.add_argument("--max-tokens", type=int, default=2048)
    parser.add_argument("--overlap-tokens", type=int, default=128)
    parser.add_argument("--near-dedup-threshold", type=float, default=0.90)
    parser.add_argument("--shingle-size", type=int, default=5)
    parser.add_argument("--keyword", action="append", default=[])
    parser.add_argument("--require-provenance", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


if __name__ == "__main__":
    build_corpus(parse_args())
