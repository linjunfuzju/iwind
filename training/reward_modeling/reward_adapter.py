"""Boundary between model-specific reward outputs and scalar consumers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import torch


class RewardOutputAdapter(Protocol):
    def __call__(self, outputs: Any) -> torch.Tensor: ...


def _field(outputs: Any, name: str) -> Any:
    if isinstance(outputs, dict):
        return outputs.get(name)
    return getattr(outputs, name, None)


@dataclass(frozen=True)
class ScalarLogitsAdapter:
    """Accept only one logit per sequence."""

    def __call__(self, outputs: Any) -> torch.Tensor:
        logits = _field(outputs, "logits")
        if not isinstance(logits, torch.Tensor):
            raise TypeError("Reward output does not expose tensor logits")
        if logits.ndim == 1:
            return logits
        if logits.ndim == 2 and logits.shape[-1] == 1:
            return logits[:, 0]
        raise ValueError(f"Scalar adapter expected logits [batch] or [batch, 1], received {tuple(logits.shape)}")


@dataclass(frozen=True)
class QuantileMeanAdapter:
    """Explicit fallback for QRM revisions whose logits are ordered quantile values."""

    field: str = "logits"

    def __call__(self, outputs: Any) -> torch.Tensor:
        quantiles = _field(outputs, self.field)
        if not isinstance(quantiles, torch.Tensor) or quantiles.ndim != 2 or quantiles.shape[-1] < 2:
            shape = tuple(quantiles.shape) if isinstance(quantiles, torch.Tensor) else None
            raise ValueError(f"Quantile adapter expected [{'{'}batch{'}'}, quantiles] tensor in {self.field!r}, received {shape}")
        return quantiles.float().mean(dim=-1)


def build_reward_adapter(config: dict[str, Any]) -> RewardOutputAdapter:
    kind = config.get("reward_adapter", "scalar_logits")
    if kind == "scalar_logits":
        return ScalarLogitsAdapter()
    if kind == "quantile_mean":
        return QuantileMeanAdapter(field=config.get("reward_quantile_field", "logits"))
    raise ValueError(f"Unsupported reward_adapter {kind!r}; expected scalar_logits or quantile_mean")
