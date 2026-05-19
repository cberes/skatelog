from collections.abc import Iterator
from datetime import date
from pathlib import Path
from rich.console import Console
from rich.table import Table
from sqlalchemy import func
from sqlmodel import Session as DBSession
from sqlmodel import select
from skatelog.db import get_engine
from skatelog.importer import import_csv
from skatelog.models import Discipline, Session
import typer
from typing import Annotated

DISCIPLINE_ATTRS = [
    "a_frame",
    "bank",
    "bowl",
    "box",
    "flat",
    "free",
    "hip",
    "manual",
    "rail",
    "slappy",
    "transition",
    "vert",
]

app = typer.Typer(help="Skateboarding session log.")
console = Console()

@app.command("import")
def import_cmd(csv_path: Annotated[Path, typer.Argument(exists=True, readable=True)]) -> None:
    """Imports sessions from a CSV file."""
    engine = get_engine()
    with DBSession(engine) as db:
        n = import_csv(csv_path, db)
    console.print(f"[green]Imported {n} sessions[/green]")

def _session_table(session: Session) -> Table:
    table = Table(title=str(session.day), show_header=False)
    disciplines = ", ".join(sorted(d.value for d in session.disciplines)) or "-"
    table.add_row("Disciplines", disciplines)
    table.add_row("Where", session.where or "-")
    table.add_row("Shoe", session.shoe or "-")
    table.add_row("Board", session.board or "-")
    table.add_row("Notes", session.notes or "-")
    return table

@app.command("show")
def show_cmd(day: Annotated[str, typer.Argument(help="Date as YYYY-MM-DD")]) -> None:
    """Show a day's session."""
    target = date.fromisoformat(day)
    engine = get_engine()
    with DBSession(engine) as db:
        session = db.get(Session, target)
    if session is None:
        console.print(f"[yellow]No session logged for {target}[/yellow]")
        raise typer.Exit(code=1)

    console.print(_session_table(session))

# TODO what's the type of col?
def _find_values(col, start: date | None) -> dict[str, int]:
    engine = get_engine()
    with DBSession(engine) as db:
        statement = select(col, func.count(Session.day)) \
            .where(Session.day >= (start or date.min)) \
            .group_by(col)
        return {str(x[0]): x[1] for x in db.exec(statement) if x[0] is not None}

def _find_location_counts(start: date | None = None) -> dict[str, int]:
    return _find_values(Session.where, start)

def _find_shoe_counts(start: date | None = None) -> dict[str, int]:
    return _find_values(Session.shoe, start)

def _find_board_counts(start: date | None = None) -> dict[str, int]:
    return _find_values(Session.board, start)

def _find_locations(start: date | None = None) -> list[str]:
    return list(_find_location_counts(start).keys())

def _find_shoes(start: date | None = None) -> list[str]:
    return list(_find_shoe_counts(start).keys())

def _find_boards(start: date | None = None) -> list[str]:
    return list(_find_board_counts(start).keys())

def _find_recent_locations() -> list[str]:
    return _find_locations()

def _find_recent_shoes() -> list[str]:
    return _find_shoes()

def _find_recent_boards() -> list[str]:
    return _find_boards()

def _delete_by_day(db: DBSession, day: date) -> None:
    existing = db.get(Session, day)
    if existing is not None:
        db.delete(existing)
        db.flush()

def _none_if_dash(s: str | None) -> str | None:
    return None if s == "-" else s

def _find_most_recent_session() -> Session | None:
    engine = get_engine()
    with DBSession(engine) as db:
        statement = select(Session) \
            .where(Session.where is not None, Session.shoe is not None, Session.board is not None) \
            .order_by(Session.day.desc()) \
            .limit(1)
        return db.exec(statement).first()

def _most_recent_location() -> str:
    session = _find_most_recent_session()
    return (session is not None and session.where) or ""

def _most_recent_shoe() -> str:
    session = _find_most_recent_session()
    return (session is not None and session.shoe) or ""

def _most_recent_board() -> str:
    session = _find_most_recent_session()
    return (session is not None and session.board) or ""

# The spreasdsheet has select inputs, so I can easily pick the right options
# I'd like to do a prompt with multiple choices and an OTHER option that adds a new value
# but IDK if I can do that. so...try to find an value from the list of existing values
def _find_by_startswith(value: str, options: list[str]) -> str | None:
    if (value or "-") == "-":
        return None
    try:
        return next(o for o in options if o.lower().startswith(value.lower()))
    except StopIteration:
        console.print(f"[yellow]Adding new value: {value}[/yellow]")
        return value

def _find_disciplines(disciplines: str | None) -> dict[str, bool]:
    discipline_flags = {}
    for d in (disciplines or "").split(","):
        matches = {attr: True for attr in DISCIPLINE_ATTRS if attr.lower().startswith(d.strip().lower())}
        if len(matches) == 1:
            discipline_flags.update(matches)
        elif len(matches) > 1:
            console.print(f"[red]Skipping ambiguous discipline: {d}[/red]")
    return discipline_flags

