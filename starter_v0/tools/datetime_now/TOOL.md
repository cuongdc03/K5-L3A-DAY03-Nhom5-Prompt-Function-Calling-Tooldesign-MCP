---
name: datetime_now
track: bonus
kind: local_knowledge
requires_env: []
inputs: [timezone]
outputs: [timezone, iso, date, time, weekday, weekday_vi, utc_offset, iso_week, week_start, week_end, unix]
side_effect: false
---
# datetime_now

Returns the current date and time in an IANA timezone (default `Asia/Ho_Chi_Minh`),
plus the Monday–Sunday bounds of the current week. Fully offline, no API key.

Use it when the answer depends on "now": today's date, the weekday, the time in another
city, or turning "this week" / "yesterday" into concrete dates before calling `lookup`
or `social_search`. Do not use it for news content itself (use `lookup`).

An unknown timezone returns an error dict (`error`, `message`) instead of raising.
