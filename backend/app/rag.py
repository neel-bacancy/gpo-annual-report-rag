"""The pipeline: ingest (load -> chunk -> embed -> store) and query (retrieve -> generate)."""

from __future__ import annotations

import time
from dataclasses import dataclass

from google import genai
from google.genai import types

from app.chunking import Chunk, chunk_pages
from app.config import Settings
from app.embeddings import Embedder
from app.generator import NOT_FOUND, Generator, cited_sources
from app.ingestion.loader import load_pdf
from app.vectorstore import Hit, VectorStore


@dataclass
class Answer:
    question: str
    answer: str
    hits: list[Hit]  # sources given to the LLM (passed the similarity threshold)
    retrieved: list[Hit]  # raw top-k, before thresholding (used for retrieval metrics)
    cited: list[int]  # 1-based indexes into hits
    found: bool
    retrieval_ms: int
    generation_ms: int
    model: str = ""


class RAGPipeline:
    def __init__(self, settings: Settings):
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not set (backend/.env)")
        self.settings = settings
        # Few SDK-level retries: on overload we'd rather fall back to another model than wait minutes.
        client = genai.Client(
            api_key=settings.gemini_api_key,
            http_options=types.HttpOptions(
                timeout=settings.llm_timeout_s * 1000,
                retry_options=types.HttpRetryOptions(attempts=2),
            ),
        )
        self.embedder = Embedder(settings, client)
        self.store = VectorStore(settings)
        self.generator = Generator(settings, client)

    # ---- ingestion -------------------------------------------------------
    def build_chunks(self) -> list[Chunk]:
        s = self.settings
        pages = load_pdf(s.pdf_path)
        return chunk_pages(pages, s.document_title, s.chunk_max_tokens, s.chunk_overlap_tokens, s.chunk_min_tokens)

    def ingest(self) -> list[Chunk]:
        chunks = self.build_chunks()
        vectors = self.embedder.embed_documents([c.text for c in chunks])
        self.store.rebuild(chunks, vectors)
        return chunks

    # ---- query -----------------------------------------------------------
    def retrieve(self, question: str, top_k: int | None = None) -> list[Hit]:
        vec = self.embedder.embed_query(question)
        return self.store.search(vec, top_k or self.settings.top_k)

    def answer(self, question: str, top_k: int | None = None) -> Answer:
        t0 = time.perf_counter()
        hits = self.retrieve(question, top_k)
        t1 = time.perf_counter()

        relevant = [h for h in hits if h.similarity >= self.settings.min_similarity]
        if not relevant:
            # Nothing similar enough: refuse instead of letting the LLM guess.
            return Answer(question, NOT_FOUND, [], hits, [], False, int((t1 - t0) * 1000), 0)

        text, model = self.generator.generate(question, relevant)
        t2 = time.perf_counter()
        return Answer(
            question=question,
            answer=text,
            hits=relevant,
            retrieved=hits,
            cited=cited_sources(text, len(relevant)),
            found=NOT_FOUND not in text,
            retrieval_ms=int((t1 - t0) * 1000),
            generation_ms=int((t2 - t1) * 1000),
            model=model,
        )
