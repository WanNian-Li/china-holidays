#!/usr/bin/env python3
"""
Fetch official Chinese holiday data from holiday-cn (github.com/NateScarlet/holiday-cn).
Updates legal_holidays and workday_adjustments in data/YYYY.json.
Preserves traditional_holidays written manually.

Usage:
  python scripts/fetch_holidays.py          # current year + next year
  python scripts/fetch_holidays.py 2025 2026
"""

import json
import sys
import urllib.request
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

BASE_URL = (
    "https://raw.githubusercontent.com/NateScarlet/holiday-cn/master/{year}.json"
)


def fetch_raw(year: int) -> dict:
    url = BASE_URL.format(year=year)
    print(f"  ↓ {url}")
    with urllib.request.urlopen(url, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def parse(raw: dict) -> tuple[list[dict], list[dict]]:
    """
    Convert holiday-cn flat day list into:
      - legal_holidays: consecutive same-name off-days grouped into blocks
      - workday_adjustments: isOffDay=false days (weekends made into workdays)
    """
    off_days  = sorted([d for d in raw["days"] if     d["isOffDay"]], key=lambda x: x["date"])
    work_days = sorted([d for d in raw["days"] if not d["isOffDay"]], key=lambda x: x["date"])

    # Group consecutive same-name off-days into blocks
    legal: list[dict] = []
    if off_days:
        cur_name  = off_days[0]["name"]
        cur_start = off_days[0]["date"]
        cur_end   = off_days[0]["date"]

        for d in off_days[1:]:
            prev_dt = date.fromisoformat(cur_end)
            curr_dt = date.fromisoformat(d["date"])
            same_name    = d["name"] == cur_name
            consecutive  = curr_dt - prev_dt <= timedelta(days=1)

            if same_name and consecutive:
                cur_end = d["date"]
            else:
                start_dt = date.fromisoformat(cur_start)
                end_dt   = date.fromisoformat(cur_end)
                legal.append({
                    "name":  cur_name,
                    "start": cur_start,
                    "days":  (end_dt - start_dt).days + 1,
                })
                cur_name  = d["name"]
                cur_start = d["date"]
                cur_end   = d["date"]

        start_dt = date.fromisoformat(cur_start)
        end_dt   = date.fromisoformat(cur_end)
        legal.append({
            "name":  cur_name,
            "start": cur_start,
            "days":  (end_dt - start_dt).days + 1,
        })

    workdays = [{"date": d["date"], "note": f"{d['name']}调休补班"} for d in work_days]
    return legal, workdays


def update(year: int) -> bool:
    try:
        raw = fetch_raw(year)
    except Exception as e:
        print(f"  ⚠️  {year} 年数据暂不可用（{e}），跳过")
        return False

    out_path = Path(f"data/{year}.json")
    existing: dict = {}
    if out_path.exists():
        existing = json.loads(out_path.read_text(encoding="utf-8"))

    legal, workdays = parse(raw)
    existing["year"]                = year
    existing["legal_holidays"]      = legal
    existing["workday_adjustments"] = workdays
    # traditional_holidays is NOT overwritten — keep manual entries

    out_path.write_text(
        json.dumps(existing, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  ✅ {out_path}  ({len(legal)} 个假期, {len(workdays)} 个补班)")
    return True


def main(years: list[int] | None = None):
    if years is None:
        today = date.today()
        years = [today.year, today.year + 1]

    for year in years:
        print(f"\n处理 {year} 年官方节假日…")
        update(year)


if __name__ == "__main__":
    years = [int(y) for y in sys.argv[1:]] if len(sys.argv) > 1 else None
    main(years)
