---
name: check_url
track: bonus
kind: live_api
provider: HTTP Link Validator
requires_env: []
inputs: [urls]
outputs: [results, valid_urls, invalid_urls]
side_effect: false
---
# check_url

Validates one or more URLs before citing them in a response. Checks HTTP status
codes (detecting 404/410/5xx broken links and soft-404 pages) and inspects
redirects (`final_url`, `redirected`) to catch links that redirect to an
unrelated page, homepage, or error page.
