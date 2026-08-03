from __future__ import annotations

import unittest

from iwind.evaluation_and_integration.evaluation import compare_sft_grpo, evaluate, normalize_objective
from iwind.evaluation_and_integration.schemas import BenchmarkItem, ExpertRating, Prediction
from iwind.evaluation_and_integration.statistics import paired_comparison, wilson_interval


def prediction(identifier: str, answer: object, score: float = 4, model: str = "model") -> Prediction:
    ratings = () if identifier == "objective" else (ExpertRating(
        identifier, "expert-1", {name: score for name in ("relevance", "professionalism", "completeness", "consistency")}, "v1"
    ),)
    return Prediction(identifier, answer, model, "run-1", ratings)


class EvaluationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.items = [
            BenchmarkItem("objective", "objective", "Select", "A", ("Alpha",)),
            BenchmarkItem("open", "open_ended", "Explain"),
        ]

    def test_objective_normalization_and_intervals(self) -> None:
        self.assertEqual(normalize_objective("  ALPHA\n"), "alpha")
        report = evaluate(self.items, {
            "objective": prediction("objective", " alpha "),
            "open": prediction("open", "answer"),
        })
        self.assertEqual(report["objective"]["accuracy"], 1.0)
        low, high = report["objective"]["wilson_95"]
        self.assertLess(low, high)
        self.assertLessEqual(high, 1.0)

    def test_paired_sft_grpo_direction(self) -> None:
        sft = {"objective": prediction("objective", "wrong", model="sft"), "open": prediction("open", "a", 3, "sft")}
        grpo = {"objective": prediction("objective", "A", model="grpo"), "open": prediction("open", "b", 4, "grpo")}
        report = compare_sft_grpo(self.items, sft, grpo, seed=9)
        self.assertEqual(report["paired_objective"]["mean_delta"], 1.0)
        self.assertEqual(report["paired_ratings"]["relevance"]["mean_delta"], 1)

    def test_invalid_rating_and_statistics_inputs_fail(self) -> None:
        with self.assertRaises(ValueError):
            prediction("open", "a", 6)
        with self.assertRaises(ValueError):
            wilson_interval(2, 1)
        with self.assertRaises(ValueError):
            paired_comparison([1], [])


if __name__ == "__main__":
    unittest.main()
