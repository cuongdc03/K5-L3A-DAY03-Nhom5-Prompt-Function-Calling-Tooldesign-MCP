from __future__ import annotations

import re
from typing import Any

from tools._shared import err, fold_text

VALID_STYLES = {"bibtex", "apa", "ieee", "mla"}


def format_citation(
    title: str = "",
    authors: list[str] | str | None = None,
    year: int | str = 2026,
    url: str = "",
    arxiv_id: str = "",
    style: str = "bibtex",
) -> dict[str, Any]:
    try:
        cleaned_title = " ".join((title or "").split())
        if not cleaned_title:
            raise ValueError("title must not be empty")

        if isinstance(authors, str):
            author_list = [a.strip() for a in re.split(r"[,;]| and ", authors) if a.strip()]
        elif isinstance(authors, list):
            author_list = [str(a).strip() for a in authors if str(a).strip()]
        else:
            author_list = []
        if not author_list:
            author_list = ["Unknown Author"]

        try:
            year_int = int(year or 2026)
            if year_int < 1000 or year_int > 2100:
                raise ValueError("year out of range")
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid year: {year!r}") from exc

        normalized_style = (style or "bibtex").strip().lower()
        if normalized_style not in VALID_STYLES:
            raise ValueError(f"Unsupported citation style: {style!r}. Must be one of {sorted(VALID_STYLES)}")

        first_author_last = re.findall(r"[a-z0-9]+", fold_text(author_list[0]))[-1] if re.findall(r"[a-z0-9]+", fold_text(author_list[0])) else "author"
        first_title_word = next((w for w in re.findall(r"[a-z0-9]+", fold_text(cleaned_title)) if len(w) > 2), "paper")
        cite_key = f"{first_author_last}{year_int}{first_title_word}"

        cleaned_arxiv = (arxiv_id or "").strip()
        cleaned_url = (url or "").strip() or (f"https://arxiv.org/abs/{cleaned_arxiv}" if cleaned_arxiv else "")

        if normalized_style == "bibtex":
            bibtex_authors = " and ".join(author_list)
            lines = [
                f"@article{{{cite_key},",
                f"  title = {{{cleaned_title}}},",
                f"  author = {{{bibtex_authors}}},",
                f"  year = {{{year_int}}},",
            ]
            if cleaned_arxiv:
                lines.append(f"  eprint = {{{cleaned_arxiv}}},")
                lines.append("  archivePrefix = {arXiv},")
            if cleaned_url:
                lines.append(f"  url = {{{cleaned_url}}},")
            lines.append("}")
            citation = "\n".join(lines)
        elif normalized_style == "ieee":
            authors_str = ", ".join(author_list)
            ref_tail = f" arXiv:{cleaned_arxiv}." if cleaned_arxiv else ""
            url_tail = f" [Online]. Available: {cleaned_url}" if cleaned_url else ""
            citation = f'{authors_str}, "{cleaned_title},"{ref_tail} {year_int}.{url_tail}'
        elif normalized_style == "mla":
            authors_str = ", ".join(author_list)
            url_tail = f" {cleaned_url}." if cleaned_url else ""
            citation = f'{authors_str}. "{cleaned_title}." {year_int}.{url_tail}'
        else:  # apa
            authors_str = ", ".join(author_list)
            source_part = f" arXiv preprint arXiv:{cleaned_arxiv}." if cleaned_arxiv else ""
            url_part = f" {cleaned_url}" if cleaned_url else ""
            citation = f"{authors_str} ({year_int}). {cleaned_title}.{source_part}{url_part}"

        return {
            "tool": "cite_export",
            "style": normalized_style,
            "cite_key": cite_key,
            "citation": citation,
            "title": cleaned_title,
            "authors": author_list,
            "year": year_int,
        }
    except Exception as exc:
        return err("cite_export", exc)
