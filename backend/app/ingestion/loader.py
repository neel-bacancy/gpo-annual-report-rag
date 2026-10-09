"""PDF -> clean, layout-aware page text.

The GPO report mixes two-column prose, side-by-side tables and full-width
financial statements. Plain text extraction separates table labels from
their numbers, so we rebuild reading order ourselves:

1. Collect spans (text + bbox + font size) from PyMuPDF.
2. Group spans that share a baseline into visual rows.
3. If the page has a vertical gutter, emit left-column rows before
   right-column rows; rows that cross the gutter stay full width.
4. Within a row, wide horizontal gaps become "   " so table cells
   ("Total assets   $ 1,018,063   $ 945,623") stay on one line.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf


@dataclass
class Span:
    x0: float
    y0: float
    x1: float
    y1: float
    text: str
    size: float
    font: str = ""

    @property
    def bold(self) -> bool:
        return any(k in self.font for k in ("Bold", "Md", "Black", "Heavy", "Semibold"))


@dataclass
class Line:
    spans: list[Span]

    @property
    def x0(self) -> float:
        return min(s.x0 for s in self.spans)

    @property
    def x1(self) -> float:
        return max(s.x1 for s in self.spans)

    @property
    def y(self) -> float:
        return max(s.y1 for s in self.spans)

    @property
    def size(self) -> float:
        return max(s.size for s in self.spans)

    def text(self, gap: float = 12.0) -> str:
        out, prev = "", None
        for s in sorted(self.spans, key=lambda s: s.x0):
            if prev is not None:
                out += "   " if s.x0 - prev > gap else " "
            out += s.text.strip()
            prev = s.x1
        return re.sub(r"[ \t]{4,}", "   ", out).strip()


@dataclass
class Page:
    number: int  # 1-based PDF page
    text: str
    headings: list[str] = field(default_factory=list)


# Running headers/footers repeated on every page; they add noise to embeddings.
_BOILERPLATE = [
    re.compile(r"^U\.\s?S\. Government Publishing Office$"),  # statement title prefix
    re.compile(r"U\.\s?S\. Government Publishing Office\s*\|\s*Financial Year In Review", re.I),
    re.compile(r"^Section [IVX]+:.*(?:\(Unaudited\)|Statements)\s*$"),
    re.compile(r"^\d{1,3}$"),  # bare page number
]


def _is_boilerplate(text: str) -> bool:
    tokens = text.split()
    # Letter-spaced running header: "U . S . G O V E R N M E N T ..."
    if len(tokens) >= 10 and sum(len(t) == 1 for t in tokens) / len(tokens) > 0.7:
        return True
    return any(p.search(text) for p in _BOILERPLATE)


def _spans(page: pymupdf.Page) -> list[Span]:
    spans = []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            if line["dir"][1] != 0:  # skip rotated text
                continue
            for s in line["spans"]:
                if s["text"].strip():
                    spans.append(Span(*s["bbox"], s["text"], round(s["size"], 1), s["font"]))
    return spans


def _dedupe(spans: list[Span]) -> list[Span]:
    """Drop spans drawn twice at the same position (faux-bold rendering)."""
    seen, out = set(), []
    for s in spans:
        key = (round(s.x0), round(s.y0), s.text)
        if key not in seen:
            seen.add(key)
            out.append(s)
    return out


def _group_rows(spans: list[Span], tol: float = 3.0) -> list[Line]:
    rows: list[Line] = []
    for s in sorted(spans, key=lambda s: (s.y1, s.x0)):
        if rows and abs(rows[-1].y - s.y1) <= tol:
            rows[-1].spans.append(s)
        else:
            rows.append(Line([s]))
    return rows


def _find_gutter(spans: list[Span], width: float) -> float | None:
    """Return an x position between two text columns, or None for single-column pages."""
    best_x, best_cross = None, None
    for x in range(int(width * 0.35), int(width * 0.65), 2):
        cross = sum(1 for s in spans if s.x0 < x < s.x1)
        if best_cross is None or cross < best_cross:
            best_x, best_cross = x, cross
    if best_x is None:
        return None
    # Weigh by characters, not span count: a column of long lines has few spans.
    total = sum(len(s.text) for s in spans)
    left = sum(len(s.text) for s in spans if s.x1 <= best_x)
    right = sum(len(s.text) for s in spans if s.x0 >= best_x)
    crossing = sum(len(s.text) for s in spans if s.x0 < best_x < s.x1)
    # Both sides need real content and little text may straddle the gutter.
    if min(left, right) < 0.15 * total or crossing > 0.08 * total:
        return None
    # A real gutter separates prose; a gap before a numeric column is a table, not a gutter.
    right_text = "".join(s.text for s in spans if s.x0 >= best_x)
    if sum(c.isalpha() for c in right_text) < 0.5 * len(right_text.replace(" ", "")):
        return None
    return best_x


def _order_lines(spans: list[Span], width: float) -> list[Line]:
    gutter = _find_gutter(spans, width)
    if gutter is None:
        return _group_rows(spans)

    # Split rows into bands: a row with a span crossing the gutter is full width;
    # consecutive non-crossing rows form a two-column band (left then right).
    ordered: list[Line] = []
    band: list[Line] = []

    def flush() -> None:
        left = [Span(**vars(s)) for r in band for s in r.spans if s.x1 <= gutter]
        right = [Span(**vars(s)) for r in band for s in r.spans if s.x0 >= gutter]
        ordered.extend(_group_rows(left))
        ordered.extend(_group_rows(right))
        band.clear()

    for row in _group_rows(spans):
        if any(s.x0 < gutter < s.x1 for s in row.spans):
            flush()
            ordered.append(row)
        else:
            band.append(row)
    flush()
    return ordered


def _body_font(spans: list[Span]) -> tuple[str, float]:
    """Most common (font, size) on the page, weighted by characters."""
    counts: Counter[tuple[str, float]] = Counter()
    for s in spans:
        counts[(s.font, s.size)] += len(s.text)
    return counts.most_common(1)[0][0] if counts else ("", 0.0)


def _is_heading(line: Line, text: str, body_font: str, body_size: float) -> bool:
    if len(text) > 90 or not re.search(r"[A-Za-z]{3}", text) or text.endswith((".", ":")):
        return False
    # Bold table rows ("Total assets   $ 1,018,063") and TOC entries are not headings.
    if "   " in text or "…" in text or ".." in text:
        return False
    if any(s.font == body_font for s in line.spans):
        return False
    bigger = line.size >= body_size * 1.2
    bold = all(s.bold for s in line.spans) and line.size >= body_size * 0.9
    return bigger or bold


def _run_in_heading(line: Line, body_font: str) -> tuple[str, str] | None:
    """Split a run-in head ("Strategic Plan  Our strategic plan, which...") into (heading, rest).

    The narrative section starts some paragraphs with a bold title on the same line.
    It is told apart from inline bold names ("govinfo and enhanced...") by the
    double space and capital letter that follow it.
    """
    spans = sorted(line.spans, key=lambda s: s.x0)
    if len(spans) < 2 or not spans[0].bold or spans[1].font != body_font:
        return None
    head, rest = spans[0].text.strip(), spans[1].text
    if not re.match(r"^\s{2,}[A-Z]", rest) or len(head) > 60 or not head[:1].isupper():
        return None
    return head, Line(spans[1:]).text()


def load_pdf(path: str | Path) -> list[Page]:
    doc = pymupdf.open(path)
    pages: list[Page] = []

    for pdf_page in doc:
        spans = _dedupe(_spans(pdf_page))
        body_font, body_size = _body_font(spans)
        lines, headings = [], []
        for line in _order_lines(spans, pdf_page.rect.width):
            text = line.text()
            if not text or _is_boilerplate(text):
                continue
            run_in = _run_in_heading(line, body_font)
            if run_in:
                headings.append(run_in[0])
                lines.extend([f"## {run_in[0]}", run_in[1]])
                continue
            # Short lines in a bolder/larger font than the body are headings; mark them for the chunker.
            if _is_heading(line, text, body_font, body_size):
                headings.append(text)
                lines.append(f"## {text}")
            else:
                lines.append(text)
        pages.append(Page(pdf_page.number + 1, _clean("\n".join(lines)), headings))
    return pages


def _clean(text: str) -> str:
    text = text.replace(" ", " ").replace("‐", "-").replace("‑", "-")
    # Re-join words broken across lines. Keep the hyphen: in this report most
    # line-end hyphens are real compounds ("Vance-Cooks", "1,242-page").
    text = re.sub(r"(\w)-\n(\w)", r"\1-\2", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
