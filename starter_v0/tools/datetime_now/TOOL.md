---
name: datetime_now
track: bonus
kind: local_knowledge
provider: Local ZoneInfo
requires_env: []
inputs: [timezone]
outputs: [timezone, iso, date, time, weekday, weekday_vi, utc_offset, iso_week, week_start, week_end, unix]
side_effect: false
---
# datetime_now

Returns the current date and time in an IANA timezone (default `Asia/Ho_Chi_Minh`),
plus the Monday–Sunday bounds of the current week. Fully offline, no API key.
