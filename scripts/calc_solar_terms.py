#!/usr/bin/env python3
"""
Auto-calculate solar term dates using astronomical computation.
Requires: pip install ephem

Usage:
  python scripts/calc_solar_terms.py              # update 2024-2027
  python scripts/calc_solar_terms.py 2026 2027    # specific years
"""

import ephem
import json
import math
import sys
from datetime import timedelta
from pathlib import Path

# Solar terms in order, with their ecliptic longitude and approximate month
SOLAR_TERMS = [
    ("小寒",  285,  1),
    ("大寒",  300,  1),
    ("立春",  315,  2),
    ("雨水",  330,  2),
    ("惊蛰",  345,  3),
    ("春分",    0,  3),
    ("清明",   15,  4),
    ("谷雨",   30,  4),
    ("立夏",   45,  5),
    ("小满",   60,  5),
    ("芒种",   75,  6),
    ("夏至",   90,  6),
    ("小暑",  105,  7),
    ("大暑",  120,  7),
    ("立秋",  135,  8),
    ("处暑",  150,  8),
    ("白露",  165,  9),
    ("秋分",  180,  9),
    ("寒露",  195, 10),
    ("霜降",  210, 10),
    ("立冬",  225, 11),
    ("小雪",  240, 11),
    ("大雪",  255, 12),
    ("冬至",  270, 12),
]


def sun_longitude(ephem_date: float) -> float:
    """Return Sun's apparent ecliptic longitude in degrees [0, 360)."""
    sun = ephem.Sun(ephem_date)
    ecl = ephem.Ecliptic(sun, epoch=ephem_date)
    return math.degrees(ecl.lon) % 360


def find_solar_term(year: int, target_lon: float, month_hint: int) -> str:
    """
    Binary-search for the moment sun reaches target_lon (degrees).
    Returns the date string in CST (UTC+8).
    """
    # Search window: ±15 days around the 1st of the expected month
    lo = ephem.Date(f"{year}/{month_hint}/1") - 15
    hi = ephem.Date(f"{year}/{month_hint}/1") + 20

    # angular_diff maps to [-180, 180] to handle 0°/360° boundary cleanly
    def angular_diff(d: float) -> float:
        lon = sun_longitude(d)
        return ((lon - target_lon + 180) % 360) - 180

    for _ in range(60):  # bisect to ~nanosecond precision
        mid = (lo + hi) / 2
        if angular_diff(mid) > 0:
            hi = mid
        else:
            lo = mid

    utc_dt = ephem.Date(mid).datetime()
    cst_dt = utc_dt + timedelta(hours=8)
    return cst_dt.strftime("%Y-%m-%d")


def calc_year(year: int) -> list[dict]:
    terms = []
    for name, lon, month in SOLAR_TERMS:
        date_str = find_solar_term(year, lon, month)
        terms.append({"name": name, "date": date_str})
        print(f"    {date_str}  {name}")
    return terms


def main(years: list[int] | None = None):
    if years is None:
        years = [2024, 2025, 2026, 2027]

    out_path = Path("data/solar_terms.json")
    data: dict = {}
    if out_path.exists():
        raw = json.loads(out_path.read_text(encoding="utf-8"))
        # preserve metadata keys (those not starting with a digit)
        data = {k: v for k, v in raw.items() if not k[:1].isdigit()}
        data.update({k: v for k, v in raw.items() if k[:1].isdigit()})

    for year in years:
        print(f"\n计算 {year} 年节气…")
        data[str(year)] = calc_year(year)

    # Write sorted by year
    ordered = {k: data[k] for k in sorted(data)}
    out_path.write_text(
        json.dumps(ordered, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n✅ 已更新 {out_path}")


if __name__ == "__main__":
    years = [int(y) for y in sys.argv[1:]] if len(sys.argv) > 1 else None
    main(years)
