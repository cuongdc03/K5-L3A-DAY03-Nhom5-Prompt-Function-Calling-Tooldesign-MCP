---
name: hackernews
track: bonus
kind: live_api
provider: Hacker News Algolia API
requires_env: []
inputs: [query, sort_by, max_results]
outputs: [items]
side_effect: false
---
# hackernews

Searches tech, startup, and developer stories on Hacker News via the public
Algolia API (`https://hn.algolia.com/api/v1/`). Supports `sort_by` (`relevance`
or `date`) and `max_results`.
