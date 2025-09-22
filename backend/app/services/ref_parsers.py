"""Parsers for transforming reference documents into clause segments."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List


@dataclass(slots=True)
class ClauseSegment:
    """Representation of a clause extracted from a reference document."""

    clause_ref: str
    heading: str | None
    text_span: str
    page_from: int | None
    page_to: int | None


_PAGE_PATTERN = re.compile(r"page(?:s)?\s*(\d+)(?:\s*[-–]\s*(\d+))?", re.IGNORECASE)
_CLAUSE_HEADER_PATTERN = re.compile(
    r"^(?:Clause|Section)?\s*([A-Za-z0-9.\-]+)\s*(?::|-)?\s*(.*)$",
    re.IGNORECASE,
)
_HTML_SECTION_PATTERN = re.compile(
    r"<(?:section|article)([^>]*)>(.*?)</(?:section|article)>",
    re.IGNORECASE | re.DOTALL,
)
_HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
_WHITESPACE_PATTERN = re.compile(r"\s+")


def _clean_text_lines(block: str) -> list[str]:
    lines = [line.strip() for line in block.splitlines()]
    return [line for line in lines if line]


def _extract_pages(text: Iterable[str]) -> tuple[list[str], int | None, int | None]:
    remaining: list[str] = []
    page_from: int | None = None
    page_to: int | None = None
    for line in text:
        match = _PAGE_PATTERN.search(line)
        if match:
            page_from = int(match.group(1))
            page_to = int(match.group(2) or match.group(1))
            continue
        remaining.append(line)
    return remaining, page_from, page_to


def _parse_text_blocks(blocks: Iterable[str]) -> List[ClauseSegment]:
    segments: List[ClauseSegment] = []
    for raw_block in blocks:
        lines = _clean_text_lines(raw_block)
        if not lines:
            continue
        lines, page_from, page_to = _extract_pages(lines)
        if not lines:
            continue
        first_line = lines[0]
        heading: str | None = None
        clause_ref: str | None = None
        body_start_index = 1

        header_match = _CLAUSE_HEADER_PATTERN.match(first_line)
        if header_match:
            clause_ref = header_match.group(1) or "unlabelled"
            heading_candidate = header_match.group(2).strip()
            if heading_candidate:
                heading = heading_candidate
        else:
            parts = first_line.split(None, 1)
            clause_ref = parts[0]
            if len(parts) > 1:
                heading = parts[1].strip() or None

        if heading is None and len(lines) > 1:
            heading = lines[1]
            body_start_index = 2
        else:
            body_start_index = 1

        text_span = " ".join(lines[body_start_index:]).strip()
        segments.append(
            ClauseSegment(
                clause_ref=clause_ref or "unlabelled",
                heading=heading,
                text_span=text_span,
                page_from=page_from,
                page_to=page_to,
            )
        )
    return segments


def parse_pdf_clauses(payload: bytes) -> List[ClauseSegment]:
    """Parse a PDF-derived text payload into clause segments."""

    text = payload.decode("utf-8", errors="ignore")
    blocks = re.split(r"\n\s*\n", text)
    return _parse_text_blocks(blocks)


def _strip_html(fragment: str) -> str:
    text = _HTML_TAG_PATTERN.sub(" ", fragment)
    return _WHITESPACE_PATTERN.sub(" ", text).strip()


def parse_html_clauses(payload: bytes) -> List[ClauseSegment]:
    """Parse an HTML payload into clause segments."""

    html = payload.decode("utf-8", errors="ignore")
    segments: List[ClauseSegment] = []
    for match in _HTML_SECTION_PATTERN.finditer(html):
        attributes = match.group(1) or ""
        body = match.group(2) or ""

        clause_ref_match = re.search(r'data-clause="([^"]+)"', attributes)
        clause_ref = clause_ref_match.group(1) if clause_ref_match else None

        pages_match = re.search(r'data-pages="([^"]+)"', attributes)
        if pages_match:
            numbers = re.findall(r"\d+", pages_match.group(1))
            page_from = int(numbers[0]) if numbers else None
            page_to = int(numbers[1]) if len(numbers) > 1 else page_from
        else:
            body_lines, page_from, page_to = _extract_pages(_clean_text_lines(body))
            body = "\n".join(body_lines)

        heading_match = re.search(r"<h[1-6][^>]*>(.*?)</h[1-6]>", body, re.IGNORECASE | re.DOTALL)
        heading = _strip_html(heading_match.group(1)) if heading_match else None
        paragraphs = [
            _strip_html(fragment)
            for fragment in re.findall(r"<p[^>]*>(.*?)</p>", body, re.IGNORECASE | re.DOTALL)
        ]
        text_span = " ".join(p for p in paragraphs if p).strip()
        if not text_span:
            text_span = _strip_html(body)

        if clause_ref is None:
            clause_ref = heading.split()[0] if heading else "unlabelled"

        segments.append(
            ClauseSegment(
                clause_ref=clause_ref,
                heading=heading,
                text_span=text_span,
                page_from=page_from,
                page_to=page_to,
            )
        )

    if not segments:
        text = _strip_html(html)
        blocks = re.split(r"\n\s*\n", text)
        return _parse_text_blocks(blocks)

    return segments


def parse_document_clauses(payload: bytes, kind: str) -> List[ClauseSegment]:
    """Parse *payload* according to *kind* and return clause segments."""

    normalized_kind = (kind or "pdf").lower()
    if normalized_kind in {"html", "sitemap"}:
        return parse_html_clauses(payload)
    return parse_pdf_clauses(payload)


__all__ = [
    "ClauseSegment",
    "parse_document_clauses",
    "parse_html_clauses",
    "parse_pdf_clauses",
]
