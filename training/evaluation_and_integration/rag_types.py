"""Validated contracts for retrieval, fusion, context, and cited generation."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class Query:
    text: str
    filters: Mapping[str, Any] = field(default_factory=dict)
    top_k: int = 10

    def __post_init__(self) -> None:
        if not self.text.strip() or self.top_k <= 0:
            raise ValueError("query text must be non-empty and top_k positive")


@dataclass(frozen=True)
class Document:
    document_id: str
    title: str
    text: str
    source_uri: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.document_id.strip() or not self.text.strip() or not self.source_uri.strip():
            raise ValueError("document_id, text, and source_uri must be non-empty")


@dataclass(frozen=True)
class RetrievalHit:
    document: Document
    score: float
    rank: int
    path: str
    explanation: str = ""

    def __post_init__(self) -> None:
        if not math.isfinite(self.score) or self.rank <= 0 or not self.path:
            raise ValueError("retrieval score must be finite, rank positive, and path non-empty")


@dataclass(frozen=True)
class RetrievedDocument:
    """Compatibility input for pre-scored three-path JSONL files."""
    document_id: str
    title: str
    text: str
    source_uri: str
    lexical_score: float = 0.0
    dense_score: float = 0.0
    structured_score: float = 0.0
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FusedEvidence:
    citation_id: str
    document_id: str
    title: str
    text: str
    source_uri: str
    fused_score: float
    path_scores: Mapping[str, float] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ContextBundle:
    text: str
    evidence: tuple[FusedEvidence, ...]
    estimated_tokens: int
    omitted_document_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class CitationValidation:
    citations: tuple[str, ...]
    invalid: tuple[str, ...]
    uncited_claims: tuple[str, ...]

    @property
    def valid(self) -> bool:
        return not self.invalid and not self.uncited_claims


@dataclass(frozen=True)
class CitedAnswer:
    answer: str
    citations: tuple[str, ...]
    evidence: tuple[FusedEvidence, ...]
    validation: CitationValidation | None = None
