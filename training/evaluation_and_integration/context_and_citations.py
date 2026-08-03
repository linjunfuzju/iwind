"""Context budgeting plus citation parsing and structural validation."""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence

try:
    from .rag_types import CitationValidation, ContextBundle, FusedEvidence
except ImportError:
    from rag_types import CitationValidation, ContextBundle, FusedEvidence


def estimate_tokens(text: str) -> int:
    return len(re.findall(r"\w+|[^\w\s]", text))


def build_context(
    evidence: Sequence[FusedEvidence], max_tokens: int, token_counter: Callable[[str], int] = estimate_tokens,
    per_document_tokens: int | None = None,
) -> ContextBundle:
    if max_tokens <= 0:
        raise ValueError("max_tokens must be positive")
    blocks, included, omitted = [], [], []
    used = 0
    for item in evidence:
        text = item.text
        if per_document_tokens is not None and token_counter(text) > per_document_tokens:
            words = re.findall(r"\S+", text)
            text = " ".join(words[:per_document_tokens])
        block = f"[{item.citation_id}]\ntitle: {item.title}\nsource: {item.source_uri}\ncontent: {text}"
        cost = token_counter(block)
        if used + cost > max_tokens:
            omitted.append(item.document_id)
            continue
        blocks.append(block)
        included.append(item)
        used += cost
    return ContextBundle("\n\n".join(blocks), tuple(included), used, tuple(omitted))


def parse_citations(answer: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(re.findall(r"\[(S[1-9]\d*)\]", answer)))


def validate_citations(answer: str, evidence: Sequence[FusedEvidence], require_claim_citations: bool = True) -> CitationValidation:
    citations = parse_citations(answer)
    valid = {item.citation_id for item in evidence}
    invalid = tuple(sorted(set(citations) - valid))
    uncited = []
    if require_claim_citations:
        sentences = re.split(r"(?<=[.!?])\s+", answer.strip())
        for sentence in sentences:
            stripped = sentence.strip()
            if len(stripped.split()) >= 5 and not re.search(r"\[S[1-9]\d*\]", stripped):
                uncited.append(stripped)
    return CitationValidation(citations, invalid, tuple(uncited))
