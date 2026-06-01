from dataclasses import dataclass
from datetime import date, timedelta
from skatelog.models import Session, Stance, Trick
from typing import Iterable, Iterator

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

def find_by_startswith(value: str, options: Iterable[str]) -> OptionResult:
    if (value or "-") == "-":
        return OptionResult(None)
    try:
        return OptionResult(next(o for o in options if o.lower().startswith(value.lower())))
    except StopIteration:
        return OptionResult(value, new=True)

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

def streak(sessions: Iterable[Session]) -> tuple[int, list[tuple[date, int]]]:
    """Finds streaks of skated days from given sessions."""
    sorted_sessions = sorted((s for s in sessions if s.skated), key=lambda it: it.day)
    current_streak = 0
    best_streak = 0
    days = []
    for session in sorted_sessions:
        if not days:
            current_streak = 1
        elif days[-1][0] + timedelta(days=1) == session.day:
            current_streak += 1
        else:
            delta = session.day - days[-1][0]
            missed_days = (days[-1][0] + timedelta(days=i) for i in range(1, delta.days))
            days += [(day, 0) for day in missed_days]
            current_streak = 1
        days.append((session.day, current_streak))
        best_streak = max(best_streak, current_streak)
    return (best_streak, days)

def new_tricks(tricks: Iterable[Trick]) -> Iterator[Trick]:
    """Finds only new tricks from the incoming list, which is assumed to be sorted chronlogically."""
    # keep a list with surface and without
    # if surface is present, the trick is new if there's not an entry with the same surface
    # if surface is empty, the trick is new if there's no entry both with and without a surface
    # abd means "already been done" of course
    abd: set[tuple[Stance, str, str]] = set()
    abd_no_surface: set[tuple[Stance, str]] = set()
    for trick in tricks:
        trick_key = (trick.stance, trick.name.casefold(), (trick.surface or "").casefold())
        trick_key_no_surface = trick_key[0:2]
        if trick.surface:
            if trick_key not in abd:
                abd.add(trick_key)
                abd_no_surface.add(trick_key_no_surface)
                yield trick
        elif trick_key_no_surface not in abd_no_surface:
            abd_no_surface.add(trick_key_no_surface)
            yield trick

