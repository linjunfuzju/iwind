"""Optional OpenAI-compatible cited generation adapter."""

from __future__ import annotations

import os

try:
    from .context_and_citations import build_context, validate_citations
    from .rag_types import CitedAnswer, FusedEvidence
except ImportError:
    from context_and_citations import build_context, validate_citations
    from rag_types import CitedAnswer, FusedEvidence


SYSTEM_PROMPT = """You are the Iwind offshore wind and marine engineering assistant.
Use supplied evidence for factual claims and cite it with [S1], [S2], and similar identifiers.
Separate evidence, assumptions, uncertainty, and recommended actions. State when evidence is insufficient.
Do not invent measurements, standards, events, or citations."""


class GenerationClient:
    def __init__(self, base_url: str, model: str, api_key_env: str = "IWIND_MODEL_API_KEY") -> None:
        api_key = os.environ.get(api_key_env)
        if not api_key:
            raise ValueError(f"missing API key environment variable: {api_key_env}")
        try:
            from openai import OpenAI
        except ImportError as error:
            raise RuntimeError("OpenAI-compatible generation requires the optional openai dependency") from error
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model = model

    def answer(self, query: str, evidence: list[FusedEvidence], context_tokens: int = 6000) -> CitedAnswer:
        context = build_context(evidence, context_tokens)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Evidence:\n{context.text}\n\nQuestion:\n{query}"},
            ],
            temperature=0.2,
            top_p=0.9,
            max_tokens=1024,
        )
        answer = response.choices[0].message.content or ""
        validation = validate_citations(answer, context.evidence)
        if validation.invalid:
            raise ValueError(f"model returned unknown citations: {list(validation.invalid)}")
        return CitedAnswer(answer, validation.citations, context.evidence, validation)
