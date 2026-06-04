from collections.abc import Iterator
from datetime import date
from fastapi import FastAPI
from sqlmodel import Session as DBSession
from skatelog.cli_util import date_range, new_tricks, streak
from skatelog.db import get_engine
from skatelog.models import Session, Trick
import skatelog.queries as query
from skatelog.queries import SessionAggregate
from typing import Any

app = FastAPI()

@app.get("/sessions/{day}")
def show_cmd(day: str) -> Session | None:
    """Show a day's session."""
    target = date.fromisoformat(day)
    with DBSession(get_engine()) as db:
        session = query.find_session(db, target)
        return session

@app.get("/sessions")
def list_cmd(month: str | None = None,
             year: str | None = None) -> Iterator[Session]:
    """List sessions."""
    start, end = date_range(month, year)
    with DBSession(get_engine()) as db:
        for session in query.find_by_date_range(db, start, end):
            yield session

@app.get("/tricks")
def list_tricks_cmd(month: str | None = None,
                    year: str | None = None,
                    new: bool = False) -> Iterator[Trick]:
    """List tricks."""
    start, end = date_range(month, year)
    with DBSession(get_engine()) as db:
        tricks = query.find_tricks_by_date_range(db, start, end)
        tricks = new_tricks(tricks) if new else tricks
        return tricks

@app.get("/disciplines")
def list_disciplines_cmd(
    month: str | None = None,
    year: str | None = None,
) -> Iterator[SessionAggregate]:
    """List all disciplines."""
    start, end = date_range(month, year)
    with DBSession(get_engine()) as db:
        aggs = query.find_discipline_counts(db, start, end)
    for row in sorted(aggs, key=lambda it: it.key):
        yield row

@app.get("/locations")
def list_locations_cmd(
    month: str | None = None,
    year: str | None = None,
) -> Iterator[SessionAggregate]:
    """List all locations."""
    start, end = date_range(month, year)
    with DBSession(get_engine()) as db:
        aggs = query.find_location_counts(db, start, end)
    for row in sorted(aggs, key=lambda it: it.count, reverse=True):
        yield row

@app.get("/shoes")
def list_shoes_cmd(
    month: str | None = None,
    year: str | None = None,
) -> Iterator[SessionAggregate]:
    """List all shoes."""
    start, end = date_range(month, year)
    with DBSession(get_engine()) as db:
        aggs = query.find_shoe_counts(db, start, end)
    for row in sorted(aggs, key=lambda it: it.count, reverse=True):
        yield row

@app.get("/boards")
def list_boards_cmd(
    month: str | None = None,
    year: str | None = None,
) -> Iterator[SessionAggregate]:
    """List all boards."""
    start, end = date_range(month, year)
    with DBSession(get_engine()) as db:
        aggs = query.find_board_counts(db, start, end)
    for row in sorted(aggs, key=lambda it: it.count, reverse=True):
        yield row

@app.get("/streak")
def streak_cmd(
    month: str | None = None,
    year: str | None = None,
) -> dict[str, Any]:
    """Finds best streak and lists current streak by day."""
    start, end = date_range(month, year)
    with DBSession(get_engine()) as db:
        sessions = query.find_by_date_range(db, start, end)
        best, days = streak(sessions)
    return {
        "best": best,
        "days": [{"day": day[0], "streak": day[1]} for day in days],
    }

