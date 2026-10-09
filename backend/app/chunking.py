"""Structure-aware chunking.

The loader gives us page text where headings are marked with "## " and table
rows keep their cells separated by 3+ spaces. We turn that into a stream of
units, then pack units greedily into chunks:

- heading  -> updates the current section; consecutive headings merge into one
              title ("Consolidated Balance Sheets > As of September 30, ...").
              A new section starts a new chunk once the current one has real content.
- sentence -> prose is split into sentences so chunks never end mid-sentence.
- table    -> consecutive table rows stay together; a table is only split if it
              alone exceeds the chunk budget, and then on row boundaries.

Each chunk's text starts with the document title and section, so the embedding
carries context that would otherwise be lost (e.g. "Cash ... increased $58.9M"
means nothing without knowing it's GPO FY2018).

Overlap: when a chunk is cut in the middle of a section, the last few sentences
are repeated at the start of the next chunk. Chunks cut at a section boundary
don't need overlap.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

from app.ingestion.loader import Page

_TABLE_ROW = re.compile(r"\S {3,}\S")
# Protect single-letter initials/abbreviations ("U.S.", "Robert J. Dole") from sentence splits.
_SENT_SPLIT = re.compile(r"(?<![A-Z]\.)(?<!\b[A-Z][a-z]\.)(?<=[.!?”\"])\s+(?=[A-Z0-9“\"(])")


def approx_tokens(text: str) -> int:
    """~1.3 tokens per word is a good approximation for English prose and numbers."""
    return int(len(text.split()) * 1.3) + 1


@dataclass
class Unit:
    kind: str  # "heading" | "sentence" | "table"
    text: str
    page: int

    @property
    def tokens(self) -> int:
        return approx_tokens(self.text)


@dataclass
class Chunk:
    id: str
    text: str  # what gets embedded (with context header)
    body: str  # chunk content without header, for display
    section: str
    page_start: int
    page_end: int
    tokens: int
    has_table: bool
    metadata: dict = field(default_factory=dict)


def _units(pages: list[Page]) -> list[Unit]:
    units: list[Unit] = []
    for page in pages:
        prose: list[str] = []
        table: list[str] = []

        def flush_prose() -> None:
            if prose:
                for s in _SENT_SPLIT.split(" ".join(prose)):
                    if s.strip():
                        units.append(Unit("sentence", s.strip(), page.number))
                prose.clear()

        def flush_table() -> None:
            if table:
                units.append(Unit("table", "\n".join(table), page.number))
                table.clear()

        for line in page.text.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("## "):
                flush_prose(); flush_table()
                units.append(Unit("heading", line[3:].strip(), page.number))
            elif _TABLE_ROW.search(line):
                flush_prose()
                table.append(line)
            else:
                # A short label line directly above table rows is part of the table
                # (e.g. "Current assets", "Restricted:").
                if table and len(line) < 60:
                    table.append(line)
                    continue
                flush_table()
                prose.append(line)
        flush_prose(); flush_table()
    return units


def _split_table(unit: Unit, budget: int) -> list[Unit]:
    rows, parts, cur = unit.text.splitlines(), [], []
    for row in rows:
        if cur and approx_tokens("\n".join(cur + [row])) > budget:
            parts.append(Unit("table", "\n".join(cur), unit.page))
            cur = []
        cur.append(row)
    if cur:
        parts.append(Unit("table", "\n".join(cur), unit.page))
    return parts


def chunk_pages(
    pages: list[Page],
    doc_title: str,
    max_tokens: int = 500,
    overlap_tokens: int = 75,
    min_tokens: int = 120,
) -> list[Chunk]:
    chunks: list[Chunk] = []
    section = ""
    heading_run: list[Unit] = []  # consecutive headings, merged into one section title
    current: list[Unit] = []
    current_section = ""

    def size(units: list[Unit]) -> int:
        return sum(u.tokens for u in units)

    def emit(carry_overlap: bool) -> None:
        nonlocal current
        if not current:
            return
        body = "\n".join(u.text for u in current)
        header = f"{doc_title}" + (f" | Section: {current_section}" if current_section else "")
        pages_ = [u.page for u in current]
        cid = hashlib.sha1(f"{min(pages_)}:{body}".encode()).hexdigest()[:12]
        chunks.append(Chunk(
            id=cid,
            text=f"{header}\n\n{body}",
            body=body,
            section=current_section,
            page_start=min(pages_),
            page_end=max(pages_),
            tokens=approx_tokens(body),
            has_table=any(u.kind == "table" for u in current),
        ))
        tail: list[Unit] = []
        if carry_overlap:
            for u in reversed(current):
                if u.kind != "sentence" or size(tail) + u.tokens > overlap_tokens:
                    break
                tail.insert(0, u)
        current = tail

    for unit in _units(pages):
        if unit.kind == "heading":
            heading_run.append(unit)
            continue

        if heading_run:
            section = " > ".join(h.text for h in heading_run)
            headings, heading_run = heading_run, []
            # New section: close the current chunk if it already has enough content.
            if size(current) >= min_tokens:
                emit(carry_overlap=False)
                current = []
            elif current:
                # Tiny previous section gets merged forward; label with both titles.
                parts = [p for p in current_section.split(" / ") if p] + [section]
                section = " / ".join(parts[-3:])  # keep labels readable
            current_section = section
            # Keep headings in the body too: inside tables they carry meaning ("ASSETS").
            current.extend(headings)
        elif not current:
            current_section = section

        pieces = _split_table(unit, max_tokens) if unit.kind == "table" and unit.tokens > max_tokens else [unit]
        for piece in pieces:
            if current and size(current) + piece.tokens > max_tokens:
                emit(carry_overlap=True)
                current_section = section
            current.append(piece)

    emit(carry_overlap=False)
    return chunks
