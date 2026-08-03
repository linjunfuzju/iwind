"""Evaluate pairwise ranking accuracy and accuracy by quality gap."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

try:
    from .reward_adapter import build_reward_adapter
    from .reward_data import format_pair
except ImportError:  # Support direct execution from this directory.
    from reward_adapter import build_reward_adapter
    from reward_data import format_pair


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-length", type=int, default=1024)
    parser.add_argument("--reward-adapter", choices=("scalar_logits", "quantile_mean"), default="scalar_logits")
    parser.add_argument("--reward-quantile-field", default="logits")
    args = parser.parse_args()
    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    if tokenizer.pad_token_id is None:
        if tokenizer.eos_token_id is None:
            raise ValueError("Reward tokenizer has neither pad_token_id nor eos_token_id")
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForSequenceClassification.from_pretrained(args.model, torch_dtype="auto", trust_remote_code=True)
    model.config.pad_token_id = tokenizer.pad_token_id
    model.eval()
    reward_adapter = build_reward_adapter(vars(args))
    device = next(model.parameters()).device
    counts = defaultdict(lambda: [0, 0])
    with args.data.open("r", encoding="utf-8") as handle, torch.inference_mode():
        for line in handle:
            record = json.loads(line)
            pair = format_pair(record, tokenizer, args.max_length)
            scores = []
            for prefix in ("chosen", "rejected"):
                ids = torch.tensor([pair[f"{prefix}_input_ids"]], device=device)
                mask = torch.tensor([pair[f"{prefix}_attention_mask"]], device=device)
                scores.append(float(reward_adapter(model(input_ids=ids, attention_mask=mask))[0]))
            gap = str(record.get("quality_gap", 1))
            counts[gap][1] += 1
            counts[gap][0] += int(scores[0] > scores[1])
    total_correct = sum(value[0] for value in counts.values())
    total = sum(value[1] for value in counts.values())
    result = {
        "overall": {"correct": total_correct, "total": total, "accuracy": total_correct / total if total else 0.0},
        "by_quality_gap": {
            gap: {"correct": value[0], "total": value[1], "accuracy": value[0] / value[1]}
            for gap, value in sorted(counts.items())
            if value[1]
        }
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
