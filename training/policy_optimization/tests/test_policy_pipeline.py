from __future__ import annotations

import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import torch

transformers_stub = types.ModuleType("transformers")


class TrainerCallbackStub:
    pass


transformers_stub.TrainerCallback = TrainerCallbackStub
transformers_stub.AutoModelForSequenceClassification = Mock()
transformers_stub.AutoTokenizer = Mock()
trainer_utils_stub = types.ModuleType("transformers.trainer_utils")
trainer_utils_stub.get_last_checkpoint = Mock(return_value=None)
sys.modules.setdefault("transformers", transformers_stub)
sys.modules.setdefault("transformers.trainer_utils", trainer_utils_stub)

from iwind.policy_optimization.grpo_utils import comparative_evaluation, export_evaluation, resolve_resume_checkpoint, validate_grpo_config
from iwind.policy_optimization.reward_client import HTTPRewardClient, TRLRewardFunction, resolve_reward_device, validate_scores


class PolicyPipelineTest(unittest.TestCase):
    def config(self):
        return {
            "policy_model_path": "policy",
            "reward_model_path": "reward",
            "reward_transport": "local",
            "train_file": "train.jsonl",
            "validation_file": "validation.jsonl",
            "output_dir": "out",
            "num_generations": 4,
            "per_device_train_batch_size": 4,
            "gradient_accumulation_steps": 1,
            "temperature": 0.7,
            "top_p": 0.9,
            "max_prompt_length": 32,
            "max_completion_length": 64,
        }

    def test_grpo_config_rejects_invalid_group_batch_and_http_endpoint(self):
        config = self.config()
        config["num_generations"] = 3
        with self.assertRaisesRegex(ValueError, "Global train batch"):
            validate_grpo_config(config, world_size=1)
        config = self.config()
        config["per_device_eval_batch_size"] = 2
        with self.assertRaisesRegex(ValueError, "Global evaluation batch"):
            validate_grpo_config(config, world_size=1)
        config = self.config()
        config["reward_transport"] = "http"
        with self.assertRaisesRegex(ValueError, "reward_endpoint"):
            validate_grpo_config(config, world_size=1)

    def test_rank_device_mapping_is_explicit(self):
        with patch("iwind.policy_optimization.reward_client.torch.cuda.is_available", return_value=True), patch(
            "iwind.policy_optimization.reward_client.torch.cuda.device_count", return_value=4
        ):
            self.assertEqual(str(resolve_reward_device("rank", local_rank=2)), "cuda:2")

    def test_named_trl_wrapper_forwards_row_metadata(self):
        client = Mock()
        client.score.return_value = [1.0]
        reward = TRLRewardFunction(client)
        result = reward(["p"], ["c"], sample_id=["s1"], ignored="scalar")
        self.assertEqual(reward.__name__, "domain_reward")
        self.assertEqual(result, [1.0])
        client.score.assert_called_once_with(["p"], ["c"], [{"sample_id": "s1"}])

    def test_http_client_validates_response(self):
        response = Mock()
        response.read.return_value = json.dumps({"scores": [1.25]}).encode()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        with patch("iwind.policy_optimization.reward_client.urllib.request.urlopen", return_value=response):
            scores = HTTPRewardClient("http://localhost/score", retries=0).score(["p"], ["c"])
        self.assertEqual(scores, [1.25])
        with self.assertRaisesRegex(ValueError, "non-finite"):
            validate_scores([float("nan")], 1)

    def test_comparative_evaluation_and_export(self):
        reward = Mock(return_value=[1.0, 2.0])
        result = comparative_evaluation(
            [{"sample_id": "s", "prompt": "p"}],
            lambda prompt: "baseline",
            lambda prompt: "policy",
            reward,
        )
        self.assertEqual(result["summary"]["policy_win_rate"], 1.0)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            export_evaluation(result, output)
            self.assertEqual(json.loads(output.read_text())["summary"]["mean_reward_delta"], 1.0)

    def test_explicit_resume_path_must_exist(self):
        with self.assertRaisesRegex(ValueError, "does not exist"):
            resolve_resume_checkpoint("out", "/missing/checkpoint")


if __name__ == "__main__":
    unittest.main()
