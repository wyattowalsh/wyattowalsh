from __future__ import annotations

from datetime import date as dt_date
from datetime import datetime

from scripts.art.shared import (
    contributions_monthly_to_daily_series,
    map_date_to_loop_delay,
    normalize_timeline_window,
)


def test_normalize_timeline_window_uses_history_and_events() -> None:
    history = {
        "account_created": "2019-04-05T10:00:00Z",
        "repos": [{"date": "2020-01-10T00:00:00Z"}],
        "stars": [{"date": "2022-06-01T00:00:00Z"}],
        "contributions_monthly": {"2021-03": 12},
    }
    events = [{"date": "2023-02-15T00:00:00Z"}]
    start, end = normalize_timeline_window(events, history)
    assert start == dt_date(2019, 4, 5)
    assert end == dt_date(2023, 2, 15)


def test_normalize_timeline_window_fallback_without_dates() -> None:
    now = dt_date(2026, 3, 20)
    start, end = normalize_timeline_window([], {}, fallback_days=30, now=now)
    assert start == dt_date(2026, 2, 18)
    assert end == now


def test_map_date_to_loop_delay_with_clamp_and_easing() -> None:
    window = (dt_date(2020, 1, 1), dt_date(2020, 1, 11))
    assert map_date_to_loop_delay("2019-01-01", window, duration=30.0) == 0.0
    assert map_date_to_loop_delay("2020-01-11", window, duration=30.0) == 27.9
    assert map_date_to_loop_delay("2020-01-06", window, duration=30.0, easing_power=2.0) == 6.975


def test_map_date_to_loop_delay_orders_early_mid_late_inside_window() -> None:
    window = (dt_date(2020, 1, 1), dt_date(2020, 1, 11))

    early = map_date_to_loop_delay("2020-01-02", window, duration=30.0)
    mid = map_date_to_loop_delay("2020-01-06", window, duration=30.0)
    late = map_date_to_loop_delay("2020-01-10", window, duration=30.0)

    assert early == 2.79
    assert mid == 13.95
    assert late == 25.11
    assert 0.0 <= early < mid < late <= 27.9


def test_map_date_to_loop_delay_invalid_when_falls_back_to_window_start() -> None:
    window = (dt_date(2020, 1, 1), dt_date(2020, 1, 11))

    for invalid_when in (None, "", "not-a-date", {"date": "2020-01-03"}):
        assert map_date_to_loop_delay(invalid_when, window, duration=30.0) == 0.0


def test_normalize_timeline_window_accepts_datetime_objects() -> None:
    history = {
        "account_created": datetime(2019, 4, 5, 10, 0, 0),
        "repos": [{"date": datetime(2020, 1, 10, 0, 0, 0)}],
        "stars": [{"date": datetime(2022, 6, 1, 0, 0, 0)}],
    }
    events = [{"date": datetime(2023, 2, 15, 18, 30, 0)}]
    start, end = normalize_timeline_window(events, history)
    assert start == dt_date(2019, 4, 5)
    assert end == dt_date(2023, 2, 15)


def test_map_date_to_loop_delay_accepts_datetime_object() -> None:
    window = (dt_date(2020, 1, 1), dt_date(2020, 1, 11))
    result = map_date_to_loop_delay(datetime(2020, 1, 6, 12, 0, 0), window, duration=30.0)
    assert result == 13.95


def test_contributions_monthly_to_daily_series_with_full_month_keys() -> None:
    series = contributions_monthly_to_daily_series({"2024-02": 29, "2024-03": 0})
    assert len(series) == 60
    feb = [v for k, v in series.items() if k.startswith("2024-02-")]
    mar = [v for k, v in series.items() if k.startswith("2024-03-")]
    assert sum(feb) == 29
    assert all(v == 1 for v in feb)
    assert sum(mar) == 0


def test_contributions_monthly_to_daily_series_handles_month_only_history() -> None:
    series = contributions_monthly_to_daily_series({"01": 31, "03": 31}, reference_year=2025)
    assert "2025-01-01" in series
    assert "2025-03-31" in series
    feb = [v for k, v in series.items() if k.startswith("2025-02-")]
    assert len(feb) == 28
    assert sum(feb) == 0
    jan = [v for k, v in series.items() if k.startswith("2025-01-")]
    mar = [v for k, v in series.items() if k.startswith("2025-03-")]
    assert sum(jan) == 31
    assert sum(mar) == 31


def test_contributions_monthly_to_daily_series_empty_or_invalid_inputs() -> None:
    assert contributions_monthly_to_daily_series({}) == {}
    assert contributions_monthly_to_daily_series({"bad-key": 10, "13": 5}) == {}
