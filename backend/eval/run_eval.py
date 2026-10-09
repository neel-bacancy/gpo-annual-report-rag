"""Run the sample questions through the pipeline and score them.

Usage (from backend/):
    python -m eval.run_eval                 # all questions
    python -m eval.run_eval --ids q01 q07   # a subset
    python -m eval.run_eval --no-judge      # retrieval metrics only (fewer API calls)

Metrics
- hit@k        an expected page falls inside one of the raw top-k chunks
- MRR          1 / rank of the first chunk covering an expected page
- citation ok  at least one cited source covers an expected page
- correctness  LLM judge vs. the expected answer: correct / partial / incorrect
- faithful     LLM judge: every claim in the answer is supported by the sources
- refusal ok   out-of-scope questions get the "not found" answer
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

from google.genai import types
from pydantic import BaseModel

from app.config import get_settings
from app.generator import build_context
from app.rag import Answer, RAGPipeline
from app.vectorstore import Hit

EVAL_DIR = Path(__file__).resolve().parent

JUDGE_PROMPT = """You are grading a question-answering system over the GPO 2018 Annual Report.

Question: {question}

Reference answer (ground truth): {expected}

System answer: {answer}

Sources the system was given:
{context}

Grade two things:
1. correctness - compare the system answer to the reference answer.
   "correct": all key facts/numbers match (unit conversions like 874,466 thousand = $874.5 million are fine;
   extra correct detail is fine). "partial": some key facts right, some missing or wrong.
   "incorrect": wrong, or a refusal when the reference has an answer.
   If the reference starts with NOT_FOUND, "correct" means the system declined to answer.
2. faithful - true if every factual claim in the system answer is supported by the sources above
   (a refusal is faithful). false if it states anything not in the sources.
