from __future__ import annotations

import unittest
import sys
import types
from types import SimpleNamespace
from unittest.mock import Mock, patch

import torch

datasets_stub = types.ModuleType("datasets")
datasets_stub.load_dataset = Mock()
transformers_stub = types.ModuleType("transformers")


class TrainerStub:
    pass


transformers_stub.Trainer = TrainerStub
transformers_stub.AutoModelForSequenceClassification = Mock()
transformers_stub.AutoTokenizer = Mock()
transformers_stub.EarlyStoppingCallback = Mock()
transformers_stub.TrainingArguments = Mock()
transformers_stub.set_seed = Mock()
trainer_utils_stub = types.ModuleType("transformers.trainer_utils")
trainer_utils_stub.get_last_checkpoint = Mock()
sys.modules.setdefault("datasets", datasets_stub)
sys.modules.setdefault("transformers", transformers_stub)
sys.modules.setdefault("transformers.trainer_utils", trainer_utils_stub)

from iwind.reward_modeling.reward_adapter import ScalarLogitsAdapter
from iwind.reward_modeling.train_reward_model import PairwiseRewardTrainer


class PairwiseTrainerPredictionTest(unittest.TestCase):
    def test_prediction_step_returns_pair_scores_and_gap_labels(self):
        trainer = object.__new__(PairwiseRewardTrainer)
        trainer.reward_adapter = ScalarLogitsAdapter()
        trainer._prepare_inputs = lambda value: value
        trainer.compute_loss_context_manager = Mock(return_value=torch.no_grad())
        model = Mock(side_effect=[SimpleNamespace(logits=torch.tensor([[3.0], [1.0]])), SimpleNamespace(logits=torch.tensor([[2.0], [2.0]]))])
        inputs = {
            "chosen_input_ids": torch.ones(2, 1, dtype=torch.long),
            "chosen_attention_mask": torch.ones(2, 1, dtype=torch.long),
            "rejected_input_ids": torch.ones(2, 1, dtype=torch.long),
            "rejected_attention_mask": torch.ones(2, 1, dtype=torch.long),
            "quality_gap": torch.tensor([1, 4]),
            "metadata": [{"pair_id": "a"}, {"pair_id": "b"}],
        }
        loss, scores, labels = trainer.prediction_step(model, inputs, False)
        self.assertEqual(tuple(scores.shape), (2, 2))
        self.assertEqual(labels.tolist(), [[0, 1], [0, 4]])
        self.assertTrue(torch.isfinite(loss))


if __name__ == "__main__":
    unittest.main()
