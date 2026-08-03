"""Reproducible corpus statistics and artifact manifests."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def corpus_statistics(records: Iterable[Mapping[str, object]]) -> dict[str, object]:
    rows = list(records)
    char_counts = [len(str(row.get("text", ""))) for row in rows]
    token_counts = [int(row["token_count"]) for row in rows if isinstance(row.get("token_count"), int)]
    return {
        "records": len(rows),
        "documents": len({row.get("document_id") for row in rows}),
        "characters": sum(char_counts),
        "tokens": sum(token_counts),
        "mean_characters": sum(char_counts) / len(char_counts) if char_counts else 0.0,
        "mean_tokens": sum(token_counts) / len(token_counts) if token_counts else 0.0,
        "by_language": dict(sorted(Counter(str(row.get("language", "unknown")) for row in rows).items())),
        "by_domain": dict(sorted(Counter(str(row.get("domain", "unknown")) for row in rows).items())),
        "by_source_type": dict(sorted(Counter(str(row.get("source_type", "unknown")) for row in rows).items())),
    }


def build_manifest(
    *,
    command: str,
    seed: int,
    inputs: Iterable[Path],
    outputs: Iterable[Path],
    parameters: Mapping[str, object],
    statistics: Mapping[str, object],
) -> dict[str, object]:
    def artifacts(paths: Iterable[Path]) -> list[dict[str, object]]:
        return [
            {"path": str(path.resolve()), "bytes": path.stat().st_size, "sha256": file_sha256(path)}
            for path in sorted(paths, key=lambda item: str(item))
            if path.exists()
        ]

    return {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "seed": seed,
        "parameters": dict(parameters),
        "inputs": artifacts(inputs),
        "outputs": artifacts(outputs),
        "statistics": dict(statistics),
    }


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)
