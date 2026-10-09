# GPO Annual Report: Baseline RAG

Question answering over the **U.S. Government Publishing Office FY 2018 Annual Report** (82-page PDF), with page-level citations.

- **Backend:** Python, FastAPI, PyMuPDF, ChromaDB, Gemini (`gemini-embedding-001` + `gemini-3.5-flash`, falling back to `gemini-3.5-flash-lite`)
- **Frontend:** React 19, Vite, TypeScript

```
React UI ──/api──▶ FastAPI ──▶ retrieve (Chroma, cosine top-k) ──▶ Gemini (grounded prompt) ──▶ answer + [S#] citations
                                  ▲
       scripts/ingest.py: PDF ──▶ layout-aware text ──▶ structure-aware chunks ──▶ embeddings ──▶ Chroma
```

## Quick start

```bash
# Backend (from backend/)
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env            # then put your key in GEMINI_API_KEY (https://aistudio.google.com/apikey)
python -m scripts.ingest          # build the index (about 1 minute)
uvicorn app.main:app --reload --port 8000

# Frontend (from frontend/, second terminal)
npm install
npm run dev                       # http://localhost:5173 (proxies /api to :8000)

# Evaluation (from backend/)
python -m eval.run_eval           # writes eval/results/<timestamp>.md and .json
```

## Pipeline

### 1. Ingestion (`app/ingestion/loader.py`)
The report has two-column prose, side-by-side tables and full-width financial statements. Default PDF text extraction splits table labels from their numbers, so a chunk might contain "Total assets" with no value next to it. The loader rebuilds the reading order from span coordinates:
- groups spans that share a baseline into rows, so table rows stay intact: `Total assets   $ 1,018,063   $ 945,623`
- detects a column gutter (weighted by characters; a gap before a numeric column doesn't count as a gutter) and reads the left column before the right
- detects headings by font: a bolder or larger font than the page's body font, including run-in heads like "**Strategic Plan** Our strategic plan…"
- strips the running headers and footers and the letter-spaced banner

### 2. Chunking (`app/chunking.py`)
- Units: headings, sentences and tables. Chunks never end mid-sentence or mid-table row.
- Packed up to **500 tokens** (approximate), with **75 tokens of sentence overlap** when a section has to be split. A new section starts a new chunk once the current chunk has at least 120 tokens.
- Every chunk starts with `GPO 2018 Annual Report | Section: …`, so the embedding keeps the document and section context.
- Result: **106 chunks**, median about 265 tokens, 38 containing tables.

**Why 500 tokens and not something larger:** the financial section is many short, fact-dense subsections (Cash, Inventory, Deferred Revenues…). Larger chunks would blend several of them into one vector and make retrieval less precise.

### 3. Embeddings (`app/embeddings.py`)
`gemini-embedding-001` at 768 dimensions, re-normalized after truncation. It uses the asymmetric `RETRIEVAL_DOCUMENT` and `RETRIEVAL_QUERY` task types. Batched, retried on HTTP 429, and cached on disk, so re-ingesting only embeds chunks that changed.

### 4. Vector store (`app/vectorstore.py`)
ChromaDB (persistent, cosine). Ingestion drops and rebuilds the collection, so it is idempotent: no stale or duplicate chunks.

### 5. Retrieval and generation (`app/rag.py`, `app/generator.py`)
- Top-k = 5. Chunks below a similarity threshold are dropped, and if none are left the system answers "not found" without calling the LLM.
- The prompt tells the model to use only the numbered sources, cite each sentence with `[S#]`, copy numbers exactly, handle "in thousands" units, and refuse when the sources don't contain the answer.
- The backend maps `[S#]` to page ranges, and the UI shows them as clickable citation chips.

## API

| Endpoint | Description |
|---|---|
| `POST /api/query` `{question, top_k?}` | answer, `found`, sources (pages, section, similarity, text, cited), latencies |
| `POST /api/ingest` | rebuild the index |
| `GET /api/health` | chunk count and models in use |

## Evaluation (`backend/eval/`)
`sample_questions.json` holds 15 questions with reference answers and pages: narrative facts, financial tables, comparisons, and 2 out-of-scope questions. `run_eval.py` reports **hit@k, MRR, citation accuracy, refusal accuracy**, and LLM-judged **correctness and faithfulness**.

### Baseline results (run `20261006-183412`, top-k 5, 500-token chunks)

| Metric | Value |
|---|---|
| Hit@5 (13 in-scope questions) | **100%** |
| MRR | **0.962** (12 of 13 at rank 1; q07 at rank 2) |
| Citation accuracy | **100%** |
| Refusal accuracy (2 out-of-scope questions) | **100%** |
| Correct / correct-or-partial (LLM judge) | **93% / 100%** |
| Faithful (no unsupported claims) | **100%** |
| Avg latency | retrieval ~0.6 s, generation ~3.4 s |

I spot-checked the judge's verdicts against the PDF. For example, q02 answered "15,901,600 passports", which is the exact figure from the *By the Numbers* page (p. 14), and q07's "41.4% of total expenses" is stated on p. 25.

**Failure analysis**
- **q03 (partial): a generation gap, not a retrieval gap.** The model gave net income correctly ($52.6M vs. $58.9M) but left out the adjusted figure ($20.4M vs. $38.3M), even though that figure is in the same retrieved chunk. A prompt that asks for "material qualifications or adjusted figures stated in the sources" would probably fix this. I left it unchanged so this stays a true baseline.
- **Similarity threshold (0.60).** Calibrated on this set: the lowest in-scope top-1 score was 0.658 and the off-topic question scored 0.512. The threshold only catches *off-topic* questions. An on-topic question about the wrong year ("revenue in FY 2022") scores 0.756, and the grounded prompt makes the model refuse it.
- **Free tier.** 5 of the 14 LLM answers were served by the fallback model `gemini-3.5-flash-lite` after the primary model returned 429/503. Results should be compared knowing that. `gemini-3.8-flash` returned 503 "high demand" consistently during development.

**Caveat:** I wrote these 15 questions while building the pipeline, so they are not a held-out test set. Score the official sample questions the same way by adding them to `sample_questions.json`.

## Known limitations (next steps)
- **Charts aren't read.** Values that appear only in bar charts (e.g. passports and smartcards produced, pp. 47–48) aren't extractable as text. A vision model or OCR of the chart images would fix this.
- **Pure vector search.** Exact-term queries ("Note 9", specific dollar amounts) could improve with hybrid BM25 + vector search and a re-ranker.
- **Token counts are approximate.** They use a word-based estimate rather than the model's tokenizer.
- **One document.** The metadata already supports several reports (e.g. year filters), but only one has been ingested.

## Layout

```
backend/
  app/            config, ingestion/loader, chunking, embeddings, vectorstore, generator, rag, schemas, main (FastAPI)
  scripts/        ingest.py
  eval/           sample_questions.json, run_eval.py, results/
  data/raw/       gpo_annual_report.pdf
frontend/
  src/            App.tsx, api.ts, components/AnswerCard.tsx, sampleQuestions.ts
```
