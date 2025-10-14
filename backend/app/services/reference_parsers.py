"""Parsing helpers for reference documents."""

from __future__ import annotations

import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from html.parser import HTMLParser

if sys.version_info >= (3, 10):

    @dataclass(slots=True)
    class ParsedClause:
        """Structured clause extracted from a reference document."""

        clause_ref: str
        heading: str
        text: str
        page_from: int
        page_to: int
        quality: str = "high"

else:

    @dataclass
    class ParsedClause:
        """Structured clause extracted from a reference document."""

        clause_ref: str
        heading: str
        text: str
        page_from: int
        page_to: int
        quality: str = "high"


class ClauseParser:
    """Extract clauses from PDF or HTML payloads."""

    def parse(self, kind: str, payload: bytes) -> list[ParsedClause]:
        kind_lower = (kind or "").lower()
        if kind_lower == "pdf":
            text = self._decode(payload)
            return self._parse_text_clauses(text)
        if kind_lower in {"html", "sitemap"}:
            sections = self._parse_html_sections(payload)
            return self._build_clauses_from_sections(sections)
        text = self._decode(payload)
        return self._parse_text_clauses(text)

    def _decode(self, payload: bytes) -> str:
        return payload.decode("utf-8", errors="ignore")

    def _parse_text_clauses(self, text: str) -> list[ParsedClause]:
        pattern = re.compile(
            r"^(?:Section\s+)?(?P<ref>\d+(?:\.\d+)*(?:[A-Za-z])?)"
            r"(?:\s*[:\-.]\s+|\s+)(?P<title>.*)$",
            re.IGNORECASE,
        )
        clauses: list[ParsedClause] = []
        current_ref: str | None = None
        current_heading: str = ""
        buffer: list[str] = []

        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            match = pattern.match(stripped)
            if match:
                if current_ref is not None:
                    clauses.append(
                        ParsedClause(
                            clause_ref=current_ref,
                            heading=current_heading or current_ref,
                            text=" ".join(buffer).strip(),
                            page_from=len(clauses) + 1,
                            page_to=len(clauses) + 1,
                        )
                    )
                current_ref = match.group("ref")
                heading = match.group("title").strip()
                current_heading = heading or stripped
                buffer = []
            else:
                buffer.append(stripped)

        if current_ref is not None:
            clauses.append(
                ParsedClause(
                    clause_ref=current_ref,
                    heading=current_heading or current_ref,
                    text=" ".join(buffer).strip(),
                    page_from=len(clauses) + 1,
                    page_to=len(clauses) + 1,
                )
            )

        return [clause for clause in clauses if clause.text or clause.heading]

    def _parse_html_sections(self, payload: bytes) -> list[tuple[str, str]]:
        parser = _HTMLSectionParser()
        parser.feed(self._decode(payload))
        parser.close()
        return parser.sections

    def _build_clauses_from_sections(
        self,
        sections: Iterable[tuple[str, str]],
    ) -> list[ParsedClause]:
        clauses: list[ParsedClause] = []
        seen_refs: set[str] = set()
        for index, (heading, body) in enumerate(sections, start=1):
            clause_ref = self._extract_clause_ref(heading) or self._extract_clause_ref(
                body
            )
            if not clause_ref or clause_ref in seen_refs:
                continue
            seen_refs.add(clause_ref)
            clauses.append(
                ParsedClause(
                    clause_ref=clause_ref,
                    heading=heading.strip() or clause_ref,
                    text=" ".join(body.split()),
                    page_from=index,
                    page_to=index,
                )
            )
        return clauses

    def _extract_clause_ref(self, text: str) -> str | None:
        match = re.search(r"(\d+(?:\.\d+)*(?:[A-Za-z])?)", text or "")
        return match.group(1) if match else None


class _HTMLSectionParser(HTMLParser):
    """Collect heading/text pairs from HTML documents."""

    HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
    TEXT_TAGS = {"p", "div", "li", "span"}

    def __init__(self) -> None:
        super().__init__()
        self.sections: list[tuple[str, str]] = []
        self._heading_parts: list[str] = []
        self._text_parts: list[str] = []
        self._in_heading = False
        self._in_text = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_lower = tag.lower()
        if tag_lower in self.HEADING_TAGS:
            self._flush_section()
            self._in_heading = True
            self._in_text = False
        elif tag_lower in self.TEXT_TAGS:
            self._in_text = True
        elif tag_lower == "br":
            self._text_parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag_lower = tag.lower()
        if tag_lower in self.HEADING_TAGS:
            self._in_heading = False
        elif tag_lower in self.TEXT_TAGS:
            self._in_text = False

    def handle_data(self, data: str) -> None:
        stripped = data.strip()
        if not stripped:
            return
        if self._in_heading:
            self._heading_parts.append(stripped)
        elif self._in_text:
            self._text_parts.append(stripped)

    def close(self) -> None:
        self._flush_section()
        super().close()

    def _flush_section(self) -> None:
        heading = " ".join(self._heading_parts).strip()
        body = " ".join(part for part in self._text_parts if part.strip()).strip()
        if heading or body:
            self.sections.append((heading, body))
        self._heading_parts = []
        self._text_parts = []
        self._in_heading = False
        self._in_text = False


__all__ = ["ClauseParser", "ParsedClause"]
