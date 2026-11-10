---
name: wiki_summary
track: bonus
kind: live_api
provider: Wikipedia REST API
requires_env: []
inputs: [title, lang]
outputs: [items, extract]
side_effect: false
---
# wiki_summary

Fetches a concise encyclopedic summary for a topic/entity from the Wikipedia REST API (`https://{lang}.wikipedia.org/api/rest_v1/page/summary/{title}`).
