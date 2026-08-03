"""Strict, dependency-free schemas for corpus and benchmark records."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


LANGUAGES = frozenset({"en", "ja", "zh"})
DOMAINS = frozenset({"marine_engineering", "offshore_wind"})
QUESTION_TYPES = frozenset({"objective", "open_ended"})
DIFFICULTIES = frozenset({"easy", "medium", "hard"})
BENCHMARK_TASKS = {
    "marine_engineering": frozenset(
        {"mooring_analysis", "structural_load_assessment", "operation_diagnostics"}
    ),
    "offshore_wind": frozenset(
        {
            "turbine_reasoning",
            "project_design",
            "technical_document_generation",
            "component_classification",
            "fault_identification",
        }
    ),
}


class SchemaError(ValueError):
    """Raised when an input record violates a published data contract."""


def _nonempty(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SchemaError(f"{name} must be a non-empty string")
    return value.strip()


def _string_list(value: Any, name: str, *, minimum: int = 0) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)) or len(value) < minimum:
        raise SchemaError(f"{name} must contain at least {minimum} strings")
    result = tuple(_nonempty(item, f"{name}[]") for item in value)
    if len(set(result)) != len(result):
        raise SchemaError(f"{name} must not contain duplicates")
    return result


@dataclass(frozen=True, slots=True)
class CorpusRecord:
    document_id: str
    chunk_id: str
    text: str
    language: str
    domain: str
    task: str
    source_type: str
    source_uri: str
    content_sha256: str
    metadata: dict[str, Any] = field(default_factory=dict)
    token_count: int | None = None
    chunk_index: int = 0

    def __post_init__(self) -> None:
        for name in ("document_id", "chunk_id", "text", "task", "source_type", "source_uri"):
            _nonempty(getattr(self, name), name)
        if self.language not in LANGUAGES:
            raise SchemaError(f"unsupported language: {self.language!r}")
        if self.domain not in DOMAINS:
            raise SchemaError(f"unsupported domain: {self.domain!r}")
        if len(self.content_sha256) != 64 or any(c not in "0123456789abcdef" for c in self.content_sha256):
            raise SchemaError("content_sha256 must be a lowercase SHA-256 digest")
        if not isinstance(self.metadata, dict):
            raise SchemaError("metadata must be an object")
        if self.token_count is not None and self.token_count <= 0:
            raise SchemaError("token_count must be positive when present")
        if self.chunk_index < 0:
            raise SchemaError("chunk_index must be non-negative")

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "CorpusRecord":
        allowed = {field.name for field in cls.__dataclass_fields__.values()}
        unknown = sorted(set(value) - allowed)
        if unknown:
            raise SchemaError(f"unknown corpus fields: {unknown}")
        try:
            return cls(**dict(value))
        except TypeError as exc:
            raise SchemaError(str(exc)) from exc

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class BenchmarkRecord:
    question_id: str
    benchmark: str
    task: str
    language: str
    question_type: str
    question: str
    evidence_document_ids: tuple[str, ...]
    difficulty: str
    choices: tuple[str, ...] = ()
    answer: str | None = None
    reference_answer: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _nonempty(self.question_id, "question_id")
        _nonempty(self.question, "question")
        if self.benchmark not in BENCHMARK_TASKS:
            raise SchemaError(f"unsupported benchmark: {self.benchmark!r}")
        if self.task not in BENCHMARK_TASKS[self.benchmark]:
            raise SchemaError(f"unsupported task {self.task!r} for {self.benchmark!r}")
        if self.language not in LANGUAGES:
            raise SchemaError(f"unsupported language: {self.language!r}")
        if self.question_type not in QUESTION_TYPES:
            raise SchemaError(f"unsupported question_type: {self.question_type!r}")
        if self.difficulty not in DIFFICULTIES:
            raise SchemaError(f"unsupported difficulty: {self.difficulty!r}")
        _string_list(self.evidence_document_ids, "evidence_document_ids", minimum=1)
        if not isinstance(self.metadata, dict):
            raise SchemaError("metadata must be an object")
        if self.question_type == "objective":
            _string_list(self.choices, "choices", minimum=2)
            if self.answer not in self.choices:
                raise SchemaError("answer must exactly equal one choice")
            if self.reference_answer is not None:
                raise SchemaError("objective records must not define reference_answer")
        else:
            if self.choices or self.answer is not None:
                raise SchemaError("open-ended records must not define choices or answer")
            _nonempty(self.reference_answer, "reference_answer")

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "BenchmarkRecord":
        allowed = {field.name for field in cls.__dataclass_fields__.values()}
        unknown = sorted(set(value) - allowed)
        if unknown:
            raise SchemaError(f"unknown benchmark fields: {unknown}")
        data = dict(value)
        data["evidence_document_ids"] = _string_list(
            data.get("evidence_document_ids"), "evidence_document_ids", minimum=1
        )
        data["choices"] = _string_list(data.get("choices", ()), "choices")
        try:
            return cls(**data)
        except TypeError as exc:
            raise SchemaError(str(exc)) from exc

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["evidence_document_ids"] = list(self.evidence_document_ids)
        value["choices"] = list(self.choices)
        return value