"""


class Judgement(BaseModel):
    correctness: str  # correct | partial | incorrect
    faithful: bool
    reason: str


def covers(hit: Hit, pages: list[int]) -> bool:
    return any(hit.page_start <= p <= hit.page_end for p in pages)


def judge(rag: RAGPipeline, item: dict, ans: Answer) -> Judgement:
    prompt = JUDGE_PROMPT.format(
        question=item["question"],
        expected=item["expected_answer"],
        answer=ans.answer,
        context=build_context(ans.hits) if ans.hits else "(none)",
    )
    text, _ = rag.generator.complete(
        prompt,
        types.GenerateContentConfig(
            temperature=0,
            response_mime_type="application/json",
            response_schema=Judgement,
            thinking_config=rag.generator.thinking,
        ),
    )
    return Judgement.model_validate_json(text)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ids", nargs="*", help="only run these question ids")
    parser.add_argument("--no-judge", action="store_true")
    parser.add_argument("--delay", type=float, default=8.0, help="seconds between questions (free-tier RPM)")
    args = parser.parse_args()

    settings = get_settings()
    rag = RAGPipeline(settings)
    items = json.loads((EVAL_DIR / "sample_questions.json").read_text(encoding="utf-8"))
    if args.ids:
        items = [i for i in items if i["id"] in args.ids]

    rows = []
    for n, item in enumerate(items):
        if n:
            time.sleep(args.delay)
        ans = rag.answer(item["question"])
        expected = item["expected_pages"]
        in_scope = bool(expected)

        rank = next((r for r, h in enumerate(ans.retrieved, 1) if covers(h, expected)), None)
        cited_hits = [ans.hits[i - 1] for i in ans.cited]
        row = {
            "id": item["id"],
            "category": item["category"],
            "question": item["question"],
            "expected_answer": item["expected_answer"],
            "expected_pages": expected,
            "answer": ans.answer,
            "found": ans.found,
            "retrieved": [
                {"pages": [h.page_start, h.page_end], "section": h.section, "similarity": round(h.similarity, 4)}
                for h in ans.retrieved
            ],
            "cited_pages": [[h.page_start, h.page_end] for h in cited_hits],
            "hit_at_k": rank is not None if in_scope else None,
            "rank": rank,
            "citation_ok": any(covers(h, expected) for h in cited_hits) if in_scope else None,
            "refusal_ok": (not ans.found) if not in_scope else None,
            "retrieval_ms": ans.retrieval_ms,
            "generation_ms": ans.generation_ms,
            "model": ans.model,
        }
        if not args.no_judge:
            time.sleep(args.delay / 2)
            j = judge(rag, item, ans)
            row.update(correctness=j.correctness, faithful=j.faithful, judge_reason=j.reason)

        rows.append(row)
        status = row.get("correctness", "-")
        print(f"{item['id']}  hit={row['hit_at_k']}  rank={rank}  {status:<9}  {item['question'][:60]}")

    write_reports(rows, settings, judged=not args.no_judge)


def write_reports(rows: list[dict], settings, judged: bool) -> None:
    in_scope = [r for r in rows if r["expected_pages"]]
    oos = [r for r in rows if not r["expected_pages"]]

    def pct(xs: list) -> str:
        return f"{100 * sum(xs) / len(xs):.0f}%" if xs else "n/a"

    summary = {
        "questions": len(rows),
        "hit_at_k": pct([r["hit_at_k"] for r in in_scope]),
        "mrr": round(sum(1 / r["rank"] for r in in_scope if r["rank"]) / len(in_scope), 3) if in_scope else None,
        "citation_accuracy": pct([r["citation_ok"] for r in in_scope]),
        "refusal_accuracy": pct([r["refusal_ok"] for r in oos]),
        "avg_retrieval_ms": int(sum(r["retrieval_ms"] for r in rows) / len(rows)),
        "avg_generation_ms": int(sum(r["generation_ms"] for r in rows) / len(rows)),
    }
    if judged:
        summary["correct"] = pct([r["correctness"] == "correct" for r in rows])
        summary["correct_or_partial"] = pct([r["correctness"] in ("correct", "partial") for r in rows])
        summary["faithful"] = pct([r["faithful"] for r in rows])

    config = {
        k: getattr(settings, k)
        for k in ("llm_model", "embedding_model", "embedding_dim", "chunk_max_tokens",
                  "chunk_overlap_tokens", "top_k", "min_similarity", "llm_temperature")
    }
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = EVAL_DIR / "results"
    out.mkdir(exist_ok=True)
    (out / f"{stamp}.json").write_text(
        json.dumps({"summary": summary, "config": config, "results": rows}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    md = [f"# Eval run {stamp}", "", "## Summary", "", "| Metric | Value |", "|---|---|"]
    md += [f"| {k} | {v} |" for k, v in summary.items()]
    md += ["", "## Config", "", "| Setting | Value |", "|---|---|"]
    md += [f"| {k} | {v} |" for k, v in config.items()]
    md += ["", "## Results", "", "| id | category | hit@k | rank | cited ok | correctness | faithful |",
           "|---|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['id']} | {r['category']} | {r['hit_at_k']} | {r['rank']} | "
                  f"{r['citation_ok'] if r['expected_pages'] else r['refusal_ok']} | "
                  f"{r.get('correctness', '-')} | {r.get('faithful', '-')} |")
    md += ["", "## Answers", ""]
    for r in rows:
        md += [f"### {r['id']}: {r['question']}", "",
               f"**Expected:** {r['expected_answer']}  ", f"**Expected pages:** {r['expected_pages']}", "",
               f"**Answer:**", "", r["answer"], "",
               f"**Retrieved pages:** {[x['pages'] for x in r['retrieved']]}  ",
               f"**Similarities:** {[x['similarity'] for x in r['retrieved']]}"]
        if r.get("judge_reason"):
            md.append(f"**Judge:** {r['correctness']} / faithful={r['faithful']}: {r['judge_reason']}")
        md.append("")
    (out / f"{stamp}.md").write_text("\n".join(md), encoding="utf-8")

    print("\n" + json.dumps(summary, indent=2))
    print(f"Reports: eval/results/{stamp}.md and .json")


if __name__ == "__main__":
    main()
