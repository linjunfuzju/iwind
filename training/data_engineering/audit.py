"""Cross-split contamination audits for exact, near, and evidence leakage."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable, Mapping

from .core import NearDuplicateIndex, sha256_text


@dataclass(frozen=True, slots=True)
class ContaminationFinding:
    kind: str
    left_split: str
    left_id: str
    right_split: str
    right_id: str
    score: float


def audit_splits(
    records_by_split: Mapping[str, Iterable[Mapping[str, object]]],
    *,
    id_key: str = "chunk_id",
    text_key: str = "text",
    group_key: str = "document_id",
    near_threshold: float = 0.85,
) -> list[ContaminationFinding]:
    findings: list[ContaminationFinding] = []
    exact: dict[str, tuple[str, str]] = {}
    groups: dict[object, tuple[str, str]] = {}
    near = NearDuplicateIndex(near_threshold)
    near_owners: dict[str, tuple[str, str]] = {}
    for split in sorted(records_by_split):
        for offset, record in enumerate(records_by_split[split]):
            identifier = str(record.get(id_key) or f"{split}:{offset}")
            text = record.get(text_key)
            if not isinstance(text, str) or not text.strip():
                continue
            group = record.get(group_key)
            if group is not None and group in groups and groups[group][0] != split:
                other_split, other_id = groups[group]
                findings.append(ContaminationFinding("group", other_split, other_id, split, identifier, 1.0))
            elif group is not None:
                groups[group] = (split, identifier)
            digest = sha256_text(text)
            if digest in exact and exact[digest][0] != split:
                other_split, other_id = exact[digest]
                findings.append(ContaminationFinding("exact", other_split, other_id, split, identifier, 1.0))
                continue
            exact.setdefault(digest, (split, identifier))
            match = near.find(text)
            if match is not None:
                other_key, score = match
                other_split, other_id = near_owners[other_key]
                if other_split != split:
                    findings.append(ContaminationFinding("near", other_split, other_id, split, identifier, score))
            key = f"{split}\0{identifier}"
            near.add(key, text)
            near_owners[key] = (split, identifier)
    return findings


def findings_as_dicts(findings: Iterable[ContaminationFinding]) -> list[dict[str, object]]:
    return [asdict(finding) for finding in findings]


def audit_benchmark_evidence(
    benchmark_records: Iterable[Mapping[str, object]], training_document_ids: set[str]
) -> list[dict[str, str]]:
    findings = []
    for record in benchmark_records:
        question_id = str(record.get("question_id", "unknown"))
        evidence = record.get("evidence_document_ids", [])
        if isinstance(evidence, list):
            for document_id in evidence:
                if document_id in training_document_ids:
                    findings.append({"question_id": question_id, "document_id": str(document_id)})
    return findings
