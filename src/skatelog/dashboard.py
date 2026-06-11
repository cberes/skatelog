from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from skatelog.cli_util import date_range, new_tricks, streak
from skatelog.deps import get_db
from skatelog.models import Session, Discipline
import skatelog.queries as query
from sqlmodel import Session as DBSession
from typing import Annotated, Any

router = APIRouter()
_templates = Jinja2Templates(directory="src/skatelog/templates")

_six_months_ago = date.today() - timedelta(days=30*6)
_one_year_ago = date.today() - timedelta(days=365)

def _most_recent(sessions: list[Session]) -> list[Session]:
    return sorted(sessions, key=lambda it: it.day, reverse=True)[:10]

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

