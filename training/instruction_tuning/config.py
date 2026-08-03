"""Strict SFT configuration loading with config-relative path resolution."""

from __future__ import annotations

import json
from dataclasses import MISSING, dataclass, fields
from pathlib import Path


@dataclass(frozen=True, slots=True)
class SFTConfig:
    model_name_or_path: str
    train_file: Path
    validation_file: Path
    output_dir: Path
    max_length: int
    lora_r: int
    lora_alpha: int
    lora_dropout: float
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
    early_stopping_patience: int
    seed: int
    bf16: bool
    truncation: str = "assistant_tail"
    target_modules: tuple[str, ...] = (
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj",
    )

    def __post_init__(self) -> None:
        if not isinstance(self.model_name_or_path, str) or not self.model_name_or_path.strip():
            raise ValueError("model_name_or_path must be non-empty")
        for name in (
            "max_length",
            "lora_r",
            "lora_alpha",
            "per_device_train_batch_size",
            "per_device_eval_batch_size",
            "gradient_accumulation_steps",
            "logging_steps",
            "eval_steps",
            "save_steps",
            "save_total_limit",
            "early_stopping_patience",
        ):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise ValueError(f"{name} must be positive")
        if not isinstance(self.seed, int) or isinstance(self.seed, bool):
            raise ValueError("seed must be an integer")
        if not isinstance(self.bf16, bool):
            raise ValueError("bf16 must be a boolean")
        if not isinstance(self.lora_dropout, (int, float)) or isinstance(self.lora_dropout, bool) or not 0 <= self.lora_dropout < 1:
            raise ValueError("lora_dropout must be in [0, 1)")
        if not isinstance(self.warmup_ratio, (int, float)) or isinstance(self.warmup_ratio, bool) or not 0 <= self.warmup_ratio < 1:
            raise ValueError("dropout and warmup_ratio must be in [0, 1)")
        numeric = (self.learning_rate, self.num_train_epochs, self.weight_decay)
        if any(not isinstance(value, (int, float)) or isinstance(value, bool) for value in numeric):
            raise ValueError("optimizer and epoch settings must be numeric")
        if self.learning_rate <= 0 or self.num_train_epochs <= 0 or self.weight_decay < 0:
            raise ValueError("invalid optimizer or epoch configuration")
        if self.truncation not in {"right", "assistant_tail"}:
            raise ValueError("truncation must be 'right' or 'assistant_tail'")
        if not self.target_modules or any(not isinstance(item, str) or not item.strip() for item in self.target_modules):
            raise ValueError("target_modules must contain non-empty strings")


def _resolve(value: str, base: Path) -> Path:
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (base / path).resolve()


def _resolve_model(value: str, base: Path) -> str:
    if value.startswith((".", "~", "/")):
        return str(_resolve(value, base))
    return value


def load_config(path: Path, *, require_data_files: bool = True) -> SFTConfig:
    path = path.expanduser().resolve()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON config {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError("training config must be a JSON object")
    allowed = {field.name for field in fields(SFTConfig)}
    unknown = sorted(set(raw) - allowed)
    if unknown:
        raise ValueError(f"unknown config keys: {unknown}")
    required = {
        field.name
        for field in fields(SFTConfig)
        if field.default is MISSING and field.default_factory is MISSING
    }
    missing = sorted(required - raw.keys())
    if missing:
        raise ValueError(f"missing config keys: {missing}")
    for name in ("train_file", "validation_file", "output_dir"):
        if not isinstance(raw.get(name), str):
            raise ValueError(f"{name} must be a string path")
        raw[name] = _resolve(raw[name], path.parent)
    if isinstance(raw.get("model_name_or_path"), str):
        raw["model_name_or_path"] = _resolve_model(raw["model_name_or_path"], path.parent)
    if "target_modules" in raw:
        if not isinstance(raw["target_modules"], list):
            raise ValueError("target_modules must be a JSON array")
        raw["target_modules"] = tuple(raw["target_modules"])
    config = SFTConfig(**raw)
    if require_data_files:
        absent = [str(file) for file in (config.train_file, config.validation_file) if not file.is_file()]
        if absent:
            raise ValueError(f"data files do not exist: {absent}")
    return config
