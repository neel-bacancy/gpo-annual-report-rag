"""FastAPI app. Run: uvicorn app.main:app --reload --port 8000 (from backend/)."""

from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google.genai import errors as genai_errors

from app.config import get_settings
from app.rag import RAGPipeline
from app.schemas import HealthResponse, IngestResponse, QueryRequest, QueryResponse, Source

settings = get_settings()
pipeline: RAGPipeline | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global pipeline
    pipeline = RAGPipeline(settings)
    yield


app = FastAPI(title="GPO Annual Report RAG", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["*"], allow_headers=["*"])


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        chunks_indexed=pipeline.store.count(),
        llm_model=settings.llm_model,
        embedding_model=settings.embedding_model,
        top_k=settings.top_k,
    )


@app.post("/api/ingest", response_model=IngestResponse)
def ingest() -> IngestResponse:
    t0 = time.perf_counter()
    chunks = pipeline.ingest()
    return IngestResponse(chunks_indexed=len(chunks), seconds=round(time.perf_counter() - t0, 1))


@app.post("/api/query", response_model=QueryResponse)
def query(req: QueryRequest) -> QueryResponse:
    if pipeline.store.count() == 0:
        raise HTTPException(409, "Index is empty. Run `python -m scripts.ingest` first.")
    try:
        result = pipeline.answer(req.question, req.top_k)
    except genai_errors.APIError as e:
        status = 429 if e.code == 429 else 502
        raise HTTPException(status, f"Gemini API error: {e.message}") from e

    return QueryResponse(
        question=result.question,
        answer=result.answer,
        found=result.found,
        sources=[
            Source(
                index=i,
                chunk_id=h.id,
                section=h.section,
                page_start=h.page_start,
                page_end=h.page_end,
                similarity=round(h.similarity, 4),
                text=h.body,
                cited=i in result.cited,
            )
            for i, h in enumerate(result.hits, 1)
        ],
        retrieval_ms=result.retrieval_ms,
        generation_ms=result.generation_ms,
        model=result.model,
    )
