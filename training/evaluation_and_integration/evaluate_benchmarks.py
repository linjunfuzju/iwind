"""Evaluate one model or perform a paired SFT-versus-GRPO comparison."""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from .artifacts import atomic_write_json, read_jsonl
    from .evaluation import compare_sft_grpo, evaluate
    from .schemas import BenchmarkItem, Prediction
except ImportError:  # Direct script execution.
    from artifacts import atomic_write_json, read_jsonl
    from evaluation import compare_sft_grpo, evaluate
    from schemas import BenchmarkItem, Prediction


def load_benchmark(path: Path) -> list[BenchmarkItem]:
    return [BenchmarkItem.from_dict(record) for record in read_jsonl(path)]


def load_predictions(path: Path) -> dict[str, Prediction]:
    records = [Prediction.from_dict(record) for record in read_jsonl(path)]
    result = {record.question_id: record for record in records}
    if len(result) != len(records):
        raise ValueError(f"duplicate question_id in {path}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--predictions", type=Path)
    parser.add_argument("--sft-predictions", type=Path)
    parser.add_argument("--grpo-predictions", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bootstrap-seed", type=int, default=0)
    args = parser.parse_args()
    benchmark = load_benchmark(args.benchmark)
    if args.predictions and not (args.sft_predictions or args.grpo_predictions):
        report = evaluate(benchmark, load_predictions(args.predictions), args.bootstrap_seed)
    elif args.sft_predictions and args.grpo_predictions and not args.predictions:
        report = compare_sft_grpo(
            benchmark,
            load_predictions(args.sft_predictions),
            load_predictions(args.grpo_predictions),
            args.bootstrap_seed,
        )
    else:
        parser.error("provide either --predictions or both --sft-predictions and --grpo-predictions")
    atomic_write_json(args.output, report)


if __name__ == "__main__":
    main()
