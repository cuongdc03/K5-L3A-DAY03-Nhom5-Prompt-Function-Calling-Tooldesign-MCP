---
name: deduplicate
track: core
kind: local_formatter
requires_env: []
inputs: [items]
outputs: [items, input_count, item_count, duplicate_count]
side_effect: false
---
# deduplicate

Removes repeated research results while preserving the first occurrence and original order. Use after collecting results when the user asks to remove duplicates or when combining result lists. URL matches ignore URL fragments, letter case in scheme/host, and trailing slashes. Items without a URL are compared by normalized title. Items with neither a URL nor a title are kept. This tool does not fetch, rank, or rewrite results.
