from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from tools._shared import err

DEFAULT_TIMEZONE = "Asia/Ho_Chi_Minh"
WEEKDAYS_VI = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]


def _now(tz: ZoneInfo) -> datetime:
    """Single clock access point so tests can freeze time."""
    return datetime.now(tz)


def get_current_datetime(timezone: str = DEFAULT_TIMEZONE) -> dict[str, Any]:
    """Return the current date/time in an IANA timezone (default Asia/Ho_Chi_Minh)."""
    name = timezone.strip() if isinstance(timezone, str) and timezone.strip() else DEFAULT_TIMEZONE
    try:
        now = _now(ZoneInfo(name))
        week_start = (now - timedelta(days=now.weekday())).date()
        offset = now.strftime("%z")
        return {
            "tool": "get_current_datetime",
            "timezone": name,
            "iso": now.isoformat(timespec="seconds"),
            "date": now.date().isoformat(),
            "time": now.strftime("%H:%M:%S"),
            "weekday": now.strftime("%A"),
            "weekday_vi": WEEKDAYS_VI[now.weekday()],
            "utc_offset": f"{offset[:3]}:{offset[3:]}",
            "iso_week": now.isocalendar().week,
            "week_start": week_start.isoformat(),
            "week_end": (week_start + timedelta(days=6)).isoformat(),
            "unix": int(now.timestamp()),
        }
    except (ZoneInfoNotFoundError, ValueError, OSError) as exc:
        result = err("get_current_datetime", exc)
        result["message"] = f"Unknown timezone '{name}'. Use an IANA name such as Asia/Ho_Chi_Minh or America/New_York."
        return result
    except Exception as exc:
        return err("get_current_datetime", exc)
