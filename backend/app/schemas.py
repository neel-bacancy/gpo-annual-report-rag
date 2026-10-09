from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    top_k: int | None = Field(default=None, ge=1, le=20)


class Source(BaseModel):
    index: int  # matches [S#] in the answer
    chunk_id: str
    section: str
    page_start: int
    page_end: int
    similarity: float
    text: str
    cited: bool


class QueryResponse(BaseModel):
    question: str
    answer: str
    found: bool
    sources: list[Source]
    retrieval_ms: int
    generation_ms: int
    model: str


class HealthResponse(BaseModel):
    status: str
    chunks_indexed: int
    llm_model: str
    embedding_model: str
    top_k: int


class IngestResponse(BaseModel):
    chunks_indexed: int
    seconds: float
