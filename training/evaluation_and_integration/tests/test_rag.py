from __future__ import annotations

import unittest

from iwind.evaluation_and_integration.context_and_citations import build_context, validate_citations
from iwind.evaluation_and_integration.quantization_compare import compare_outputs
from iwind.evaluation_and_integration.rag_metrics import citation_metrics, retrieval_metrics
from iwind.evaluation_and_integration.rag_types import Document, Query
from iwind.evaluation_and_integration.retrieval_fusion import reciprocal_rank_fusion, rerank
from iwind.evaluation_and_integration.retrievers import DenseCallbackRetriever, LexicalBM25Retriever, StructuredRetriever


class RagTests(unittest.TestCase):
    def setUp(self) -> None:
        self.documents = [
            Document("d1", "Cable fault", "subsea cable insulation fault alarm", "urn:d1", {"asset": "array cable"}),
            Document("d2", "Gearbox", "turbine gearbox oil analysis", "urn:d2", {"asset": "turbine"}),
            Document("d3", "Cable inspection", "inspection vessel cable route", "urn:d3", {"asset": "array cable"}),
        ]

    def test_retrievers_fusion_and_reranking_are_deterministic(self) -> None:
        query = Query("cable fault", top_k=3)
        lexical = LexicalBM25Retriever(self.documents).retrieve(query)
        structured = StructuredRetriever(self.documents, ["asset"]).retrieve(query)
        dense = DenseCallbackRetriever(lambda text, k, filters: [(self.documents[2], 0.8), (self.documents[0], 0.9)]).retrieve(query)
        evidence = reciprocal_rank_fusion({"lexical": lexical, "dense": dense, "structured": structured}, rank_constant=10)
        self.assertEqual(evidence[0].document_id, "d1")
        reranked = rerank(query.text, evidence, lambda _, item: 1 if item.document_id == "d3" else 0)
        self.assertEqual(reranked[0].document_id, "d3")
        self.assertEqual(reranked[0].citation_id, "S1")

    def test_context_and_citation_validation(self) -> None:
        hits = LexicalBM25Retriever(self.documents).retrieve(Query("cable", top_k=3))
        evidence = reciprocal_rank_fusion({"lexical": hits}, rank_constant=10)
        context = build_context(evidence, 30)
        self.assertLessEqual(context.estimated_tokens, 30)
        answer = "The cable evidence indicates an insulation fault [S1]."
        validation = validate_citations(answer, context.evidence)
        self.assertTrue(validation.valid)
        invalid = validate_citations("This cites unavailable evidence [S99].", context.evidence)
        self.assertEqual(invalid.invalid, ("S99",))

    def test_metrics_and_quantization_comparison(self) -> None:
        metrics = retrieval_metrics(["d2", "d1"], {"d1", "d3"}, 2)
        self.assertEqual(metrics["recall_at_k"], 0.5)
        evidence = reciprocal_rank_fusion({"lexical": LexicalBM25Retriever(self.documents).retrieve(Query("cable"))})
        citations = citation_metrics("Claim [S1]. Unknown [S99].", evidence, {evidence[0].document_id})
        self.assertEqual(citations["citation_validity"], 0.5)
        comparison = compare_outputs({"q": "Cable fault."}, {"q": "cable fault"})
        self.assertEqual(comparison["mean_token_f1"], 0.8)


if __name__ == "__main__":
    unittest.main()
