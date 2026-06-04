from datetime import date
from fastapi import FastAPI
from sqlmodel import Session as DBSession
from skatelog.cli_util import date_range, new_tricks, streak, Streak
from skatelog.db import get_engine
from skatelog.models import Session, Trick
import skatelog.queries as query
from skatelog.queries import SessionAggregate

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
             year: str | None = None) -> list[Session]:
    """List sessions."""
    start, end = date_range(month, year)
    with DBSession(get_engine()) as db:
        sessions = query.find_by_date_range(db, start, end)
        return list(sessions)

@app.get("/tricks")
def list_tricks_cmd(month: str | None = None,
                    year: str | None = None,
                    new: bool = False) -> list[Trick]:
    """List tricks."""
    start, end = date_range(month, year)
    with DBSession(get_engine()) as db:
        tricks = query.find_tricks_by_date_range(db, start, end)
        tricks = new_tricks(tricks) if new else tricks
        return list(tricks)

@app.get("/disciplines")
def list_disciplines_cmd(
    month: str | None = None,
    year: str | None = None,
) -> list[SessionAggregate]:
    """List all disciplines."""
    start, end = date_range(month, year)
    with DBSession(get_engine()) as db:
        aggs = query.find_discipline_counts(db, start, end)
    return list(sorted(aggs, key=lambda it: it.key))

@app.get("/locations")
def list_locations_cmd(
    month: str | None = None,
    year: str | None = None,
) -> list[SessionAggregate]:
    """List all locations."""
    start, end = date_range(month, year)
    with DBSession(get_engine()) as db:
        aggs = query.find_location_counts(db, start, end)
    return list(sorted(aggs, key=lambda it: it.count, reverse=True))

@app.get("/shoes")
def list_shoes_cmd(
    month: str | None = None,
    year: str | None = None,
) -> list[SessionAggregate]:
    """List all shoes."""
    start, end = date_range(month, year)
    with DBSession(get_engine()) as db:
        aggs = query.find_shoe_counts(db, start, end)
    return list(sorted(aggs, key=lambda it: it.count, reverse=True))

@app.get("/boards")
def list_boards_cmd(
    month: str | None = None,
    year: str | None = None,
) -> list[SessionAggregate]:
    """List all boards."""
    start, end = date_range(month, year)
    with DBSession(get_engine()) as db:
        aggs = query.find_board_counts(db, start, end)
    return list(sorted(aggs, key=lambda it: it.count, reverse=True))

@app.get("/streak")
def streak_cmd(
    month: str | None = None,
    year: str | None = None,
) -> Streak:
    """Finds best streak and lists current streak by day."""
    start, end = date_range(month, year)
    with DBSession(get_engine()) as db:
        sessions = query.find_by_date_range(db, start, end)
        return streak(sessions)

