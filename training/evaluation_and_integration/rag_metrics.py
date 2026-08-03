"""Retrieval and citation metrics with explicit denominators."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

try:
    from .context_and_citations import parse_citations
    from .rag_types import FusedEvidence
except ImportError:
    from context_and_citations import parse_citations
    from rag_types import FusedEvidence


def retrieval_metrics(ranked_ids: Sequence[str], relevant_ids: Iterable[str], k: int) -> dict[str, float]:
    relevant = set(relevant_ids)
    if not relevant or k <= 0:
        raise ValueError("relevant_ids must be non-empty and k positive")
    ranked = list(dict.fromkeys(ranked_ids))[:k]
    hits = [identifier in relevant for identifier in ranked]
    reciprocal_rank = next((1 / rank for rank, hit in enumerate(hits, 1) if hit), 0.0)
    return {
        "recall_at_k": sum(hits) / len(relevant),
        "precision_at_k": sum(hits) / k,
        "hit_at_k": float(any(hits)),
        "reciprocal_rank": reciprocal_rank,
    }


def citation_metrics(answer: str, evidence: Sequence[FusedEvidence], relevant_document_ids: Iterable[str]) -> dict[str, float | int]:
    citation_map = {item.citation_id: item.document_id for item in evidence}
    citations = parse_citations(answer)
    valid = [citation for citation in citations if citation in citation_map]
    relevant = set(relevant_document_ids)
    relevant_citations = [citation for citation in valid if citation_map[citation] in relevant]
    cited_relevant_documents = {citation_map[citation] for citation in relevant_citations}
    return {
        "citation_count": len(citations),
        "citation_validity": len(valid) / len(citations) if citations else 0.0,
        "citation_precision": len(relevant_citations) / len(valid) if valid else 0.0,
        "citation_recall": len(cited_relevant_documents) / len(relevant) if relevant else 0.0,
    }
