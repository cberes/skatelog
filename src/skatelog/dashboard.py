from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from skatelog.cli_util import date_range, streak
from skatelog.deps import get_db
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
    sessions = list(query.find_by_date_range(db, start, end))
    ctx = {
            "request": request,
            "sessions": sessions,
            "disciplines": query.find_discipline_counts(db, start, end),
            "locations": query.find_location_counts(db, start, end),
            "shoes": query.find_shoe_counts(db, start, end),
            "boards": query.find_board_counts(db, start, end),
            "steak": streak(sessions).best,
    }
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
    ctx = {
            "request": request,
            "year": year,
            "month": month,
            "sessions": sessions,
            "disciplines": query.find_discipline_counts(db, start, end),
            "locations": query.find_location_counts(db, start, end),
            "shoes": query.find_shoe_counts(db, start, end),
            "boards": query.find_board_counts(db, start, end),
            "steak": streak(sessions).best,
    }
    return _templates.TemplateResponse(request, "_dashboard_refresh.html", ctx)
