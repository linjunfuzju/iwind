"""Build deterministic calibration data with exact and approximate leakage checks."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
from pathlib import Path
from typing import Any, Iterable

try:
    from .artifacts import atomic_write_json, atomic_write_jsonl, build_manifest, canonical_json
except ImportError:
    from artifacts import atomic_write_json, atomic_write_jsonl, build_manifest, canonical_json


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).casefold().strip()


def stable_hash(text: str) -> str:
    return hashlib.sha256(normalize_text(text).encode("utf-8")).hexdigest()


def token_fingerprint(text: str) -> set[str]:
    return set(re.findall(r"\w+", normalize_text(text)))


def extract_text(record: dict[str, Any], source_format: str) -> str:
    if source_format == "grpo":
        return str(record.get("prompt", ""))
    if source_format == "text":
        return str(record.get("text", ""))
    if source_format == "messages":
        messages = record.get("messages", [])
        if not isinstance(messages, list):
            raise ValueError("messages source requires a list")
        return "\n".join(
            f"{message.get('role', 'unknown')}: {message.get('content', '')}"
            for message in messages if isinstance(message, dict)
        )
    raise ValueError(f"unsupported calibration source format: {source_format}")


def load_exclusions(paths: Iterable[Path]) -> tuple[set[str], list[set[str]]]:
    hashes: set[str] = set()
    fingerprints: list[set[str]] = []
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8")) if path.suffix == ".json" else None
        if isinstance(payload, list):
            for item in payload:
                if isinstance(item, str) and re.fullmatch(r"[0-9a-fA-F]{64}", item):
                    hashes.add(item.casefold())
                elif isinstance(item, str):
                    hashes.add(stable_hash(item))
                    fingerprints.append(token_fingerprint(item))
            continue
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    value = json.loads(line)
                except json.JSONDecodeError as error:
                    raise ValueError(f"invalid exclusion JSON at {path}:{line_number}") from error
                texts = [str(value.get(key, "")) for key in ("prompt", "question", "text", "answer") if value.get(key)]
                combined = "\n".join(texts)
                if combined:
                    hashes.add(stable_hash(combined))
                    fingerprints.append(token_fingerprint(combined))
                if isinstance(value.get("sha256"), str):
                    hashes.add(value["sha256"].casefold())
    return hashes, fingerprints


def is_leakage(text: str, hashes: set[str], fingerprints: list[set[str]], threshold: float) -> bool:
    if stable_hash(text) in hashes:
        return True
    tokens = token_fingerprint(text)
    if not tokens or threshold >= 1:
        return False
    for excluded in fingerprints:
        union = tokens | excluded
        if union and len(tokens & excluded) / len(union) >= threshold:
            return True
    return False


def read_source(source: dict[str, Any], base: Path, min_chars: int) -> list[dict[str, Any]]:
    path = (base / source["path"]).resolve() if not Path(source["path"]).is_absolute() else Path(source["path"])
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"invalid source JSON at {path}:{line_number}") from error
            text = extract_text(raw, source["format"]).strip()
            if len(text) >= min_chars:
                records.append({
                    "text": text,
                    "source": str(source.get("name") or path.name),
                    "source_format": source["format"],
                    "source_file": str(path),
                    "source_line": line_number,
                    "sha256": stable_hash(text),
                })
    return records


def allocate(total: int, ratios: list[float]) -> list[int]:
    if total <= 0 or not ratios or any(not math.isfinite(r) or r < 0 for r in ratios) or sum(ratios) <= 0:
        raise ValueError("total and source ratios must be positive and finite")
    raw = [total * ratio / sum(ratios) for ratio in ratios]
    result = [int(value) for value in raw]
    order = sorted(range(len(raw)), key=lambda index: (-(raw[index] - result[index]), index))
    for index in order[:total - sum(result)]:
        result[index] += 1
    return result


def build(config: dict[str, Any], config_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    seed = int(config["seed"])
    rng = random.Random(seed)
    exclusion_paths = []
    for value in config.get("evaluation_files", []):
        path = Path(value)
        exclusion_paths.append((config_dir / path).resolve() if not path.is_absolute() else path)
    legacy = config.get("evaluation_hash_file")
    if legacy:
        path = Path(legacy)
        exclusion_paths.append((config_dir / path).resolve() if not path.is_absolute() else path)
    excluded_hashes, excluded_fingerprints = load_exclusions(exclusion_paths)
    threshold = float(config.get("near_duplicate_jaccard", 0.85))
    if not 0 < threshold <= 1:
        raise ValueError("near_duplicate_jaccard must be in (0, 1]")
    pools = [read_source(source, config_dir, int(config["min_chars"])) for source in config["sources"]]
    targets = allocate(int(config["total_samples"]), [float(source["ratio"]) for source in config["sources"]])
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    rejected_leakage = 0
    actual_by_source: dict[str, int] = {}
    for source, pool, target in zip(config["sources"], pools, targets):
        rng.shuffle(pool)
        count = 0
        for record in pool:
            if record["sha256"] in seen:
                continue
            if is_leakage(record["text"], excluded_hashes, excluded_fingerprints, threshold):
                rejected_leakage += 1
                continue
            selected.append(record)
            seen.add(record["sha256"])
            count += 1
            if count == target:
                break
        actual_by_source[str(source.get("name") or source["path"])] = count
    remaining = [record for pool in pools for record in pool if record["sha256"] not in seen]
    rng.shuffle(remaining)
    for record in remaining:
        if len(selected) >= int(config["total_samples"]):
            break
        if is_leakage(record["text"], excluded_hashes, excluded_fingerprints, threshold):
            rejected_leakage += 1
            continue
        selected.append(record)
        seen.add(record["sha256"])
    rng.shuffle(selected)
    if config.get("require_full_sample", True) and len(selected) < int(config["total_samples"]):
        raise ValueError(f"only {len(selected)} leakage-free unique records available; requested {config['total_samples']}")
    digest = hashlib.sha256(b"".join(canonical_json(record) + b"\n" for record in selected)).hexdigest()
    return selected, {
        "seed": seed,
        "requested_samples": int(config["total_samples"]),
        "actual_samples": len(selected),
        "targets": targets,
        "actual_by_source_before_redistribution": actual_by_source,
        "excluded_files": [str(path) for path in exclusion_paths],
        "rejected_for_leakage": rejected_leakage,
        "near_duplicate_jaccard": threshold,
        "dataset_sha256": digest,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    config_path = args.config.resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    records, parameters = build(config, config_path.parent)
    output = Path(config["output_file"])
    output = (config_path.parent / output).resolve() if not output.is_absolute() else output
    manifest_path = Path(config["manifest_file"])
    manifest_path = (config_path.parent / manifest_path).resolve() if not manifest_path.is_absolute() else manifest_path
    atomic_write_jsonl(output, records)
    manifest = build_manifest("gptq_calibration", [output], parameters)
    atomic_write_json(manifest_path, manifest)


if __name__ == "__main__":
    main()
