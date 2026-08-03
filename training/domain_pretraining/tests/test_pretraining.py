from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from iwind.domain_pretraining.config import load_config
from iwind.domain_pretraining.evaluation import perplexity, weighted_mean_loss
from iwind.domain_pretraining.packing import pack_token_sequences, packing_statistics


class PackingTests(unittest.TestCase):
    def test_global_packing_preserves_remainder_and_boundaries(self) -> None:
        blocks = list(pack_token_sequences([[1, 2], [3, 4]], 3, separator_id=9))
        self.assertEqual([list(block.input_ids) for block in blocks], [[1, 2, 9], [3, 4]])
        self.assertEqual(blocks[0].source_indices, (0, 1))

    def test_drop_remainder(self) -> None:
        blocks = list(pack_token_sequences([[1, 2, 3, 4]], 3, drop_remainder=True))
        self.assertEqual([list(block.input_ids) for block in blocks], [[1, 2, 3]])
        self.assertEqual(packing_statistics(blocks, 3)["utilization"], 1.0)


class ConfigAndEvaluationTests(unittest.TestCase):
    def test_paths_are_relative_to_config(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "train.jsonl").write_text("{}\n", encoding="utf-8")
            (root / "validation.jsonl").write_text("{}\n", encoding="utf-8")
            raw = {
                "model_name_or_path": "model",
                "train_file": "train.jsonl",
                "validation_file": "validation.jsonl",
                "output_dir": "output",
                "max_length": 8,
                "per_device_train_batch_size": 1,
                "per_device_eval_batch_size": 1,
                "gradient_accumulation_steps": 1,
                "learning_rate": 0.001,
                "num_train_epochs": 1.0,
                "warmup_ratio": 0.0,
                "weight_decay": 0.0,
                "logging_steps": 1,
                "eval_steps": 1,
                "save_steps": 1,
                "save_total_limit": 1,
                "seed": 1,
                "bf16": False,
            }
            path = root / "training.json"
            path.write_text(json.dumps(raw), encoding="utf-8")
            config = load_config(path)
            self.assertEqual(config.train_file, (root / "train.jsonl").resolve())
            self.assertEqual(config.output_dir, (root / "output").resolve())

    def test_local_model_path_is_config_relative(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            raw = {
                "model_name_or_path": "./model",
                "train_file": "train.jsonl",
                "validation_file": "validation.jsonl",
                "output_dir": "output",
                "max_length": 8,
                "per_device_train_batch_size": 1,
                "per_device_eval_batch_size": 1,
                "gradient_accumulation_steps": 1,
                "learning_rate": 0.001,
                "num_train_epochs": 1.0,
                "warmup_ratio": 0.0,
                "weight_decay": 0.0,
                "logging_steps": 1,
                "eval_steps": 1,
                "save_steps": 1,
                "save_total_limit": 1,
                "seed": 1,
                "bf16": False,
            }
            path = root / "training.json"
            path.write_text(json.dumps(raw), encoding="utf-8")
            config = load_config(path, require_data_files=False)
            self.assertEqual(config.model_name_or_path, str((root / "model").resolve()))

    def test_evaluation_helpers(self) -> None:
        self.assertAlmostEqual(weighted_mean_loss([(1.0, 1), (2.0, 3)]), 1.75)
        self.assertEqual(perplexity(1000), float("inf"))


if __name__ == "__main__":
    unittest.main()
