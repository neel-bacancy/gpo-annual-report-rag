"""All tunable settings in one place. Override any field via environment or backend/.env."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    # Gemini
    gemini_api_key: str = ""
    llm_model: str = "gemini-3.5-flash"
    # Tried in order when the primary model is overloaded (503) or rate-limited (429) on the free tier.
    llm_fallback_models: list[str] = ["gemini-3.5-flash-lite"]
    embedding_model: str = "gemini-embedding-001"
    embedding_dim: int = 768  # gemini-embedding-001 supports 768/1536/3072 (MRL)
    llm_temperature: float = 0.1
    llm_thinking_level: str = "low"  # Gemini 3: "low" keeps latency down; "high" for harder reasoning
    llm_timeout_s: int = 60

    # Source + storage
    pdf_path: Path = BACKEND_DIR / "data" / "raw" / "gpo_annual_report.pdf"
    chroma_dir: Path = BACKEND_DIR / "data" / "chroma"
    cache_dir: Path = BACKEND_DIR / "data" / "cache"
    collection_name: str = "gpo_annual_report_2018"
    document_title: str = "GPO 2018 Annual Report"

    # Chunking (approximate tokens; see chunking.py)
    chunk_max_tokens: int = 500
    chunk_overlap_tokens: int = 75
    chunk_min_tokens: int = 120

    # Retrieval
    top_k: int = 5
    # Calibrated on eval set: in-scope top-1 >= 0.658, off-topic (q15) <= 0.512. See README.
    min_similarity: float = 0.60

    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
