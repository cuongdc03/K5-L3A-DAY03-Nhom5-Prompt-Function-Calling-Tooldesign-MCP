---
name: current_time
track: bonus
kind: local_knowledge
provider: System Clock
requires_env: []
inputs: [timezone]
outputs: [timezone, iso, date, time, year, month, day, weekday, weekday_vi, formatted]
side_effect: false
---
# current_time

Returns the current system date, time, weekday, and year for a given timezone
(defaults to `Asia/Ho_Chi_Minh`, UTC+7). Use this tool when the user asks about
the current date/time/year or when accurate temporal context is needed before
calling other research tools.
