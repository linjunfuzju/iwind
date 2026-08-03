from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from iwind.instruction_tuning.config import load_config
from iwind.instruction_tuning.evaluation import aggregate_metrics, extract_generated_tokens, masked_token_accuracy
from iwind.instruction_tuning.sft_data import IGNORE_INDEX, SFTRecord, encode_messages, validate_messages


class FakeTokenizer:
    pad_token_id = 0

    def apply_chat_template(self, messages, tokenize, add_generation_prompt):
        del tokenize, add_generation_prompt
        ids = []
        role_ids = {"system": 10, "user": 20, "assistant": 30}
        for message in messages:
            ids.extend([role_ids[message["role"]], *[100 + ord(char) % 20 for char in message["content"]], 2])
        return ids


MESSAGES = [
    {"role": "system", "content": "expert"},
    {"role": "user", "content": "diagnose"},
    {"role": "assistant", "content": "bearing fault"},
]


class ValidationAndMaskingTests(unittest.TestCase):
    def test_strict_turn_validation(self) -> None:
        with self.assertRaises(ValueError):
            validate_messages([{"role": "assistant", "content": "orphan"}])
        record = SFTRecord.from_dict(
            {"sample_id": "s-1", "messages": MESSAGES, "language": "en", "task": "fault_identification"}
        )
        self.assertEqual(record.messages[-1]["role"], "assistant")

    def test_assistant_only_masking(self) -> None:
        encoded = encode_messages(MESSAGES, FakeTokenizer(), 100)
        first_supervised = encoded["labels"].index(30)
        self.assertTrue(all(label == IGNORE_INDEX for label in encoded["labels"][:first_supervised]))
        self.assertEqual(encoded["labels"][first_supervised:], encoded["input_ids"][first_supervised:])

    def test_assistant_tail_truncation_retains_supervision(self) -> None:
        encoded = encode_messages(MESSAGES, FakeTokenizer(), 8, truncation="assistant_tail")
        self.assertEqual(len(encoded["input_ids"]), 8)
        self.assertTrue(any(label != IGNORE_INDEX for label in encoded["labels"]))
        with self.assertRaises(ValueError):
            encode_messages(MESSAGES, FakeTokenizer(), 8, truncation="right")


class ConfigAndEvaluationTests(unittest.TestCase):
    def test_config_validation_and_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ("train.jsonl", "validation.jsonl"):
                (root / name).write_text("{}\n", encoding="utf-8")
            raw = {
                "model_name_or_path": "./model",
                "train_file": "train.jsonl",
                "validation_file": "validation.jsonl",
                "output_dir": "output",
                "max_length": 16,
                "lora_r": 4,
                "lora_alpha": 8,
                "lora_dropout": 0.1,
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
                "early_stopping_patience": 1,
                "seed": 1,
                "bf16": False,
            }
            path = root / "training.json"
            path.write_text(json.dumps(raw), encoding="utf-8")
            config = load_config(path)
            self.assertEqual(config.validation_file, (root / "validation.jsonl").resolve())
            self.assertEqual(config.model_name_or_path, str((root / "model").resolve()))

    def test_evaluation_helpers(self) -> None:
        self.assertEqual(masked_token_accuracy([1, 2, 3], [IGNORE_INDEX, 2, 4]), 0.5)
        self.assertEqual(extract_generated_tokens([1, 2, 3, 4], 2), [3, 4])
        self.assertEqual(aggregate_metrics([{"score": 1.0}, {"score": 0.0}]), {"score": 0.5})


if __name__ == "__main__":
    unittest.main()
