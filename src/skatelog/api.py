from datetime import date
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Response
from sqlmodel import Session as DBSession
from skatelog.cli_util import date_range, new_tricks, streak, Streak
from skatelog.dashboard import router as dashboard_router
from skatelog.deps import get_db
from skatelog.models import Session, Trick
import skatelog.queries as query
from typing import Annotated

app = FastAPI()
api = APIRouter(prefix="/api/v1")
app.include_router(dashboard_router)

@api.get("/sessions/{day}")
def show_api(db: Annotated[DBSession, Depends(get_db)],
             day: str) -> Session | None:
    """Show a day's session."""
    target = date.fromisoformat(day)
    session = query.find_session(db, target)
    if session is None:
        raise HTTPException(status_code=404, detail=f"No session for {day}")
    return session

@api.get("/sessions/{day}/tricks")
def show_tricks_api(db: Annotated[DBSession, Depends(get_db)],
                    day: str) -> list[Trick]:
    """Show a day's session."""
    target = date.fromisoformat(day)
    session = query.find_session(db, target)
    if session is None:
        raise HTTPException(status_code=404, detail=f"No session for {day}")
    return session.tricks

@api.get("/sessions")
def list_api(db: Annotated[DBSession, Depends(get_db)],
             month: int | str | None = None,
             year: int | str | None = None) -> list[Session]:
    """List sessions."""
    start, end = date_range(month, year)
    sessions = query.find_by_date_range(db, start, end)
    return list(sessions)

@api.get("/tricks")
def list_tricks_api(db: Annotated[DBSession, Depends(get_db)],
                    month: int | str | None = None,
                    year: int | str | None = None,
                    new: bool = False) -> list[Trick]:
    """List tricks."""
    start, end = date_range(month, year)
    tricks = query.find_tricks_by_date_range(db, start, end)
    tricks = new_tricks(tricks) if new else tricks
    return list(tricks)

@api.get("/disciplines")
def list_disciplines_api(
    db: Annotated[DBSession, Depends(get_db)],
    month: int | str | None = None,
    year: int | str | None = None,
) -> list[query.SessionAggregate]:
    """List all disciplines."""
    start, end = date_range(month, year)
    aggs = query.find_discipline_counts(db, start, end)
    return list(sorted(aggs, key=lambda it: it.key))

@api.get("/locations")
def list_locations_api(
    db: Annotated[DBSession, Depends(get_db)],
    month: int | str | None = None,
    year: int | str | None = None,
) -> list[query.SessionAggregate]:
    """List all locations."""
    start, end = date_range(month, year)
    aggs = query.find_location_counts(db, start, end)
    return list(sorted(aggs, key=lambda it: it.count, reverse=True))

@api.get("/shoes")
def list_shoes_api(
    db: Annotated[DBSession, Depends(get_db)],
    month: int | str | None = None,
    year: int | str | None = None,
) -> list[query.SessionAggregate]:
    """List all shoes."""
    start, end = date_range(month, year)
    aggs = query.find_shoe_counts(db, start, end)
    return list(sorted(aggs, key=lambda it: it.count, reverse=True))

@api.get("/boards")
def list_boards_api(
    db: Annotated[DBSession, Depends(get_db)],
    month: int | str | None = None,
    year: int | str | None = None,
) -> list[query.SessionAggregate]:
    """List all boards."""
    start, end = date_range(month, year)
    aggs = query.find_board_counts(db, start, end)
    return list(sorted(aggs, key=lambda it: it.count, reverse=True))

@api.get("/streak")
def streak_api(
    db: Annotated[DBSession, Depends(get_db)],
    month: int | str | None = None,
    year: int | str | None = None,
) -> Streak:
    """Finds best streak and lists current streak by day."""
    start, end = date_range(month, year)
    sessions = query.find_by_date_range(db, start, end)
    return streak(sessions)

@api.post("/sessions", status_code=201)
def add_session_api(db: Annotated[DBSession, Depends(get_db)],
                    session: Session) -> Session:
    """Creates a new session."""
    if not session.tricks:
        session.tricks = []
        session.parse_tricks()

    if not session.is_good:
        raise HTTPException(status_code=400, detail="Bad session")

    query.create_session(db, session)
    return session

@api.delete("/sessions/{day}")
def delete_session_api(db: Annotated[DBSession, Depends(get_db)],
                       day: str) -> Response:
    """Delete session by day."""
    target = date.fromisoformat(day)
    query.delete_session(db, target)
    return Response(status_code=200)

@api.delete("/tricks/{id}")
def delete_trick_api(db: Annotated[DBSession, Depends(get_db)],
                     id: int) -> Response:
    """Delete trick by ID."""
    existing = db.get(Trick, id)
    if existing is not None:
        db.delete(existing)
        db.commit()
    return Response(status_code=200)

app.include_router(api)
