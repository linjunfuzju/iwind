"""Run dependency-free lexical and structured retrieval over a JSONL corpus."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from .artifacts import read_jsonl
    from .context_and_citations import build_context
    from .rag_types import Document, Query
    from .retrieval_fusion import reciprocal_rank_fusion
    from .retrievers import LexicalBM25Retriever, StructuredRetriever
except ImportError:
    from artifacts import read_jsonl
    from context_and_citations import build_context
    from rag_types import Document, Query
    from retrieval_fusion import reciprocal_rank_fusion
    from retrievers import LexicalBM25Retriever, StructuredRetriever


def load_documents(path: Path) -> list[Document]:
    return [Document(
        document_id=record["document_id"], title=record.get("title", ""), text=record["text"],
        source_uri=record["source_uri"], metadata=record.get("metadata", {}),
    ) for record in read_jsonl(path)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--documents", type=Path, required=True)
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--context-tokens", type=int, default=4000)
    parser.add_argument("--structured-fields", nargs="*", default=["asset", "component", "alarm", "project", "document_type"])
    args = parser.parse_args()
    documents = load_documents(args.documents)
    query = Query(args.query, top_k=args.top_k)
    results = {
        "lexical": LexicalBM25Retriever(documents).retrieve(query),
        "structured": StructuredRetriever(documents, args.structured_fields).retrieve(query),
    }
    evidence = reciprocal_rank_fusion(results, args.top_k)
    context = build_context(evidence, args.context_tokens)
    print(json.dumps({
        "query": args.query,
        "estimated_tokens": context.estimated_tokens,
        "omitted_document_ids": context.omitted_document_ids,
        "evidence": [item.__dict__ for item in context.evidence],
        "context": context.text,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
