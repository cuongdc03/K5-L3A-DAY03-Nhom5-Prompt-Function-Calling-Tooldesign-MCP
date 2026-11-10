---
name: github_search
track: bonus
kind: live_api
provider: GitHub REST API
requires_env: []
inputs: [query, language, sort, max_results]
outputs: [items, total_count]
side_effect: false
---
# github_search

Searches public GitHub repositories via the GitHub REST API (`https://api.github.com/search/repositories`).
Supports optional filtering by programming `language`, sorting by `stars` / `forks` / `updated`, and `max_results`.
