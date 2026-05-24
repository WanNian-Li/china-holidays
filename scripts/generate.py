#!/usr/bin/env python3
"""
Generate China holidays ICS subscription calendar from JSON data files.
Zero external dependencies — uses only Python standard library.
"""

import hashlib
import json
import sys
from datetime import date, timedelta, datetime, timezone
from pathlib import Path


# ── ICS helpers ──────────────────────────────────────────────────────────────

def fold_line(line: str) -> str:
    """Fold a single ICS property line per RFC 5545 (max 75 octets)."""
    if len(line.encode("utf-8")) <= 75:
        return line
    chunks = []
    current = b""
    for char in line:
        cb = char.encode("utf-8")
        limit = 74 if chunks else 75
        if len(current) + len(cb) > limit:
            chunks.append(current)
            current = cb
        else:
            current += cb
    if current:
        chunks.append(current)
    result = chunks[0].decode("utf-8")
    for chunk in chunks[1:]:
        result += "\r\n " + chunk.decode("utf-8")
    return result


def stable_uid(name: str, date_str: str) -> str:
    """Deterministic UID so re-generation never creates duplicates."""
    key = f"{date_str}:{name}".encode("utf-8")
    return hashlib.sha256(key).hexdigest()[:32] + "@china-holidays.ics"


def make_vevent(name: str, start: str, days: int = 1, description: str = "") -> str:
    start_date = date.fromisoformat(start)
    end_date = start_date + timedelta(days=days)
    dtstamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    props = [
        "BEGIN:VEVENT",
        f"UID:{stable_uid(name, start)}",
        f"DTSTAMP:{dtstamp}",
        f"DTSTART;VALUE=DATE:{start_date.strftime('%Y%m%d')}",
        f"DTEND;VALUE=DATE:{end_date.strftime('%Y%m%d')}",
        f"SUMMARY:{name}",
    ]
    if description:
        props.append(f"DESCRIPTION:{description}")
    props.append("END:VEVENT")
    return "\r\n".join(fold_line(p) for p in props)


# ── Loaders ───────────────────────────────────────────────────────────────────

def load_year(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    events = []

    for h in data.get("legal_holidays", []):
        events.append(make_vevent(
            name=f"{h['name']}",
            start=h["start"],
            days=h["days"],
            description=h.get("note", f"法定节假日，放假{h['days']}天"),
        ))

    for w in data.get("workday_adjustments", []):
        events.append(make_vevent(
            name="调休补班",
            start=w["date"],
            days=1,
            description=w.get("note", "调休补班工作日"),
        ))

    for t in data.get("traditional_holidays", []):
        events.append(make_vevent(
            name=f"{t['name']}",
            start=t["date"],
            days=1,
            description=t.get("note", ""),
        ))

    return events


def load_solar_terms(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    events = []
    for year_terms in data.values():
        if not isinstance(year_terms, list):
            continue
        for term in year_terms:
            events.append(make_vevent(
                name=f"{term['name']}",
                start=term["date"],
                days=1,
                description="二十四节气",
            ))
    return events


# ── Builder ───────────────────────────────────────────────────────────────────

HEADER = "\r\n".join([
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//China Holidays//ZH",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    "X-WR-CALNAME:中国节假日",
    "X-WR-TIMEZONE:Asia/Shanghai",
    "X-WR-CALDESC:法定节假日 · 调休补班 · 传统节日 · 二十四节气",
    "X-APPLE-CALENDAR-COLOR:#FF3B30",
    "REFRESH-INTERVAL;VALUE=DURATION:P1D",
    "X-PUBLISHED-TTL:P1D",
])


def generate(data_dir: str = "data", output: str = "output/china-holidays.ics"):
    data_path = Path(data_dir)
    events: list[str] = []

    year_files = sorted(data_path.glob("[0-9]*.json"))
    if not year_files:
        print(f"[错误] 在 {data_dir}/ 下未找到年份数据文件", file=sys.stderr)
        sys.exit(1)

    for f in year_files:
        year_events = load_year(f)
        events.extend(year_events)
        print(f"  ✔ {f.name}  ({len(year_events)} 个事件)")

    solar_path = data_path / "solar_terms.json"
    if solar_path.exists():
        solar_events = load_solar_terms(solar_path)
        events.extend(solar_events)
        print(f"  ✔ solar_terms.json  ({len(solar_events)} 个节气)")

    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    body = "\r\n".join(events)
    content = HEADER + "\r\n" + body + "\r\nEND:VCALENDAR\r\n"
    out_path.write_text(content, encoding="utf-8")

    print(f"\n✅ 生成完成 → {output}")
    print(f"   共 {len(events)} 个事件")


if __name__ == "__main__":
    generate()
