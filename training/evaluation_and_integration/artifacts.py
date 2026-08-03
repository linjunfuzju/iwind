"""Atomic artifact I/O and reproducibility manifests."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def atomic_write_json(path: Path, value: Any) -> None:
    _atomic_write(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n")


def atomic_write_jsonl(path: Path, records: Iterable[Mapping[str, Any]]) -> None:
    payload = b"".join(canonical_json(record) + b"\n" for record in records)
    _atomic_write(path, payload)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"invalid JSON at {path}:{line_number}: {error.msg}") from error
            if not isinstance(value, dict):
                raise ValueError(f"expected JSON object at {path}:{line_number}")
            records.append(value)
    return records


def build_manifest(kind: str, artifacts: Iterable[Path], parameters: Mapping[str, Any]) -> dict[str, Any]:
    entries = []
    for path in sorted((Path(item) for item in artifacts), key=lambda item: str(item)):
        entries.append({"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    return {
        "schema_version": 1,
        "kind": kind,
        "python": platform.python_version(),
        "parameters": dict(parameters),
        "artifacts": entries,
    }


def verify_manifest(manifest: Mapping[str, Any]) -> list[str]:
    errors = []
    for artifact in manifest.get("artifacts", []):
        path = Path(artifact["path"])
        if not path.is_file():
            errors.append(f"missing: {path}")
        elif path.stat().st_size != artifact["bytes"]:
            errors.append(f"size mismatch: {path}")
        elif sha256_file(path) != artifact["sha256"]:
            errors.append(f"sha256 mismatch: {path}")
    return errors
