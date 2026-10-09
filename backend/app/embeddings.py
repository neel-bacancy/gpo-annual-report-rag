"""Gemini embeddings with batching, retry on rate limits, and a disk cache.

- Documents and queries use different task types (RETRIEVAL_DOCUMENT vs
  RETRIEVAL_QUERY); gemini-embedding-001 is trained for that asymmetry.
- At 768 dims the vectors are truncated (Matryoshka), so we re-normalise them.
- The free tier rate-limits aggressively; the cache means re-running ingestion
  after a chunking tweak only embeds chunks whose text actually changed.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from pathlib import Path

from google import genai
from google.genai import errors, types

from app.config import Settings

_BATCH = 50


def _normalise(v: list[float]) -> list[float]:
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


class Embedder:
    def __init__(self, settings: Settings, client: genai.Client):
        self.client = client
        self.model = settings.embedding_model
        self.dim = settings.embedding_dim
        self.cache_path = Path(settings.cache_dir) / f"embeddings_{self.model}_{self.dim}.jsonl"
        self._cache: dict[str, list[float]] = {}
        if self.cache_path.exists():
            for line in self.cache_path.read_text(encoding="utf-8").splitlines():
                rec = json.loads(line)
                self._cache[rec["key"]] = rec["vector"]

    def _key(self, text: str, task: str) -> str:
        return hashlib.sha256(f"{task}\x00{text}".encode()).hexdigest()

    def _call(self, texts: list[str], task: str) -> list[list[float]]:
        delay = 5.0
        for attempt in range(6):
            try:
                res = self.client.models.embed_content(
                    model=self.model,
                    contents=texts,
                    config=types.EmbedContentConfig(task_type=task, output_dimensionality=self.dim),
                )
                return [_normalise(e.values) for e in res.embeddings]
            except errors.APIError as e:
                if e.code in (429, 500, 503) and attempt < 5:
                    print(f"  embedding API {e.code}; retrying in {delay:.0f}s")
                    time.sleep(delay)
                    delay = min(delay * 2, 60)
                    continue
                raise
        raise RuntimeError("unreachable")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embed(texts, "RETRIEVAL_DOCUMENT", cache=True)

    def embed_query(self, text: str) -> list[float]:
        return self._embed([text], "RETRIEVAL_QUERY", cache=False)[0]

    def _embed(self, texts: list[str], task: str, cache: bool) -> list[list[float]]:
        keys = [self._key(t, task) for t in texts]
        missing = [i for i, k in enumerate(keys) if k not in self._cache] if cache else list(range(len(texts)))
        fresh: dict[int, list[float]] = {}
        for start in range(0, len(missing), _BATCH):
            idx = missing[start:start + _BATCH]
            for i, vec in zip(idx, self._call([texts[i] for i in idx], task)):
                fresh[i] = vec
        if cache and fresh:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            with self.cache_path.open("a", encoding="utf-8") as f:
                for i, vec in fresh.items():
                    self._cache[keys[i]] = vec
                    f.write(json.dumps({"key": keys[i], "vector": vec}) + "\n")
        return [fresh[i] if i in fresh else self._cache[keys[i]] for i in range(len(texts))]
