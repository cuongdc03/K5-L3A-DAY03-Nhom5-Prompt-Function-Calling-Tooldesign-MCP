---
name: cite_export
track: bonus
kind: local_formatter
requires_env: []
inputs: [title, authors, year, url, arxiv_id, style]
outputs: [citation, cite_key, style]
side_effect: false
---
# cite_export

Formats academic or web source metadata into a standardized citation string (`bibtex`, `apa`, `ieee`, or `mla`) locally without calling external APIs.