@app.command("add")
def add_cmd(day: Annotated[str, typer.Option(prompt=True, help="Date as YYYY-MM-DD")] = str(date.today()),
            where: Annotated[str, typer.Option(prompt=True, autocompletion=_find_recent_locations)] = _most_recent_location(),
            shoe: Annotated[str, typer.Option(prompt=True, autocompletion=_find_recent_shoes)] = _most_recent_shoe(),
            board: Annotated[str, typer.Option(prompt=True, autocompletion=_find_recent_boards)] = _most_recent_board(),
            disciplines: Annotated[str | None, typer.Option(prompt=True, help="Disciplines trained as CSV")] = "-",
            notes: Annotated[str | None, typer.Option(prompt=True)] = "-") -> None:
    """Interactively log a session."""
    session = Session(
        day=date.fromisoformat(day),
        where=_find_by_startswith(where, _find_locations()),
        shoe=_find_by_startswith(shoe, _find_shoes()),
        board=_find_by_startswith(board, _find_boards()),
        notes=_none_if_dash(notes),
        **_find_disciplines(disciplines),
    )

    if not session.is_good:
        console.print("[red]Not saving incomplete session[/red]")
        raise typer.Exit(code=1)

    engine = get_engine()
    with DBSession(engine) as db:
        _delete_by_day(db, session.day)
        db.add(session)
        db.commit()
        console.print(f"[green]Saved session for {session.day}[/green]")
        console.print(_session_table(session))

@app.command("delete")
def delete_cmd(day: Annotated[str, typer.Argument(help="Date as YYYY-MM-DD")]) -> None:
    target = date.fromisoformat(day)
    engine = get_engine()
    with DBSession(engine) as db:
        _delete_by_day(db, target)
        db.commit()

def _month_range(month: str) -> tuple[date, date]:
    start = date.strptime(month, "%Y-%m")
    next_year = start.year + (start.month // 12)
    next_month = (start.month % 12) + 1
    end = date(next_year, next_month, start.day)
    return (start, end)

def _year_range(year: str) -> tuple[date, date]:
    start = date.strptime(year, "%Y")
    end = date(start.year + 1, start.month, start.day)
    return (start, end)

def _find_by_date_range(start: date, end: date) -> Iterator[Session]:
    engine = get_engine()
    with DBSession(engine) as db:
        statement = select(Session).where(Session.day >= start, Session.day < end)
        sessions = db.exec(statement)
        for session in sessions:
            yield session

@app.command("list")
def list_cmd(month: Annotated[str | None, typer.Option(help="Filter to YYYY-MM")] = None,
             year: Annotated[str | None, typer.Option(help="Filter to YYYY")] = None) -> None:
    """List sessions."""
    if month is not None:
        start, end = _month_range(month)
    elif year is not None:
        start, end = _year_range(year)
    else:
        start, end = (date.min, date.max)

    table = Table(title="Sessions")
    table.add_column("Day", justify="right", style="cyan")
    table.add_column("Where", style="green")
    table.add_column("Shoe")
    table.add_column("Board")
    table.add_column("Notes")

    for session in _find_by_date_range(start, end):
        table.add_row(str(session.day), session.where or "-", session.shoe or "-", session.board or "-", session.notes or "-")
    console.print(table)

def _find_discipline_counts(start: date | None = None) -> dict[Discipline, int]:
    counts = {d: 0 for d in Discipline}
    for session in _find_by_date_range(start or date.min, date.max):
        for d in session.disciplines:
            counts[d] += 1
    return counts

@app.command("list-disciplines")
def list_disciplines_cmd() -> None:
    """List all disciplines."""
    table = Table(title="Disciplines")
    table.add_column("Discipline", style="cyan")
    table.add_column("Count", justify="right")
    counts = _find_discipline_counts()
    for d in sorted(counts.keys()):
        table.add_row(str(d), str(counts[d]))
    console.print(table)

@app.command("list-locations")
def list_locations_cmd() -> None:
    """List all locations."""
    table = Table(title="Locations")
    table.add_column("Where", style="cyan")
    table.add_column("Count", justify="right")
    counts = _find_location_counts()
    for loc in sorted(counts.keys()):
        table.add_row(loc, str(counts[loc]))
    console.print(table)

@app.command("list-shoes")
def list_shoes_cmd() -> None:
    """List all shoes."""
    table = Table(title="Shoes")
    table.add_column("Shoe", style="cyan")
    table.add_column("Count", justify="right")
    counts = _find_shoe_counts()
    for shoe in sorted(counts.keys()):
        table.add_row(shoe, str(counts[shoe]))
    console.print(table)

@app.command("list-boards")
def list_boards_cmd() -> None:
    """List all boards."""
    table = Table(title="Boards")
    table.add_column("Board", style="cyan")
    table.add_column("Count", justify="right")
    counts = _find_board_counts()
    for board in sorted(counts.keys()):
        table.add_row(board, str(counts[board]))
    console.print(table)

def main() -> None:
    app()

if __name__ == "__main__":
    main()
