from collections.abc import Iterable
from datetime import date, timedelta
from io import BytesIO
from typing import Annotated, Any

import matplotlib
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session as DBSession

import skatelog.queries as query
from skatelog.cli_util import date_range, new_tricks, streak
from skatelog.deps import get_db
from skatelog.models import Discipline, Session
from skatelog.plots import PlotConfig, bar, line

matplotlib.use("Agg")
router = APIRouter()
_templates = Jinja2Templates(directory="src/skatelog/templates")

_six_months_ago = date.today() - timedelta(days=30 * 6)
_one_year_ago = date.today() - timedelta(days=365)


def _most_recent(sessions: list[Session]) -> list[Session]:
    return sorted(sessions, key=lambda it: it.day, reverse=True)[:10]


def _to_plot_data(results: Iterable[query.SessionAggregate]) -> list[tuple[str, int]]:
    sorted_results = sorted(list(results), key=lambda it: it.count, reverse=True)
    return [(result.key, result.count) for result in sorted_results]


@router.get("/", response_class=HTMLResponse)
def dashboard_page(
    request: Request,
    db: Annotated[DBSession, Depends(get_db)],
    year: str | None = None,
    month: str | None = None,
) -> Any:
    start, end = date_range(month, year)
    sessions = list(query.find_by_date_range(db, start, end))
    tricks = list(query.find_tricks_by_date_range(db, start, end))
    ctx = {
        "request": request,
        "sessions": _most_recent(sessions),
        "discipline_counts": query.find_discipline_counts(db, start, end),
        "location_counts": query.find_location_counts(db, start, end),
        "shoe_counts": query.find_shoe_counts(db, start, end),
        "board_counts": query.find_board_counts(db, start, end),
        "streak": streak(sessions).best,
        "new_tricks": sorted(list(new_tricks(tricks)), key=lambda it: it.day, reverse=True),
    }
    return _templates.TemplateResponse(request, "dashboard.html", ctx)


@router.get("/refresh", response_class=HTMLResponse)
def refresh_dashboard(
    request: Request,
    db: Annotated[DBSession, Depends(get_db)],
    year: str | None = None,
    month: str | None = None,
) -> Any:
    start, end = date_range(month, year)
    sessions = list(query.find_by_date_range(db, start, end))
    tricks = list(query.find_tricks_by_date_range(db, start, end))
    ctx = {
        "request": request,
        "year": year,
        "month": month,
        "sessions": _most_recent(sessions),
        "discipline_counts": query.find_discipline_counts(db, start, end),
        "location_counts": query.find_location_counts(db, start, end),
        "shoe_counts": query.find_shoe_counts(db, start, end),
        "board_counts": query.find_board_counts(db, start, end),
        "streak": streak(sessions).best,
        "new_tricks": sorted(list(new_tricks(tricks)), key=lambda it: it.day, reverse=True),
    }
    return _templates.TemplateResponse(request, "_dashboard_refresh.html", ctx)


@router.get("/sessions", response_class=HTMLResponse)
def sessions_page(
    request: Request,
    db: Annotated[DBSession, Depends(get_db)],
    year: str | None = None,
    month: str | None = None,
) -> Any:
    start, end = date_range(month, year)
    most_recent_session = query.find_most_recent_session(db)
    sessions = list(query.find_by_date_range(db, start, end))
    ctx = {
        "request": request,
        "today": date.today().isoformat(),
        "sessions": sorted(sessions, key=lambda it: it.day, reverse=True),
        "disciplines": [d.value for d in Discipline],
        "locations": list(query.find_locations(db, _one_year_ago)),
        "shoes": list(query.find_shoes(db, _six_months_ago)),
        "boards": list(query.find_boards(db, _six_months_ago)),
        "location_last": (most_recent_session and most_recent_session.where) or "",
        "shoe_last": (most_recent_session and most_recent_session.shoe) or "",
        "board_last": (most_recent_session and most_recent_session.board) or "",
    }
    [ctx[it].sort() for it in ("locations", "shoes", "boards")]
    return _templates.TemplateResponse(request, "sessions.html", ctx)


@router.get("/refresh-sessions", response_class=HTMLResponse)
def refresh_sessions(
    request: Request,
    db: Annotated[DBSession, Depends(get_db)],
    year: str | None = None,
    month: str | None = None,
) -> Any:
    start, end = date_range(month, year)
    sessions = list(query.find_by_date_range(db, start, end))
    ctx = {
        "request": request,
        "sessions": sorted(sessions, key=lambda it: it.day, reverse=True),
    }
    return _templates.TemplateResponse(request, "_session_rows.html", ctx)


