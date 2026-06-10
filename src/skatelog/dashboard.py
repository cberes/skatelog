from datetime import date, timedelta
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from skatelog.cli_util import date_range, new_tricks, streak
from skatelog.deps import get_db
from skatelog.models import Discipline
import skatelog.queries as query
from sqlmodel import Session as DBSession
from typing import Annotated, Any

router = APIRouter()
_templates = Jinja2Templates(directory="src/skatelog/templates")

@router.get("/", response_class=HTMLResponse)
def dashboard(
    request: Request,
    db: Annotated[DBSession, Depends(get_db)],
    year: str | None = None,
    month: str | None = None,
) -> Any:
    start, end = date_range(month, year)
    six_months_ago = date.today() - timedelta(days=30*6)
    last_year = date.today() - timedelta(days=365)
    most_recent_session = query.find_most_recent_session(db)
    sessions = list(query.find_by_date_range(db, start, end))
    tricks = list(query.find_tricks_by_date_range(db, start, end))
    ctx = {
            "request": request,
            "today": date.today().isoformat(),
            "sessions": sessions,
            "disciplines": [d.value for d in Discipline],
            "locations": list(query.find_locations(db, last_year)),
            "shoes": list(query.find_shoes(db, six_months_ago)),
            "boards": list(query.find_boards(db, six_months_ago)),
            "location_last": (most_recent_session and most_recent_session.where) or "",
            "shoe_last": (most_recent_session and most_recent_session.shoe) or "",
            "board_last": (most_recent_session and most_recent_session.board) or "",
            "discipline_counts": query.find_discipline_counts(db, start, end),
            "location_counts": query.find_location_counts(db, start, end),
            "shoe_counts": query.find_shoe_counts(db, start, end),
            "board_counts": query.find_board_counts(db, start, end),
            "streak": streak(sessions).best,
            "new_tricks": list(new_tricks(tricks)),
    }
    [ctx[it].sort() for it in ("locations", "shoes", "boards")]
    return _templates.TemplateResponse(request, "dashboard.html", ctx)

@router.get("/refresh", response_class=HTMLResponse)
def refresh(
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
            "sessions": sessions,
            "discipline_counts": query.find_discipline_counts(db, start, end),
            "location_counts": query.find_location_counts(db, start, end),
            "shoe_counts": query.find_shoe_counts(db, start, end),
            "board_counts": query.find_board_counts(db, start, end),
            "streak": streak(sessions).best,
            "new_tricks": list(new_tricks(tricks)),
    }
    return _templates.TemplateResponse(request, "_dashboard_refresh.html", ctx)
