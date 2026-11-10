from __future__ import annotations

from datetime import datetime, timedelta, timezone as dt_timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from tools._shared import err

FIXED_OFFSETS: dict[str, tuple[str, int]] = {
    "asia/ho_chi_minh": ("Asia/Ho_Chi_Minh", 7),
    "asia/saigon": ("Asia/Ho_Chi_Minh", 7),
    "asia/bangkok": ("Asia/Bangkok", 7),
    "vn": ("Asia/Ho_Chi_Minh", 7),
    "ict": ("Asia/Ho_Chi_Minh", 7),
    "utc": ("UTC", 0),
    "gmt": ("UTC", 0),
    "etc/utc": ("UTC", 0),
    "asia/tokyo": ("Asia/Tokyo", 9),
    "asia/singapore": ("Asia/Singapore", 8),
    "europe/london": ("Europe/London", 0),
    "america/new_york": ("America/New_York", -5),
    "america/los_angeles": ("America/Los_Angeles", -8),
}

WEEKDAY_VI = {
    0: "Thứ Hai",
    1: "Thứ Ba",
    2: "Thứ Tư",
    3: "Thứ Năm",
    4: "Thứ Sáu",
    5: "Thứ Bảy",
    6: "Chủ Nhật",
}


def _resolve_timezone(tz_input: str) -> tuple[str, Any]:
    cleaned = (tz_input or "").strip() or "Asia/Ho_Chi_Minh"
    key = cleaned.lower()
    if key in FIXED_OFFSETS:
        canonical, hours = FIXED_OFFSETS[key]
        try:
            return canonical, ZoneInfo(canonical)
        except ZoneInfoNotFoundError:
            return canonical, dt_timezone(timedelta(hours=hours))

    try:
        return cleaned, ZoneInfo(cleaned)
    except (ZoneInfoNotFoundError, KeyError, ValueError) as exc:
        raise ValueError(f"Unsupported or invalid timezone: {cleaned}") from exc


def get_current_time(timezone: str = "Asia/Ho_Chi_Minh") -> dict[str, Any]:
    try:
        canonical_tz, tz_obj = _resolve_timezone(timezone)
        now = datetime.now(tz_obj)
        weekday_en = now.strftime("%A")
        weekday_vi = WEEKDAY_VI.get(now.weekday(), weekday_en)
        formatted = (
            f"{weekday_vi}, ngày {now.day:02d} tháng {now.month:02d} năm {now.year}, "
            f"{now.strftime('%H:%M:%S')} ({canonical_tz})"
        )
        return {
            "tool": "get_current_time",
            "timezone": canonical_tz,
            "iso": now.isoformat(timespec="seconds"),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "year": now.year,
            "month": now.month,
            "day": now.day,
            "weekday": weekday_en,
            "weekday_vi": weekday_vi,
            "formatted": formatted,
        }
    except Exception as exc:
        return err("get_current_time", exc)