@router.get("/tricks", response_class=HTMLResponse)
def tricks_page(
    request: Request,
    db: Annotated[DBSession, Depends(get_db)],
    year: str | None = None,
    month: str | None = None,
) -> Any:
    start, end = date_range(month, year)
    tricks = query.find_tricks_by_date_range(db, start, end)
    ctx = {
        "request": request,
        "tricks": sorted(list(tricks), key=lambda it: it.day, reverse=True),
    }
    return _templates.TemplateResponse(request, "tricks.html", ctx)


@router.get("/refresh-tricks", response_class=HTMLResponse)
def refresh_tricks(
    request: Request,
    db: Annotated[DBSession, Depends(get_db)],
    year: str | None = None,
    month: str | None = None,
) -> Any:
    start, end = date_range(month, year)
    tricks = query.find_tricks_by_date_range(db, start, end)
    ctx = {
        "request": request,
        "tricks": sorted(list(tricks), key=lambda it: it.day, reverse=True),
    }
    return _templates.TemplateResponse(request, "_trick_rows.html", ctx)


@router.get("/sessions/{day}", response_class=HTMLResponse)
def session_page(
    request: Request,
    db: Annotated[DBSession, Depends(get_db)],
    day: str,
) -> Any:
    target = date.fromisoformat(day)
    session = query.find_session(db, target)
    if session is None:
        raise HTTPException(status_code=404, detail=f"No session for {day}")
    tricks = list(session.tricks)
    ctx = {
        "request": request,
        "session": session,
        "tricks": tricks,
        "disciplines": [d.value for d in Discipline],
    }
    return _templates.TemplateResponse(request, "session.html", ctx)


@router.get("/disciplines.png", response_class=Response)
def plot_disciplines(
    db: Annotated[DBSession, Depends(get_db)],
    month: int | str | None = None,
    year: int | str | None = None,
) -> Response:
    """Generates plot for discipline training frequency."""
    start, end = date_range(month, year)
    result = query.find_discipline_counts(db, start, end)
    buf = BytesIO()
    config = PlotConfig(
        title="Discipline training frequency",
        label_x="Discipline",
        label_y="Sessions (days)",
        buf=buf,
    )
    bar([d for d in _to_plot_data(result) if d[1] != 0], config)
    return Response(content=buf.getvalue(), media_type="image/png")


@router.get("/locations.png", response_class=Response)
def plot_locations(
    db: Annotated[DBSession, Depends(get_db)],
    month: int | str | None = None,
    year: int | str | None = None,
) -> Response:
    """Generates plot for location frequency."""
    start, end = date_range(month, year)
    result = query.find_location_counts(db, start, end)
    buf = BytesIO()
    config = PlotConfig(
        title="Location frequency", label_x="Location", label_y="Sessions (days)", buf=buf
    )
    bar(_to_plot_data(result), config)
    return Response(content=buf.getvalue(), media_type="image/png")


@router.get("/shoes.png", response_class=Response)
def plot_shoes(
    db: Annotated[DBSession, Depends(get_db)],
    month: int | str | None = None,
    year: int | str | None = None,
) -> Response:
    """Generates plot for shoe usage."""
    start, end = date_range(month, year)
    result = query.find_shoe_counts(db, start, end)
    buf = BytesIO()
    config = PlotConfig(title="Shoe frequency", label_x="Shoe", label_y="Sessions (days)", buf=buf)
    bar(_to_plot_data(result), config)
    return Response(content=buf.getvalue(), media_type="image/png")


@router.get("/boards.png", response_class=Response)
def plot_boards(
    db: Annotated[DBSession, Depends(get_db)],
    month: int | str | None = None,
    year: int | str | None = None,
) -> Response:
    """Generates plot for board usage."""
    start, end = date_range(month, year)
    result = query.find_board_counts(db, start, end)
    buf = BytesIO()
    config = PlotConfig(
        title="Board frequency", label_x="Board", label_y="Sessions (days)", buf=buf
    )
    bar(_to_plot_data(result), config)
    return Response(content=buf.getvalue(), media_type="image/png")


@router.get("/streak.png", response_class=Response)
def plot_streak(
    db: Annotated[DBSession, Depends(get_db)],
    month: int | str | None = None,
    year: int | str | None = None,
) -> Response:
    """Generates plot for current streak by day."""
    start, end = date_range(month, year)
    sessions = query.find_by_date_range(db, start, end)
    result = streak(sessions)
    buf = BytesIO()
    config = PlotConfig(title="Streak by day", label_x="Day", label_y="Streak (days)", buf=buf)
    line(result.to_plot_data(), config)
    return Response(content=buf.getvalue(), media_type="image/png")
