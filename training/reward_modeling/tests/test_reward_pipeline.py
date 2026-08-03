from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import torch

from iwind.reward_modeling.prepare_preferences import deterministic_group_split, expand_question_group, prepare
from iwind.reward_modeling.reward_adapter import QuantileMeanAdapter, ScalarLogitsAdapter
from iwind.reward_modeling.reward_data import PairwiseRewardCollator, format_pair
from iwind.reward_modeling.reward_metrics import pairwise_reward_metrics
from iwind.reward_modeling.rubric import validate_question_group, validate_question_groups


class FakeTokenizer:
    pad_token_id = 0

    def apply_chat_template(self, messages, **kwargs):
        return [len(messages[0]["content"]), len(messages[1]["content"])]


class RewardPipelineTest(unittest.TestCase):
    def group(self):
        return {
            "question_id": "q-1",
            "question": "Assess the load case.",
            "task": "loads",
            "language": "en",
            "responses": [
                {"response_id": "r1", "text": "weak", "level": 1, "annotator_id": "a"},
                {"response_id": "r3", "text": "adequate", "level": 3, "annotator_id": "b"},
                {"response_id": "r5", "text": "expert", "level": 5, "annotator_id": "c"},
            ],
        }

    def test_question_validation_rejects_duplicate_ids_and_levels_outside_rubric(self):
        group = self.group()
        group["responses"][1]["response_id"] = "r1"
        with self.assertRaisesRegex(ValueError, "duplicate response_id"):
            validate_question_group(group)
        group = self.group()
        group["responses"][0]["level"] = 0
        with self.assertRaisesRegex(ValueError, "level must be"):
            validate_question_group(group)

    def test_cross_group_duplicate_question_id_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate question_id"):
            validate_question_groups([self.group(), self.group()])

    def test_split_is_deterministic_and_pair_expansion_preserves_metadata(self):
        self.assertEqual(
            deterministic_group_split("q-1", 42, 0.8, 0.1),
            deterministic_group_split("q-1", 42, 0.8, 0.1),
        )
        pairs = expand_question_group(validate_question_group(self.group()))
        self.assertEqual(len(pairs), 3)
        self.assertEqual({pair["quality_gap"] for pair in pairs}, {2, 4})
        self.assertTrue(all(pair["question_id"] == "q-1" and pair["task"] == "loads" for pair in pairs))
        self.assertTrue(all(pair["chosen_level"] > pair["rejected_level"] for pair in pairs))

    def test_prepare_writes_manifest_and_keeps_each_group_in_one_split(self):
        groups = []
        for index in range(30):
            group = self.group()
            group["question_id"] = f"q-{index}"
            groups.append(group)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "groups.jsonl"
            source.write_text("".join(json.dumps(group) + "\n" for group in groups), encoding="utf-8")
            manifest = prepare(source, root / "out", 7, 0.7, 0.2)
            assigned = [question_id for split in manifest["partitions"].values() for question_id in split["question_ids"]]
            self.assertCountEqual(assigned, [group["question_id"] for group in groups])
            self.assertEqual(len(assigned), len(set(assigned)))
            self.assertTrue((root / "out" / "manifest.json").is_file())

    def test_format_and_collator_preserve_metadata_and_quality_gap(self):
        record = {"question": "question", "chosen": "best", "rejected": "bad", "quality_gap": 4, "pair_id": "p1"}
        formatted = format_pair(record, FakeTokenizer(), 16)
        batch = PairwiseRewardCollator(FakeTokenizer())([formatted])
        self.assertEqual(batch["quality_gap"].tolist(), [4])
        self.assertEqual(batch["metadata"][0]["pair_id"], "p1")

    def test_adapters_are_explicit_about_output_shape(self):
        self.assertEqual(ScalarLogitsAdapter()(SimpleNamespace(logits=torch.tensor([[2.0]]))).tolist(), [2.0])
        self.assertEqual(QuantileMeanAdapter()(SimpleNamespace(logits=torch.tensor([[1.0, 3.0]]))).tolist(), [2.0])
        with self.assertRaisesRegex(ValueError, "Scalar adapter"):
            ScalarLogitsAdapter()(SimpleNamespace(logits=torch.ones(2, 3)))

    def test_pairwise_metrics_include_gap_accuracy(self):
        prediction = SimpleNamespace(
            predictions=np.array([[2.0, 1.0], [0.0, 1.0]]),
            label_ids=np.array([[0, 1], [0, 3]]),
        )
        metrics = pairwise_reward_metrics(prediction)
        self.assertEqual(metrics["accuracy"], 0.5)
        self.assertEqual(metrics["accuracy_gap_1"], 1.0)
        self.assertEqual(metrics["accuracy_gap_3"], 0.0)


if __name__ == "__main__":
    unittest.main()
