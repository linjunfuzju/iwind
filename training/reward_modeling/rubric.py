"""Executable five-level rubric and preference-data validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


RUBRIC_LEVELS = {
    1: "unacceptable",
    2: "limited",
    3: "competent",
    4: "strong",
    5: "expert",
}

REQUIRED_RESPONSE_FIELDS = ("response_id", "text", "level")


@dataclass(frozen=True)
class RubricResponse:
    response_id: str
    text: str
    level: int
    annotator_id: str | None = None
    rationale: str | None = None

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "RubricResponse":
        missing = [key for key in REQUIRED_RESPONSE_FIELDS if key not in value]
        if missing:
            raise ValueError(f"Rubric response is missing fields: {missing}")
        response_id = str(value["response_id"]).strip()
        text = str(value["text"]).strip()
        level = value["level"]
        if not response_id or not text:
            raise ValueError("response_id and text must be non-empty")
        if isinstance(level, bool) or not isinstance(level, int) or level not in RUBRIC_LEVELS:
            raise ValueError(f"level must be one of {sorted(RUBRIC_LEVELS)}, received {level!r}")
        return cls(
            response_id=response_id,
            text=text,
            level=level,
            annotator_id=_optional_text(value.get("annotator_id")),
            rationale=_optional_text(value.get("rationale")),
        )


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def validate_question_group(record: dict[str, Any], require_multiple_levels: bool = True) -> dict[str, Any]:
    """Validate one question and return a normalized, metadata-preserving copy."""
    question_id = str(record.get("question_id", "")).strip()
    question = str(record.get("question", "")).strip()
    responses_value = record.get("responses")
    if not question_id or not question:
        raise ValueError("question_id and question must be non-empty")
    if not isinstance(responses_value, list) or len(responses_value) < 2:
        raise ValueError(f"Question {question_id!r} requires at least two responses")
    responses = [RubricResponse.from_mapping(value) for value in responses_value]
    response_ids = [response.response_id for response in responses]
    if len(response_ids) != len(set(response_ids)):
        raise ValueError(f"Question {question_id!r} has duplicate response_id values")
    if require_multiple_levels and len({response.level for response in responses}) < 2:
        raise ValueError(f"Question {question_id!r} has no ordered preference across rubric levels")
    normalized = dict(record)
    normalized["question_id"] = question_id
    normalized["question"] = question
    normalized["responses"] = [response.__dict__ for response in responses]
    return normalized


def validate_question_groups(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    seen = set()
    for record in records:
        group = validate_question_group(record)
        question_id = group["question_id"]
        if question_id in seen:
            raise ValueError(f"Duplicate question_id across groups: {question_id!r}")
        seen.add(question_id)
        normalized.append(group)
    if not normalized:
        raise ValueError("At least one question group is required")
    return normalized
