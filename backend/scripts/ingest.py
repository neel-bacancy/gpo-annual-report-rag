"""Build the vector index from the PDF.

Usage (from backend/):
    python -m scripts.ingest              # load, chunk, embed, store
    python -m scripts.ingest --dry-run    # load + chunk only; writes data/chunks.jsonl for inspection
"""

import argparse
import json
import statistics
import time
from dataclasses import asdict

from app.config import BACKEND_DIR, get_settings
from app.chunking import chunk_pages
from app.ingestion.loader import load_pdf


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="skip embedding; just write chunks.jsonl")
    args = parser.parse_args()
    s = get_settings()

    t0 = time.perf_counter()
    pages = load_pdf(s.pdf_path)
    chunks = chunk_pages(pages, s.document_title, s.chunk_max_tokens, s.chunk_overlap_tokens, s.chunk_min_tokens)
    sizes = [c.tokens for c in chunks]
    print(f"Loaded {len(pages)} pages -> {len(chunks)} chunks "
          f"(tokens min {min(sizes)}, median {statistics.median(sizes):.0f}, max {max(sizes)}; "
          f"{sum(c.has_table for c in chunks)} with tables)")

    out = BACKEND_DIR / "data" / "chunks.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(asdict(c), ensure_ascii=False) + "\n")
    print(f"Wrote {out.relative_to(BACKEND_DIR)}")
    if args.dry_run:
        return

    from app.rag import RAGPipeline  # needs the API key; imported late so --dry-run works without one

    rag = RAGPipeline(s)
    vectors = rag.embedder.embed_documents([c.text for c in chunks])
    rag.store.rebuild(chunks, vectors)
    print(f"Indexed {rag.store.count()} chunks into '{s.collection_name}' in {time.perf_counter() - t0:.1f}s")


if __name__ == "__main__":
    main()
