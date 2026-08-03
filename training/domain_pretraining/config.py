"""Strict configuration loading with config-relative path resolution."""

from __future__ import annotations

import json
from dataclasses import MISSING, dataclass, fields
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class PretrainingConfig:
    model_name_or_path: str
    train_file: Path
    validation_file: Path
    output_dir: Path
    max_length: int
    per_device_train_batch_size: int
    per_device_eval_batch_size: int
    gradient_accumulation_steps: int
    learning_rate: float
    num_train_epochs: float
    warmup_ratio: float
    weight_decay: float
    logging_steps: int
    eval_steps: int
    save_steps: int
    save_total_limit: int
    seed: int
    bf16: bool
    drop_remainder: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.model_name_or_path, str) or not self.model_name_or_path.strip():
            raise ValueError("model_name_or_path must be non-empty")
        for name in (
            "max_length",
            "per_device_train_batch_size",
            "per_device_eval_batch_size",
            "gradient_accumulation_steps",
            "logging_steps",
            "eval_steps",
            "save_steps",
            "save_total_limit",
        ):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise ValueError(f"{name} must be positive")
        if not isinstance(self.seed, int) or isinstance(self.seed, bool):
            raise ValueError("seed must be an integer")
        if not isinstance(self.bf16, bool) or not isinstance(self.drop_remainder, bool):
            raise ValueError("bf16 and drop_remainder must be booleans")
        if not isinstance(self.learning_rate, (int, float)) or isinstance(self.learning_rate, bool) or self.learning_rate <= 0:
            raise ValueError("learning_rate must be positive")
        if not isinstance(self.num_train_epochs, (int, float)) or isinstance(self.num_train_epochs, bool) or self.num_train_epochs <= 0:
            raise ValueError("learning_rate and num_train_epochs must be positive")
        if not isinstance(self.warmup_ratio, (int, float)) or isinstance(self.warmup_ratio, bool) or not 0 <= self.warmup_ratio < 1:
            raise ValueError("warmup_ratio must be in [0, 1)")
        if not isinstance(self.weight_decay, (int, float)) or isinstance(self.weight_decay, bool) or self.weight_decay < 0:
            raise ValueError("weight_decay must be non-negative")

    def as_training_dict(self) -> dict[str, Any]:
        result = {field.name: getattr(self, field.name) for field in fields(self)}
        for name in ("train_file", "validation_file", "output_dir"):
            result[name] = str(result[name])
        return result


def _resolve(value: str, base: Path) -> Path:
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (base / path).resolve()


def _resolve_model(value: str, base: Path) -> str:
    if value.startswith((".", "~", "/")):
        return str(_resolve(value, base))
    return value


def load_config(path: Path, *, require_data_files: bool = True) -> PretrainingConfig:
    path = path.expanduser().resolve()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON config {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError("training config must be a JSON object")
    allowed = {field.name for field in fields(PretrainingConfig)}
    unknown = sorted(set(raw) - allowed)
    missing = sorted(
        field.name
        for field in fields(PretrainingConfig)
        if field.default is MISSING and field.default_factory is MISSING and field.name not in raw
    )
    if unknown:
        raise ValueError(f"unknown config keys: {unknown}")
    if missing:
        raise ValueError(f"missing config keys: {missing}")
    for name in ("train_file", "validation_file", "output_dir"):
        if name in raw and not isinstance(raw[name], str):
            raise ValueError(f"{name} must be a string path")
        raw[name] = _resolve(raw[name], path.parent)
    if isinstance(raw.get("model_name_or_path"), str):
        raw["model_name_or_path"] = _resolve_model(raw["model_name_or_path"], path.parent)
    config = PretrainingConfig(**raw)
    if require_data_files:
        absent = [str(file) for file in (config.train_file, config.validation_file) if not file.is_file()]
        if absent:
            raise ValueError(f"data files do not exist: {absent}")
    return config
