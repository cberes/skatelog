from dataclasses import dataclass
from datetime import date
from typing import Callable

@dataclass
class OptionResult:
    found: str | None
    new: bool = False

@dataclass
class DisciplineResult:
    found: dict[str, bool]
    ambiguous: list[str]
    unknown: list[str]

_DISCIPLINE_ATTRS = [
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

def find_by_startswith(value: str, options: list[str]) -> OptionResult:
    if (value or "-") == "-":
        return OptionResult(None)
    try:
        return OptionResult(next(o for o in options if o.lower().startswith(value.lower())))
    except StopIteration:
        return OptionResult(value, True)

def find_disciplines(disciplines: str | None) -> DisciplineResult:
    result = DisciplineResult({}, [], [])
    for d in (disciplines or "").split(","):
        if not d or d.isspace():
            continue
        matches = {attr: True for attr in _DISCIPLINE_ATTRS if attr.lower().startswith(d.strip().lower())}
        match len(matches):
            case 0:
                result.unknown.append(d)
            case 1:
                result.found.update(matches)
            case x if x > 1:
                result.ambiguous.append(d)
    return result

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
