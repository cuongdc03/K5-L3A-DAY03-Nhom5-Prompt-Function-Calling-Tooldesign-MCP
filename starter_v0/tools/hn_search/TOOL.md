---
name: hn_search
track: bonus
kind: live_api
provider: Hacker News Algolia API
requires_env: []
inputs: [query, tags, max_results]
outputs: [items, total_hits]
side_effect: false
---
# hn_search

Searches tech discussions and stories on Hacker News via the public Algolia API (`https://hn.algolia.com/api/v1/search`).
