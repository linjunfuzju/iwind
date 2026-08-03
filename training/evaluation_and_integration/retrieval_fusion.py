"""Rank-aware reciprocal-rank fusion and deterministic reranking."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence

try:
    from .rag_types import Document, FusedEvidence, RetrievalHit, RetrievedDocument
except ImportError:
    from rag_types import Document, FusedEvidence, RetrievalHit, RetrievedDocument


def reciprocal_rank_fusion(
    result_sets: Mapping[str, Sequence[RetrievalHit]], top_k: int = 8, rank_constant: int = 60,
    weights: Mapping[str, float] | None = None,
) -> list[FusedEvidence]:
    if top_k <= 0 or rank_constant < 0:
        raise ValueError("top_k must be positive and rank_constant non-negative")
    weights = dict(weights or {})
    documents: dict[str, Document] = {}
    fused: dict[str, float] = defaultdict(float)
    path_scores: dict[str, dict[str, float]] = defaultdict(dict)
    for path, hits in result_sets.items():
        seen: set[str] = set()
        for position, hit in enumerate(hits, 1):
            identifier = hit.document.document_id
            if identifier in seen:
                continue
            seen.add(identifier)
            documents.setdefault(identifier, hit.document)
            rank = hit.rank if hit.rank > 0 else position
            fused[identifier] += float(weights.get(path, 1.0)) / (rank_constant + rank)
            path_scores[identifier][path] = hit.score
    ranked = sorted(documents, key=lambda identifier: (-fused[identifier], identifier))[:top_k]
    return [FusedEvidence(
        citation_id=f"S{index}", document_id=identifier, title=documents[identifier].title,
        text=documents[identifier].text, source_uri=documents[identifier].source_uri,
        fused_score=fused[identifier], path_scores=path_scores[identifier], metadata=documents[identifier].metadata,
    ) for index, identifier in enumerate(ranked, 1)]


def rerank(
    query: str, evidence: Sequence[FusedEvidence], scorer: Callable[[str, FusedEvidence], float], top_k: int | None = None,
) -> list[FusedEvidence]:
    scored = [(float(scorer(query, item)), item) for item in evidence]
    scored.sort(key=lambda pair: (-pair[0], -pair[1].fused_score, pair[1].document_id))
    limit = len(scored) if top_k is None else top_k
    return [FusedEvidence(
        citation_id=f"S{index}", document_id=item.document_id, title=item.title, text=item.text,
        source_uri=item.source_uri, fused_score=score, path_scores=item.path_scores, metadata=item.metadata,
    ) for index, (score, item) in enumerate(scored[:limit], 1)]


def fuse_candidates(
    lexical: list[RetrievedDocument], dense: list[RetrievedDocument], structured: list[RetrievedDocument], top_k: int = 8,
) -> list[FusedEvidence]:
    result_sets = {}
    for path, records, score_field in (
        ("lexical", lexical, "lexical_score"), ("dense", dense, "dense_score"), ("structured", structured, "structured_score")
    ):
        result_sets[path] = [RetrievalHit(
            Document(item.document_id, item.title, item.text, item.source_uri, item.metadata),
            float(getattr(item, score_field)), rank, path,
        ) for rank, item in enumerate(records, 1)]
    return reciprocal_rank_fusion(result_sets, top_k=top_k)
