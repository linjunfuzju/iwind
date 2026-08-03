"""Prompt loading and conversation formatting for GRPO."""

from __future__ import annotations

from datasets import Dataset


def prepare_dataset(dataset: Dataset, system_prompt: str) -> Dataset:
    def format_record(record):
        prompt = str(record.get("prompt", "")).strip()
        if not prompt:
            raise ValueError("Every GRPO record requires a non-empty prompt")
        result = dict(record)
        result.update({
            "prompt": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ]
        })
        return result

    return dataset.map(format_record)
