"""Strict conversation validation and assistant-only label construction."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence


ROLES = frozenset({"system", "user", "assistant"})
LANGUAGES = frozenset({"en", "ja", "zh"})
IGNORE_INDEX = -100


def validate_messages(messages: Any) -> tuple[dict[str, str], ...]:
    if not isinstance(messages, list) or not messages:
        raise ValueError("messages must be a non-empty list")
    validated = []
    previous = None
    for index, message in enumerate(messages):
        if not isinstance(message, dict) or set(message) != {"role", "content"}:
            raise ValueError(f"message {index} must contain exactly role and content")
        role, content = message["role"], message["content"]
        if role not in ROLES:
            raise ValueError(f"message {index} has unsupported role {role!r}")
        if not isinstance(content, str) or not content.strip():
            raise ValueError(f"message {index} content must be non-empty")
        if role == "system" and index != 0:
            raise ValueError("system messages are allowed only at index 0")
        if previous == role and role != "system":
            raise ValueError("consecutive user or assistant messages are not allowed")
        if role == "assistant" and previous != "user":
            raise ValueError("assistant messages must follow user messages")
        if role == "user" and previous not in {None, "system", "assistant"}:
            raise ValueError("user messages must begin or follow system/assistant messages")
        validated.append({"role": role, "content": content.strip()})
        previous = role
    if validated[-1]["role"] != "assistant":
        raise ValueError("the final message must be an assistant response")
    return tuple(validated)


@dataclass(frozen=True, slots=True)
class SFTRecord:
    sample_id: str
    messages: tuple[dict[str, str], ...]
    language: str
    task: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.sample_id, str) or not self.sample_id.strip():
            raise ValueError("sample_id must be non-empty")
        validate_messages(list(self.messages))
        if self.language not in LANGUAGES:
            raise ValueError(f"unsupported language: {self.language!r}")
        if not isinstance(self.task, str) or not self.task.strip():
            raise ValueError("task must be non-empty")
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be an object")

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "SFTRecord":
        allowed = {"sample_id", "messages", "language", "task", "metadata"}
        unknown = sorted(set(value) - allowed)
        if unknown:
            raise ValueError(f"unknown SFT fields: {unknown}")
        return cls(
            sample_id=value.get("sample_id"),
            messages=validate_messages(value.get("messages")),
            language=value.get("language"),
            task=value.get("task"),
            metadata=value.get("metadata", {}),
        )


def _template_ids(tokenizer: Any, messages: Sequence[dict[str, str]]) -> list[int]:
    ids = tokenizer.apply_chat_template(list(messages), tokenize=True, add_generation_prompt=False)
    if hasattr(ids, "tolist"):
        ids = ids.tolist()
    if not isinstance(ids, list) or any(not isinstance(token, int) for token in ids):
        raise TypeError("apply_chat_template must return a flat list of token IDs")
    return ids


def encode_messages(
    messages: list[dict[str, str]],
    tokenizer: Any,
    max_length: int,
    *,
    truncation: str = "assistant_tail",
) -> dict[str, list[int]]:
    """Serialize once per turn and retain labels only for assistant-added tokens."""
    if max_length <= 0:
        raise ValueError("max_length must be positive")
    validated = validate_messages(messages)
    input_ids: list[int] = []
    labels: list[int] = []
    previous_ids: list[int] = []
    for index, message in enumerate(validated):
        current_ids = _template_ids(tokenizer, validated[: index + 1])
        if current_ids[: len(previous_ids)] != previous_ids:
            raise ValueError("chat template is not prefix-stable across appended messages")
        new_ids = current_ids[len(previous_ids) :]
        input_ids.extend(new_ids)
        labels.extend(new_ids if message["role"] == "assistant" else [IGNORE_INDEX] * len(new_ids))
        previous_ids = current_ids

    if len(input_ids) > max_length:
        if truncation == "right":
            start = 0
        elif truncation == "assistant_tail":
            supervised = [index for index, label in enumerate(labels) if label != IGNORE_INDEX]
            if not supervised:
                raise ValueError("conversation contains no assistant tokens")
            end = supervised[-1] + 1
            start = max(0, end - max_length)
            if end - start < max_length:
                start = max(0, len(input_ids) - max_length)
            input_ids = input_ids[start : start + max_length]
            labels = labels[start : start + max_length]
            start = -1
        else:
            raise ValueError("truncation must be 'right' or 'assistant_tail'")
        if start == 0:
            input_ids = input_ids[:max_length]
            labels = labels[:max_length]
    if not input_ids or all(label == IGNORE_INDEX for label in labels):
        raise ValueError("the truncated conversation contains no assistant tokens")
    return {"input_ids": input_ids, "attention_mask": [1] * len(input_ids), "labels": labels}


@dataclass
class AssistantOnlyCollator:
    tokenizer: Any
    pad_to_multiple_of: int | None = None

    def __call__(self, features: list[dict[str, list[int]]]) -> dict[str, Any]:
        if not features:
            raise ValueError("features must be non-empty")
        if self.tokenizer.pad_token_id is None:
            raise ValueError("tokenizer.pad_token_id must be configured")
        max_length = max(len(feature["input_ids"]) for feature in features)
        if self.pad_to_multiple_of:
            max_length = ((max_length + self.pad_to_multiple_of - 1) // self.pad_to_multiple_of) * self.pad_to_multiple_of
        padded_ids, padded_masks, padded_labels = [], [], []
        for feature in features:
            length = len(feature["input_ids"])
            if len(feature["attention_mask"]) != length or len(feature["labels"]) != length:
                raise ValueError("input_ids, attention_mask, and labels must have equal lengths")
            padding = max_length - length
            padded_ids.append(feature["input_ids"] + [self.tokenizer.pad_token_id] * padding)
            padded_masks.append(feature["attention_mask"] + [0] * padding)
            padded_labels.append(feature["labels"] + [IGNORE_INDEX] * padding)
        try:
            import torch
        except ImportError as exc:
            raise RuntimeError("torch is required only when collating training batches") from exc
        return {
            "input_ids": torch.tensor(padded_ids, dtype=torch.long),
            "attention_mask": torch.tensor(padded_masks, dtype=torch.long),
            "labels": torch.tensor(padded_labels, dtype=torch.long),
        }
