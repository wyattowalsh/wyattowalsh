"""Timeline and contribution-series helpers for living-art."""
from __future__ import annotations

import calendar
import hashlib
import re
from collections.abc import Mapping, Sequence
from datetime import date as dt_date
from datetime import datetime, timedelta
from typing import Any

_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_YYYY_MM_RE = re.compile(r"^\d{4}-\d{2}$")
_MONTH_ONLY_RE = re.compile(r"^\d{1,2}$")


def _as_date(value: Any) -> dt_date | None:
    """Convert common date representations into ``datetime.date``."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, dt_date):
        return value
    if not isinstance(value, str):
        return None
    s = value.strip()
    if not s:
        return None
    if _ISO_DATE_RE.match(s):
        try:
            return dt_date.fromisoformat(s)
        except ValueError:
            return None
    if _YYYY_MM_RE.match(s):
        try:
            year, month = map(int, s.split("-"))
            return dt_date(year, month, 1)
        except ValueError:
            return None
    if "T" in s:
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
        except ValueError:
            return None
    return None


def normalize_timeline_window(
    dated_events: Sequence[Any] | None = None,
    history: Mapping[str, Any] | None = None,
    *,
    fallback_days: int = 365,
    now: dt_date | None = None,
) -> tuple[dt_date, dt_date]:
    """Infer a normalized [start, end] window from history and dated events."""
    observed: list[dt_date] = []
    if dated_events:
        for event in dated_events:
            if isinstance(event, Mapping):
                parsed = _as_date(event.get("date"))
            else:
                parsed = _as_date(event)
            if parsed:
                observed.append(parsed)

    if history:
        for key in ("account_created",):
            parsed = _as_date(history.get(key))
            if parsed:
                observed.append(parsed)
        for collection in ("repos", "stars", "forks"):
            for item in history.get(collection, []) or []:
                if isinstance(item, Mapping):
                    parsed = _as_date(item.get("date"))
                    if parsed:
                        observed.append(parsed)
        for month_key in (history.get("contributions_monthly", {}) or {}).keys():
            parsed = _as_date(month_key)
            if parsed:
                observed.append(parsed)
        for day_key in (history.get("contributions_daily", {}) or {}).keys():
            parsed = _as_date(day_key)
            if parsed:
                observed.append(parsed)

    if observed:
        start = min(observed)
        end = max(observed)
        return (start, end if end >= start else start)

    today = now or dt_date.today()
    safe_days = max(int(fallback_days), 1)
    return today - timedelta(days=safe_days), today


def map_date_to_loop_delay(
    when: Any,
    window: tuple[dt_date, dt_date],
    *,
    duration: float,
    reveal_fraction: float = 0.93,
    easing_power: float = 1.0,
) -> float:
    """Map a real date into a loop delay in seconds, clamped to timeline window."""
    start, end = window
    if end < start:
        start, end = end, start
    parsed = _as_date(when)
    if parsed is None:
        parsed = start
    clamped = min(max(parsed, start), end)
    span_days = max((end - start).days, 1)
    frac = (clamped - start).days / span_days
    eased = frac ** max(easing_power, 0.01)
    reveal_end = max(duration, 0.0) * max(min(reveal_fraction, 1.0), 0.0)
    return round(eased * reveal_end, 3)


def _iter_months(start_year: int, start_month: int, end_year: int, end_month: int) -> list[tuple[int, int]]:
    """Yield (year, month) inclusive between start and end."""
    out: list[tuple[int, int]] = []
    year, month = start_year, start_month
    while (year, month) <= (end_year, end_month):
        out.append((year, month))
        month += 1
        if month > 12:
            month = 1
            year += 1
    return out


def _distribute_monthly_count(year: int, month: int, count: int) -> list[int]:
    """Deterministically spread monthly counts across month days."""
    days_in_month = calendar.monthrange(year, month)[1]
    count = max(int(count), 0)
    if count == 0:
        return [0] * days_in_month

    base, remainder = divmod(count, days_in_month)
    daily = [base] * days_in_month
    if remainder == 0:
        return daily

    seed = int(hashlib.sha256(f"{year:04d}-{month:02d}".encode()).hexdigest()[:8], 16)
    start = seed % days_in_month
    step = max(1, days_in_month // remainder)
    used: set[int] = set()
    idx = start
    for _ in range(remainder):
        while idx in used:
            idx = (idx + 1) % days_in_month
        used.add(idx)
        daily[idx] += 1
        idx = (idx + step) % days_in_month
    return daily


def contributions_monthly_to_daily_series(
    contributions_monthly: Mapping[str, int] | None,
    *,
    reference_year: int | None = None,
) -> dict[str, int]:
    """Expand monthly contribution buckets into deterministic per-day series."""
    if not contributions_monthly:
        return {}

    ref_year = reference_year or dt_date.today().year
    month_counts: dict[tuple[int, int], int] = {}
    for key, value in contributions_monthly.items():
        k = str(key).strip()
        if _YYYY_MM_RE.match(k):
            year, month = map(int, k.split("-"))
        elif _MONTH_ONLY_RE.match(k):
            month = int(k)
            year = ref_year
        else:
            continue
        if not (1 <= month <= 12):
            continue
        month_counts[(year, month)] = max(0, int(value or 0))

    if not month_counts:
        return {}

    (start_y, start_m) = min(month_counts.keys())
    (end_y, end_m) = max(month_counts.keys())
    daily: dict[str, int] = {}
    for year, month in _iter_months(start_y, start_m, end_y, end_m):
        distributed = _distribute_monthly_count(year, month, month_counts.get((year, month), 0))
        for day, count in enumerate(distributed, start=1):
            iso = dt_date(year, month, day).isoformat()
            daily[iso] = count
    return daily
