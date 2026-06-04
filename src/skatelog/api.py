from collections.abc import Iterable
from datetime import date
from fastapi import FastAPI, Response
from io import BytesIO
import matplotlib
from sqlmodel import Session as DBSession
from skatelog.cli_util import date_range, new_tricks, streak, Streak
from skatelog.db import get_engine
from skatelog.models import Session, Trick
from skatelog.plots import bar, line, PlotConfig
import skatelog.queries as query
from skatelog.queries import SessionAggregate

matplotlib.use("Agg")
app = FastAPI()

def to_plot_data(results: Iterable[SessionAggregate]) -> list[tuple[str, int]]:
    sorted_results = sorted(list(results), key=lambda it: it.count, reverse=True)
    return [(result.key, result.count) for result in sorted_results]

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

@app.get("/disciplines.png", response_class=Response)
def plot_disciplines_cmd(
    month: str | None = None,
    year: str | None = None,
) -> Response:
    """Generates plot for discipline training frequency."""
    result = list_disciplines_cmd(month, year)
    buf = BytesIO()
    config = PlotConfig(title="Discipline training frequency", label_x="Discipline", label_y="Sessions (days)", buf=buf)
    bar([d for d in to_plot_data(result) if d[1] != 0], config)
    return Response(content=buf.getvalue(), media_type="image/png")

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

@app.get("/locations.png", response_class=Response)
def plot_locations_cmd(
    month: str | None = None,
    year: str | None = None,
) -> Response:
    """Generates plot for location frequency."""
    result = list_locations_cmd(month, year)
    buf = BytesIO()
    config = PlotConfig(title="Location frequency", label_x="Location", label_y="Sessions (days)", buf=buf)
    bar(to_plot_data(result), config)
    return Response(content=buf.getvalue(), media_type="image/png")

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

@app.get("/shoes.png", response_class=Response)
def plot_shoes_cmd(
    month: str | None = None,
    year: str | None = None,
) -> Response:
    """Generates plot for shoe usage."""
    result = list_shoes_cmd(month, year)
    buf = BytesIO()
    config = PlotConfig(title="Shoe frequency", label_x="Shoe", label_y="Sessions (days)", buf=buf)
    bar(to_plot_data(result), config)
    return Response(content=buf.getvalue(), media_type="image/png")

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

@app.get("/boards.png", response_class=Response)
def plot_boards_cmd(
    month: str | None = None,
    year: str | None = None,
) -> Response:
    """Generates plot for board usage."""
    result = list_boards_cmd(month, year)
    buf = BytesIO()
    config = PlotConfig(title="Board frequency", label_x="Board", label_y="Sessions (days)", buf=buf)
    bar(to_plot_data(result), config)
    return Response(content=buf.getvalue(), media_type="image/png")

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

@app.get("/streak.png", response_class=Response)
def plot_streak_cmd(
    month: str | None = None,
    year: str | None = None,
) -> Response:
    """Generates plot for current streak by day."""
    streak_result = streak_cmd(month, year)
    buf = BytesIO()
    config = PlotConfig(title="Streak by day", label_x="Day", label_y="Streak (days)", buf=buf)
    line(streak_result.to_plot_data(), config)
    return Response(content=buf.getvalue(), media_type="image/png")

