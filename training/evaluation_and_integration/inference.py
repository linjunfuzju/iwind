"""Runtime-neutral inference adapter contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, Sequence, runtime_checkable


@dataclass(frozen=True)
class GenerationRequest:
    prompt: str
    max_new_tokens: int = 512
    temperature: float = 0.0
    top_p: float = 1.0
    seed: int | None = None
    stop: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GenerationResult:
    text: str
    model_id: str
    prompt_tokens: int | None = None
    generated_tokens: int | None = None
    latency_seconds: float | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@runtime_checkable
class InferenceAdapter(Protocol):
    @property
    def model_id(self) -> str: ...

    def generate(self, requests: Sequence[GenerationRequest]) -> list[GenerationResult]: ...


class CallableInferenceAdapter:
    """Wrap a deterministic callback for tests or an application-owned runtime."""

    def __init__(self, model_id: str, callback: Any) -> None:
        self._model_id = model_id
        self._callback = callback

    @property
    def model_id(self) -> str:
        return self._model_id

    def generate(self, requests: Sequence[GenerationRequest]) -> list[GenerationResult]:
        return [GenerationResult(text=str(self._callback(request)), model_id=self.model_id) for request in requests]
