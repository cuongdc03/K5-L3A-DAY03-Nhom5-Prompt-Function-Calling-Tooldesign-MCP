---
name: github_search
track: bonus
kind: live_api
provider: GitHub REST API (optional GITHUB_TOKEN)
requires_env: []
inputs: [query, sort, language, limit]
outputs: [items]
side_effect: false
---
# github_search

Searches public GitHub repositories. `sort` is `stars` (default, most popular),
`updated` (recently pushed) or `best_match`. Optional `language` filter adds a
`language:<x>` qualifier. Each item has title (owner/repo), url, summary
(description), stars, language, updated_at.

Use when the user wants code, libraries, open-source repos or projects on
GitHub. Not for papers (`papers`) or news (`lookup`). Works without a key; set
`GITHUB_TOKEN` in `.env` for a higher rate limit.

Guardrails: empty query or unknown `sort` returns an error dict; `limit` is
clamped to 1..20.
