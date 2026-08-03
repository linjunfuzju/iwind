"""Dataset and collator for pairwise reward-model training."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import torch


def format_pair(record: dict[str, Any], tokenizer, max_length: int) -> dict[str, Any]:
    question = str(record["question"]).strip()
    chosen = str(record["chosen"]).strip()
    rejected = str(record["rejected"]).strip()
    if not question or not chosen or not rejected:
        raise ValueError("question, chosen, and rejected must be non-empty")

    def encode(answer: str) -> dict[str, list[int]]:
        messages = [{"role": "user", "content": question}, {"role": "assistant", "content": answer}]
        encoded = tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=False,
            truncation=True,
            max_length=max_length,
        )
        return {"input_ids": encoded, "attention_mask": [1] * len(encoded)}

    chosen_tokens = encode(chosen)
    rejected_tokens = encode(rejected)
    result = dict(record)
    result.update({
        "chosen_input_ids": chosen_tokens["input_ids"],
        "chosen_attention_mask": chosen_tokens["attention_mask"],
        "rejected_input_ids": rejected_tokens["input_ids"],
        "rejected_attention_mask": rejected_tokens["attention_mask"],
        "quality_gap": int(record.get("quality_gap", 1)),
    })
    return result


@dataclass
class PairwiseRewardCollator:
    tokenizer: Any

    def _pad(self, values: list[list[int]], pad_value: int) -> torch.Tensor:
        width = max(len(value) for value in values)
        return torch.tensor([value + [pad_value] * (width - len(value)) for value in values], dtype=torch.long)

    def __call__(self, features: list[dict[str, Any]]) -> dict[str, Any]:
        if not features:
            raise ValueError("Cannot collate an empty reward batch")
        if self.tokenizer.pad_token_id is None:
            raise ValueError("tokenizer.pad_token_id must be configured before collation")
        tensor_keys = {
            "chosen_input_ids": self._pad([f["chosen_input_ids"] for f in features], self.tokenizer.pad_token_id),
            "chosen_attention_mask": self._pad([f["chosen_attention_mask"] for f in features], 0),
            "rejected_input_ids": self._pad([f["rejected_input_ids"] for f in features], self.tokenizer.pad_token_id),
            "rejected_attention_mask": self._pad([f["rejected_attention_mask"] for f in features], 0),
            "quality_gap": torch.tensor([int(f.get("quality_gap", 1)) for f in features], dtype=torch.long),
        }
        metadata_keys = sorted(set().union(*(feature.keys() for feature in features)) - set(tensor_keys))
        tensor_keys["metadata"] = [{key: feature.get(key) for key in metadata_keys} for feature in features]
        return tensor_keys
