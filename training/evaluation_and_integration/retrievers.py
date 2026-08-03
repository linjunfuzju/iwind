"""Dependency-free lexical, callback dense, and structured retrievers."""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any, Protocol

try:
    from .rag_types import Document, Query, RetrievalHit
except ImportError:
    from rag_types import Document, Query, RetrievalHit


def tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.casefold())


class Retriever(Protocol):
    def retrieve(self, query: Query) -> list[RetrievalHit]: ...


class LexicalBM25Retriever:
    def __init__(self, documents: Iterable[Document], k1: float = 1.5, b: float = 0.75) -> None:
        self.documents = tuple(documents)
        self.k1, self.b = k1, b
        self.terms = [Counter(tokenize(f"{doc.title} {doc.text}")) for doc in self.documents]
        self.lengths = [sum(values.values()) for values in self.terms]
        self.average_length = sum(self.lengths) / len(self.lengths) if self.lengths else 0.0
        self.document_frequency = Counter(term for values in self.terms for term in values)

    def retrieve(self, query: Query) -> list[RetrievalHit]:
        query_terms = Counter(tokenize(query.text))
        scored = []
        for document, frequencies, length in zip(self.documents, self.terms, self.lengths):
            score = 0.0
            for term, query_frequency in query_terms.items():
                frequency = frequencies[term]
                if not frequency:
                    continue
                count = len(self.documents)
                inverse = math.log(1 + (count - self.document_frequency[term] + 0.5) / (self.document_frequency[term] + 0.5))
                denominator = frequency + self.k1 * (1 - self.b + self.b * length / (self.average_length or 1))
                score += query_frequency * inverse * frequency * (self.k1 + 1) / denominator
            if score > 0:
                scored.append((score, document))
        scored.sort(key=lambda item: (-item[0], item[1].document_id))
        return [RetrievalHit(document, score, rank, "lexical") for rank, (score, document) in enumerate(scored[:query.top_k], 1)]


class DenseCallbackRetriever:
    """Adapts an application-owned dense search callback without owning a model."""

    def __init__(self, callback: Callable[[str, int, Mapping[str, Any]], Sequence[tuple[Document, float]]]) -> None:
        self.callback = callback

    def retrieve(self, query: Query) -> list[RetrievalHit]:
        results = list(self.callback(query.text, query.top_k, query.filters))
        results.sort(key=lambda item: (-float(item[1]), item[0].document_id))
        return [RetrievalHit(document, float(score), rank, "dense") for rank, (document, score) in enumerate(results[:query.top_k], 1)]


class StructuredRetriever:
    def __init__(self, documents: Iterable[Document], fields: Sequence[str]) -> None:
        self.documents = tuple(documents)
        self.fields = tuple(fields)

    def retrieve(self, query: Query) -> list[RetrievalHit]:
        terms = set(tokenize(query.text))
        scored = []
        for document in self.documents:
            if any(document.metadata.get(key) != value for key, value in query.filters.items()):
                continue
            values = " ".join(str(document.metadata.get(field, "")) for field in self.fields)
            candidate_terms = set(tokenize(values))
            score = len(terms & candidate_terms) / len(terms) if terms else 0.0
            if score > 0 or query.filters:
                scored.append((score, document))
        scored.sort(key=lambda item: (-item[0], item[1].document_id))
        return [RetrievalHit(document, score, rank, "structured") for rank, (score, document) in enumerate(scored[:query.top_k], 1)]
