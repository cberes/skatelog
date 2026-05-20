from datetime import date
from typing import Callable

DISCIPLINE_ATTRS = [
    "a_frame",
    "bank",
    "bowl",
    "box",
    "flat",
    "free",
    "hip",
    "manual",
    "rail",
    "slappy",
    "transition",
    "vert",
]

def find_by_startswith(value: str, options: list[str], new_value: Callable[[str], None]) -> str | None:
    if (value or "-") == "-":
        return None
    try:
        return next(o for o in options if o.lower().startswith(value.lower()))
    except StopIteration:
        new_value(value)
        return value

def find_disciplines(disciplines: str | None, skipped: Callable[[str], None]) -> dict[str, bool]:
    discipline_flags = {}
    for d in (disciplines or "").split(","):
        if not d or d.isspace():
            continue
        matches = {attr: True for attr in DISCIPLINE_ATTRS if attr.lower().startswith(d.strip().lower())}
        if len(matches) == 1:
            discipline_flags.update(matches)
        elif len(matches) > 1:
            skipped(d)
    return discipline_flags

def _month_range(month: str) -> tuple[date, date]:
    start = date.strptime(month, "%Y-%m")
    next_year = start.year + (start.month // 12)
    next_month = (start.month % 12) + 1
    end = date(next_year, next_month, start.day)
    return (start, end)

def _year_range(year: str) -> tuple[date, date]:
    start = date.strptime(year, "%Y")
    end = date(start.year + 1, start.month, start.day)
    return (start, end)

def date_range(month: str | None, year: str | None) -> tuple[date, date]:
    if month is not None:
        return _month_range(month)
    elif year is not None:
        return _year_range(year)
    else:
        return (date.min, date.max)
