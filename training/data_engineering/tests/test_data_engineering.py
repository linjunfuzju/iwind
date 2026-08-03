from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from iwind.data_engineering.audit import audit_splits
from iwind.data_engineering.core import NearDuplicateIndex, chunk_text, sha256_text, stable_document_id
from iwind.data_engineering.evaluation import exact_match, token_f1
from iwind.data_engineering.schemas import BenchmarkRecord, CorpusRecord, SchemaError
from iwind.data_engineering.splits import grouped_split
from iwind.data_engineering.statistics import build_manifest, corpus_statistics


class CoreTests(unittest.TestCase):
    def test_stable_document_id_ignores_source_order(self) -> None:
        left = stable_document_id({"source_uri": "internal://manual/1"}, "First text")
        right = stable_document_id({"source_uri": "internal://manual/1"}, "Changed extraction")
        self.assertEqual(left, right)

    def test_token_chunking_is_deterministic_and_overlapping(self) -> None:
        chunks = chunk_text("one two three four five six", max_tokens=4, overlap_tokens=2)
        self.assertEqual([chunk.text for chunk in chunks], ["one two three four", "three four five six"])
        self.assertEqual([chunk.token_count for chunk in chunks], [4, 4])

    def test_near_duplicate_index(self) -> None:
        index = NearDuplicateIndex(threshold=0.5, shingle_size=2)
        index.add("a", "gearbox oil pressure alarm detected")
        match = index.find("gearbox oil pressure alarm observed")
        self.assertIsNotNone(match)
        self.assertEqual(match[0], "a")


class SchemaTests(unittest.TestCase):
    def test_corpus_schema_rejects_unknown_fields(self) -> None:
        value = {
            "document_id": "doc",
            "chunk_id": "doc:0",
            "text": "valid text",
            "language": "en",
            "domain": "offshore_wind",
            "task": "knowledge",
            "source_type": "manual",
            "source_uri": "internal://manual",
            "content_sha256": sha256_text("valid text"),
            "unexpected": True,
        }
        with self.assertRaises(SchemaError):
            CorpusRecord.from_dict(value)

    def test_benchmark_objective_contract(self) -> None:
        record = BenchmarkRecord.from_dict(
            {
                "question_id": "q-1",
                "benchmark": "offshore_wind",
                "task": "fault_identification",
                "language": "en",
                "question_type": "objective",
                "question": "Which alarm is most likely?",
                "evidence_document_ids": ["doc-1"],
                "difficulty": "medium",
                "choices": ["A", "B"],
                "answer": "B",
            }
        )
        self.assertEqual(record.answer, "B")


class SplitAndAuditTests(unittest.TestCase):
    def test_grouped_split_is_deterministic_and_nonempty_when_possible(self) -> None:
        sizes = {f"doc-{index}": index + 1 for index in range(6)}
        first = grouped_split(sizes, seed=7)
        second = grouped_split(sizes, seed=7)
        self.assertEqual(first, second)
        self.assertEqual(set(first.values()), {"train", "validation", "test"})

    def test_audit_detects_group_and_exact_contamination(self) -> None:
        records = {
            "train": [{"chunk_id": "a", "document_id": "doc", "text": "same content"}],
            "test": [{"chunk_id": "b", "document_id": "doc", "text": "same content"}],
        }
        kinds = {finding.kind for finding in audit_splits(records)}
        self.assertEqual(kinds, {"group", "exact"})


class StatisticsAndEvaluationTests(unittest.TestCase):
    def test_statistics_and_manifest_hash_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "data.jsonl"
            path.write_text(json.dumps({"text": "abc"}) + "\n", encoding="utf-8")
            stats = corpus_statistics([{"document_id": "d", "text": "abc", "language": "en"}])
            manifest = build_manifest(command="test", seed=1, inputs=[path], outputs=[], parameters={}, statistics=stats)
            self.assertEqual(manifest["inputs"][0]["bytes"], path.stat().st_size)
            self.assertEqual(len(manifest["inputs"][0]["sha256"]), 64)

    def test_text_metrics(self) -> None:
        self.assertEqual(exact_match(" Gear-box! ", "gear box"), 1.0)
        self.assertAlmostEqual(token_f1("a b", "a c"), 0.5)


if __name__ == "__main__":
    unittest.main()
