"""Canonicalization, stable identifiers, chunking, and near-deduplication."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Iterable, Iterator, Mapping, Sequence


TOKEN_PATTERN = re.compile(r"\w+|[^\w\s]", re.UNICODE)


def normalize_text(text: str) -> str:
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    text = unicodedata.normalize("NFKC", text).replace("\x00", " ").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t\f\v]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def canonical_text(text: str) -> str:
    return re.sub(r"\s+", " ", normalize_text(text)).casefold()


def sha256_text(text: str) -> str:
    return hashlib.sha256(canonical_text(text).encode("utf-8")).hexdigest()


def stable_id(namespace: str, *parts: Any, length: int = 24) -> str:
    if not re.fullmatch(r"[a-z][a-z0-9_-]*", namespace):
        raise ValueError("namespace must be a lowercase identifier")
    payload = json.dumps(parts, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:length]
    return f"{namespace}-{digest}"


def stable_document_id(record: Mapping[str, Any], text: str) -> str:
    explicit = record.get("document_id") or record.get("id")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()
    uri = record.get("source_uri")
    if isinstance(uri, str) and uri.strip() and uri.strip() != "unknown":
        return stable_id("doc", uri.strip())
    return stable_id("doc", canonical_text(text))


@dataclass(frozen=True, slots=True)
class TextChunk:
    text: str
    index: int
    token_start: int
    token_end: int
    token_count: int


def regex_token_spans(text: str) -> list[tuple[int, int]]:
    """Return deterministic token offsets without requiring a model tokenizer."""
    return [(match.start(), match.end()) for match in TOKEN_PATTERN.finditer(text)]


def chunk_text(text: str, max_tokens: int, overlap_tokens: int = 0) -> list[TextChunk]:
    """Chunk normalized text by token offsets, preserving exact source substrings."""
    if max_tokens <= 0:
        raise ValueError("max_tokens must be positive")
    if overlap_tokens < 0 or overlap_tokens >= max_tokens:
        raise ValueError("overlap_tokens must satisfy 0 <= overlap_tokens < max_tokens")
    normalized = normalize_text(text)
    spans = regex_token_spans(normalized)
    if not spans:
        return []
    result: list[TextChunk] = []
    step = max_tokens - overlap_tokens
    for index, start in enumerate(range(0, len(spans), step)):
        end = min(start + max_tokens, len(spans))
        char_start = spans[start][0]
        char_end = spans[end - 1][1]
        result.append(TextChunk(normalized[char_start:char_end], index, start, end, end - start))
        if end == len(spans):
            break
    return result


def word_shingles(text: str, size: int = 5) -> frozenset[str]:
    if size <= 0:
        raise ValueError("shingle size must be positive")
    tokens = [match.group(0).casefold() for match in TOKEN_PATTERN.finditer(canonical_text(text))]
    if not tokens:
        return frozenset()
    if len(tokens) < size:
        return frozenset({" ".join(tokens)})
    return frozenset(" ".join(tokens[i : i + size]) for i in range(len(tokens) - size + 1))


def jaccard_similarity(left: Iterable[str], right: Iterable[str]) -> float:
    a, b = set(left), set(right)
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


class NearDuplicateIndex:
    """Deterministic exact Jaccard index suitable for curated corpora and audits."""

    def __init__(self, threshold: float = 0.85, shingle_size: int = 5) -> None:
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("threshold must be in [0, 1]")
        self.threshold = threshold
        self.shingle_size = shingle_size
        self._entries: list[tuple[str, frozenset[str]]] = []

    def find(self, text: str) -> tuple[str, float] | None:
        shingles = word_shingles(text, self.shingle_size)
        best: tuple[str, float] | None = None
        for identifier, candidate in self._entries:
            score = jaccard_similarity(shingles, candidate)
            if score >= self.threshold and (best is None or score > best[1]):
                best = (identifier, score)
        return best

    def add(self, identifier: str, text: str) -> None:
        self._entries.append((identifier, word_shingles(text, self.shingle_size)))

    def check_and_add(self, identifier: str, text: str) -> tuple[str, float] | None:
        match = self.find(text)
        if match is None:
            self.add(identifier, text)
        return match


def batched(values: Sequence[Any], size: int) -> Iterator[Sequence[Any]]:
    if size <= 0:
        raise ValueError("size must be positive")
    for start in range(0, len(values), size):
        yield values[start : start + size]
