from collections.abc import Iterable
from datetime import date
from fastapi import Depends, FastAPI, HTTPException, Response
from io import BytesIO
import matplotlib
from sqlmodel import Session as DBSession
from skatelog.cli_util import date_range, new_tricks, streak, Streak
from skatelog.dashboard import router as dashboard_router
from skatelog.deps import get_db
from skatelog.models import Session, Trick
from skatelog.plots import bar, line, PlotConfig
import skatelog.queries as query
from skatelog.queries import SessionAggregate
from typing import Annotated

matplotlib.use("Agg")
app = FastAPI()
app.include_router(dashboard_router)

def _to_plot_data(results: Iterable[SessionAggregate]) -> list[tuple[str, int]]:
    sorted_results = sorted(list(results), key=lambda it: it.count, reverse=True)
    return [(result.key, result.count) for result in sorted_results]

@app.get("/sessions/{day}")
def show_api(db: Annotated[DBSession, Depends(get_db)],
             day: str) -> Session | None:
    """Show a day's session."""
    target = date.fromisoformat(day)
    session = query.find_session(db, target)
    if session is None:
        raise HTTPException(status_code=404, detail=f"No session for {day}")
    return session

@app.get("/sessions/{day}/tricks")
def show_tricks_api(db: Annotated[DBSession, Depends(get_db)],
                    day: str) -> list[Trick]:
    """Show a day's session."""
    target = date.fromisoformat(day)
    session = query.find_session(db, target)
    if session is None:
        raise HTTPException(status_code=404, detail=f"No session for {day}")
    return session.tricks

@app.get("/sessions")
def list_api(db: Annotated[DBSession, Depends(get_db)],
             month: int | str | None = None,
             year: int | str | None = None) -> list[Session]:
    """List sessions."""
    start, end = date_range(month, year)
    sessions = query.find_by_date_range(db, start, end)
    return list(sessions)

@app.get("/tricks")
def list_tricks_api(db: Annotated[DBSession, Depends(get_db)],
                    month: int | str | None = None,
                    year: int | str | None = None,
                    new: bool = False) -> list[Trick]:
    """List tricks."""
    start, end = date_range(month, year)
    tricks = query.find_tricks_by_date_range(db, start, end)
    tricks = new_tricks(tricks) if new else tricks
    return list(tricks)

@app.get("/disciplines")
def list_disciplines_api(
    db: Annotated[DBSession, Depends(get_db)],
    month: int | str | None = None,
    year: int | str | None = None,
) -> list[SessionAggregate]:
    """List all disciplines."""
    start, end = date_range(month, year)
    aggs = query.find_discipline_counts(db, start, end)
    return list(sorted(aggs, key=lambda it: it.key))

@app.get("/disciplines.png", response_class=Response)
def plot_disciplines_api(
    db: Annotated[DBSession, Depends(get_db)],
    month: int | str | None = None,
    year: int | str | None = None,
) -> Response:
    """Generates plot for discipline training frequency."""
    result = list_disciplines_api(db, month, year)
    buf = BytesIO()
    config = PlotConfig(title="Discipline training frequency", label_x="Discipline", label_y="Sessions (days)", buf=buf)
    bar([d for d in _to_plot_data(result) if d[1] != 0], config)
    return Response(content=buf.getvalue(), media_type="image/png")

@app.get("/locations")
def list_locations_api(
    db: Annotated[DBSession, Depends(get_db)],
    month: int | str | None = None,
    year: int | str | None = None,
) -> list[SessionAggregate]:
    """List all locations."""
    start, end = date_range(month, year)
    aggs = query.find_location_counts(db, start, end)
    return list(sorted(aggs, key=lambda it: it.count, reverse=True))

@app.get("/locations.png", response_class=Response)
def plot_locations_api(
    db: Annotated[DBSession, Depends(get_db)],
    month: int | str | None = None,
    year: int | str | None = None,
) -> Response:
    """Generates plot for location frequency."""
    result = list_locations_api(db, month, year)
    buf = BytesIO()
    config = PlotConfig(title="Location frequency", label_x="Location", label_y="Sessions (days)", buf=buf)
    bar(_to_plot_data(result), config)
    return Response(content=buf.getvalue(), media_type="image/png")

@app.get("/shoes")
def list_shoes_api(
    db: Annotated[DBSession, Depends(get_db)],
    month: int | str | None = None,
    year: int | str | None = None,
) -> list[SessionAggregate]:
    """List all shoes."""
    start, end = date_range(month, year)
    aggs = query.find_shoe_counts(db, start, end)
    return list(sorted(aggs, key=lambda it: it.count, reverse=True))

@app.get("/shoes.png", response_class=Response)
def plot_shoes_api(
    db: Annotated[DBSession, Depends(get_db)],
    month: int | str | None = None,
    year: int | str | None = None,
) -> Response:
    """Generates plot for shoe usage."""
    result = list_shoes_api(db, month, year)
    buf = BytesIO()
    config = PlotConfig(title="Shoe frequency", label_x="Shoe", label_y="Sessions (days)", buf=buf)
    bar(_to_plot_data(result), config)
    return Response(content=buf.getvalue(), media_type="image/png")

@app.get("/boards")
def list_boards_api(
    db: Annotated[DBSession, Depends(get_db)],
    month: int | str | None = None,
    year: int | str | None = None,
) -> list[SessionAggregate]:
    """List all boards."""
    start, end = date_range(month, year)
    aggs = query.find_board_counts(db, start, end)
    return list(sorted(aggs, key=lambda it: it.count, reverse=True))

@app.get("/boards.png", response_class=Response)
def plot_boards_api(
    db: Annotated[DBSession, Depends(get_db)],
    month: int | str | None = None,
    year: int | str | None = None,
) -> Response:
    """Generates plot for board usage."""
    result = list_boards_api(db, month, year)
    buf = BytesIO()
    config = PlotConfig(title="Board frequency", label_x="Board", label_y="Sessions (days)", buf=buf)
    bar(_to_plot_data(result), config)
    return Response(content=buf.getvalue(), media_type="image/png")

@app.get("/streak")
def streak_api(
    db: Annotated[DBSession, Depends(get_db)],
    month: int | str | None = None,
    year: int | str | None = None,
) -> Streak:
    """Finds best streak and lists current streak by day."""
    start, end = date_range(month, year)
    sessions = query.find_by_date_range(db, start, end)
    return streak(sessions)

@app.get("/streak.png", response_class=Response)
def plot_streak_api(
    db: Annotated[DBSession, Depends(get_db)],
    month: int | str | None = None,
    year: int | str | None = None,
) -> Response:
    """Generates plot for current streak by day."""
    streak_result = streak_api(db, month, year)
    buf = BytesIO()
    config = PlotConfig(title="Streak by day", label_x="Day", label_y="Streak (days)", buf=buf)
    line(streak_result.to_plot_data(), config)
    return Response(content=buf.getvalue(), media_type="image/png")

@app.post("/sessions", status_code=201)
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

@app.delete("/sessions/{day}")
def delete_session_api(db: Annotated[DBSession, Depends(get_db)],
                       day: str) -> Response:
    """Delete session by day."""
    target = date.fromisoformat(day)
    query.delete_session(db, target)
    return Response(status_code=200)

@app.delete("/tricks/{id}")
def delete_trick_api(db: Annotated[DBSession, Depends(get_db)],
                     id: int) -> Response:
    """Delete trick by ID."""
    existing = db.get(Trick, id)
    if existing is not None:
        db.delete(existing)
        db.commit()
    return Response(status_code=200)

