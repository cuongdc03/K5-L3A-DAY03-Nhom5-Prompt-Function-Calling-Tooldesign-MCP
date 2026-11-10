---
name: wiki
track: bonus
kind: live_api
provider: Wikipedia (MediaWiki API, no key)
requires_env: []
inputs: [query, lang, limit]
outputs: [items]
side_effect: false
---
# wiki

Searches Wikipedia (`en` or `vi`) and returns the intro summary of the best
matching articles (title, url, summary). Use for stable background knowledge:
definitions, people, organizations, concepts. Not for news or anything that
changed recently — use `lookup` with `topic=news` for that.

Guardrails: empty query, unsupported `lang`, and HTTP errors return an error
dict instead of raising; `limit` is clamped to 1..5.
