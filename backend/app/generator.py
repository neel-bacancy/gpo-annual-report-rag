"""Prompt construction and Gemini answer generation."""

from __future__ import annotations

import re

from google import genai
from google.genai import errors, types

from app.config import Settings
from app.vectorstore import Hit

NOT_FOUND = "I couldn't find this information in the GPO 2018 Annual Report."

SYSTEM_PROMPT = f"""You answer questions about the U.S. Government Publishing Office (GPO) 2018 Annual Report \
(fiscal year ended September 30, 2018) using ONLY the numbered sources provided.

Rules:
- Use only facts stated in the sources. Do not use outside knowledge.
- Cite every factual sentence with its source number in square brackets, e.g. [S2] or [S1][S3].
- Copy numbers exactly as written, including units. Financial tables are often "in thousands": \
say so or convert correctly (e.g. 644,807 thousand = $644.8 million).
- Table rows are written as "label   value_2018   value_2017" when a table has 2018 and 2017 columns.
- If the sources do not contain the answer, reply exactly: "{NOT_FOUND}"
- If the sources only partly answer the question, answer that part and say what is missing.
- Be concise: a direct answer first, then brief supporting detail if useful."""


def build_context(hits: list[Hit]) -> str:
    blocks = []
    for i, h in enumerate(hits, 1):
        pages = f"p. {h.page_start}" if h.page_start == h.page_end else f"pp. {h.page_start}-{h.page_end}"
        blocks.append(f"[S{i}] ({pages}; section: {h.section or 'n/a'})\n{h.body}")
    return "\n\n---\n\n".join(blocks)


def cited_sources(answer: str, n_sources: int) -> list[int]:
    """Source numbers the answer actually cites, in order of first appearance (1-based)."""
    seen: list[int] = []
    for m in re.finditer(r"\[S(\d+)\]", answer):
        i = int(m.group(1))
        if 1 <= i <= n_sources and i not in seen:
            seen.append(i)
    return seen


class Generator:
    def __init__(self, settings: Settings, client: genai.Client):
        self.client = client
        self.models = [settings.llm_model, *settings.llm_fallback_models]
        self.thinking = types.ThinkingConfig(thinking_level=settings.llm_thinking_level)
        self.config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=settings.llm_temperature,
            thinking_config=self.thinking,
        )

    def complete(self, contents: str, config: types.GenerateContentConfig) -> tuple[str, str]:
        """Call the primary model, falling back on overload/rate-limit. Returns (text, model used)."""
        for i, model in enumerate(self.models):
            try:
                res = self.client.models.generate_content(model=model, contents=contents, config=config)
                return (res.text or "").strip(), model
            except errors.APIError as e:
                if e.code in (429, 503) and i < len(self.models) - 1:
                    continue
                raise
        raise RuntimeError("no models configured")

    def generate(self, question: str, hits: list[Hit]) -> tuple[str, str]:
        prompt = f"Sources:\n\n{build_context(hits)}\n\nQuestion: {question}"
        return self.complete(prompt, self.config)
