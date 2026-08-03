"""Validated, dependency-free schemas for benchmark evaluation records."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


RATING_DIMENSIONS = ("relevance", "professionalism", "completeness", "consistency")


def _required_text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


@dataclass(frozen=True)
class BenchmarkItem:
    question_id: str
    question_type: str
    prompt: str
    answer: Any = None
    acceptable_answers: tuple[Any, ...] = ()
    split: str = "test"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "question_id", _required_text(self.question_id, "question_id"))
        object.__setattr__(self, "prompt", _required_text(self.prompt, "prompt"))
        if self.question_type not in {"objective", "open_ended"}:
            raise ValueError("question_type must be 'objective' or 'open_ended'")
        if self.question_type == "objective" and self.answer is None and not self.acceptable_answers:
            raise ValueError("objective items require answer or acceptable_answers")
        if not isinstance(self.metadata, Mapping):
            raise ValueError("metadata must be a mapping")

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "BenchmarkItem":
        return cls(
            question_id=value.get("question_id", ""),
            question_type=value.get("question_type", ""),
            prompt=value.get("prompt") or value.get("question") or "",
            answer=value.get("answer"),
            acceptable_answers=tuple(value.get("acceptable_answers", ())),
            split=value.get("split", "test"),
            metadata=value.get("metadata", {}),
        )


@dataclass(frozen=True)
class ExpertRating:
    question_id: str
    rater_id: str
    scores: Mapping[str, float]
    protocol_version: str
    rationale: str = ""
    blind: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "question_id", _required_text(self.question_id, "question_id"))
        object.__setattr__(self, "rater_id", _required_text(self.rater_id, "rater_id"))
        object.__setattr__(self, "protocol_version", _required_text(self.protocol_version, "protocol_version"))
        missing = set(RATING_DIMENSIONS) - set(self.scores)
        unknown = set(self.scores) - set(RATING_DIMENSIONS)
        if missing or unknown:
            raise ValueError(f"rating dimensions mismatch; missing={sorted(missing)}, unknown={sorted(unknown)}")
        for dimension, score in self.scores.items():
            if isinstance(score, bool) or not isinstance(score, (int, float)) or not 1 <= score <= 5:
                raise ValueError(f"{dimension} must be a numeric 1-5 score")

    @classmethod
    def from_dict(cls, value: Mapping[str, Any], question_id: str | None = None) -> "ExpertRating":
        return cls(
            question_id=question_id or value.get("question_id", ""),
            rater_id=value.get("rater_id", ""),
            scores=value.get("scores") or value.get("ratings") or {},
            protocol_version=value.get("protocol_version", ""),
            rationale=value.get("rationale", ""),
            blind=value.get("blind", True),
        )


@dataclass(frozen=True)
class Prediction:
    question_id: str
    answer: Any
    model_id: str
    run_id: str
    ratings: tuple[ExpertRating, ...] = ()
    latency_seconds: float | None = None
    generated_tokens: int | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "question_id", _required_text(self.question_id, "question_id"))
        object.__setattr__(self, "model_id", _required_text(self.model_id, "model_id"))
        object.__setattr__(self, "run_id", _required_text(self.run_id, "run_id"))
        if self.latency_seconds is not None and self.latency_seconds < 0:
            raise ValueError("latency_seconds must be non-negative")
        if self.generated_tokens is not None and self.generated_tokens < 0:
            raise ValueError("generated_tokens must be non-negative")

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "Prediction":
        question_id = value.get("question_id", "")
        raw_ratings = value.get("expert_ratings", ())
        if not raw_ratings and isinstance(value.get("ratings"), Mapping):
            raw_ratings = ({
                "question_id": question_id,
                "rater_id": value.get("rater_id", "legacy-unspecified"),
                "protocol_version": value.get("protocol_version", "legacy-unspecified"),
                "scores": value["ratings"],
            },)
        return cls(
            question_id=question_id,
            answer=value.get("answer"),
            model_id=value.get("model_id", "unspecified"),
            run_id=value.get("run_id", "unspecified"),
            ratings=tuple(ExpertRating.from_dict(item, question_id) for item in raw_ratings),
            latency_seconds=value.get("latency_seconds"),
            generated_tokens=value.get("generated_tokens"),
            metadata=value.get("metadata", {}),
        )
