from datetime import date
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from skatelog.cli_util import date_range
from skatelog.deps import get_db
import skatelog.queries as query
from sqlmodel import Session as DBSession
from typing import Annotated, Any

router = APIRouter()
_templates = Jinja2Templates(directory="src/skatelog/templates")

def _date_range(month: str | None, year: str | None) -> tuple[date, date]:
    if not year:
        args = [None, None]
    elif month:
        args = [f"{year}-{month}", None]
    else:
        args = [None, year]
    return date_range(*args)

@router.get("/", response_class=HTMLResponse)
def dashboard(
    request: Request,
    db: Annotated[DBSession, Depends(get_db)],
    year: str | None = None,
    month: str | None = None,
) -> Any:
    # TODO: does this need to get sessions?
    start, end = _date_range(month, year)
    sessions = query.find_by_date_range(db, start, end)
    return _templates.TemplateResponse(
        request, "dashboard.html", {"sessions": sessions}
    )

@router.get("/sessions.html", response_class=HTMLResponse)
def session_rows(
    request: Request,
    db: Annotated[DBSession, Depends(get_db)],
    year: str | None = None,
    month: str | None = None,
) -> Any:
    start, end = _date_range(month, year)
    sessions = query.find_by_date_range(db, start, end)
    return _templates.TemplateResponse(
        request, "_session_rows.html", {"sessions": sessions}
    )

@router.get("/disciplines.html", response_class=HTMLResponse)
def discipline_rows(
    request: Request,
    db: Annotated[DBSession, Depends(get_db)],
    year: str | None = None,
    month: str | None = None,
) -> Any:
    start, end = _date_range(month, year)
    items = query.find_discipline_counts(db, start, end)
    return _templates.TemplateResponse(
        request, "_session_aggregate_relative.html", {"items": items}
    )

@router.get("/locations.html", response_class=HTMLResponse)
def location_rows(
    request: Request,
    db: Annotated[DBSession, Depends(get_db)],
    year: str | None = None,
    month: str | None = None,
) -> Any:
    start, end = _date_range(month, year)
    items = query.find_location_counts(db, start, end)
    return _templates.TemplateResponse(
        request, "_session_aggregate.html", {"items": items}
    )

@router.get("/shoes.html", response_class=HTMLResponse)
def shoe_rows(
    request: Request,
    db: Annotated[DBSession, Depends(get_db)],
    year: str | None = None,
    month: str | None = None,
) -> Any:
    start, end = _date_range(month, year)
    items = query.find_shoe_counts(db, start, end)
    return _templates.TemplateResponse(
        request, "_session_aggregate.html", {"items": items}
    )

@router.get("/boards.html", response_class=HTMLResponse)
def board_rows(
    request: Request,
    db: Annotated[DBSession, Depends(get_db)],
    year: str | None = None,
    month: str | None = None,
) -> Any:
    start, end = _date_range(month, year)
    items = query.find_board_counts(db, start, end)
    return _templates.TemplateResponse(
        request, "_session_aggregate.html", {"items": items}
    )
