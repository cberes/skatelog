from collections.abc import Iterator
from datetime import date
from pathlib import Path
from rich.console import Console
from rich.table import Table
from sqlmodel import Session as DBSession
from sqlmodel import select
from skatelog.db import get_engine
from skatelog.importer import import_csv
from skatelog.models import Session
import typer
from typing import Annotated

DISCIPLINE_ATTRS = [
    "a_frame",
    "bank",
    "bowl",
    "box",
    "flat",
    "hip",
    "manual",
    "rail",
    "slappy",
    "transition",
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

    table = Table(title=str(session.day), show_header=False)
    disciplines = ", ".join(sorted(d.value for d in session.disciplines)) or "-"
    table.add_row("Disciplines", disciplines)
    table.add_row("Where", session.where or "-")
    table.add_row("Shoe", session.shoe or "-")
    table.add_row("Board", session.board or "-")
    table.add_row("Notes", session.notes or "-")
    console.print(table)

# TODO what's the type of col?
def _find_values(col, start: date | None) -> list[str]:
    engine = get_engine()
    with DBSession(engine) as db:
        statement = select(col).distinct().where(Session.day >= (start or date.min))
        return list(x for x in db.exec(statement) if x is not None)

def _find_locations(start: date | None = None) -> list[str]:
    return _find_values(Session.where, start)

def _find_shoes(start: date | None = None) -> list[str]:
    return _find_values(Session.shoe, start)

def _find_boards(start: date | None = None) -> list[str]:
    return _find_values(Session.board, start)

def _delete_by_day(db: DBSession, day: date) -> None:
    existing = db.get(Session, day)
    if existing is not None:
        db.delete(existing)
        db.flush()

def _none_if_dash(s: str | None) -> str | None:
    return None if s == "-" else s

@app.command("add")
def add_cmd(where: Annotated[str, typer.Option(prompt=True)],
            shoe: Annotated[str, typer.Option(prompt=True)],
            board: Annotated[str, typer.Option(prompt=True)],
            day: Annotated[str, typer.Argument(help="Date as YYYY-MM-DD")] = str(date.today()),
            notes: Annotated[str | None, typer.Option(prompt=True)] = None,
            disciplines: Annotated[list[str] | None, typer.Option("--discipline", "-d", help="Disciplines trained")] = None) -> None:
    """Interactively log a session."""
    # The spreasdsheet has select inputs, so I can easily pick the right options
    # I'd like to do a prompt with multiple choices and an OTHER option that adds a new value
    # but IDK if I can do that. so...try to find an value from the list of existing values
    locations = sorted(_find_locations())
    shoes = sorted(_find_shoes())
    boards = sorted(_find_boards())

    selected_attrs = [attr for attr in DISCIPLINE_ATTRS if sum(1 for d in (disciplines or []) if d.startswith(attr.lower())) == 1]
    discipline_flags = {attr: True for attr in selected_attrs}

    session = Session(
        day=date.fromisoformat(day),
        where=next(loc for loc in locations if loc.lower().startswith(where.lower())) or _none_if_dash(where),
        shoe=next(s for s in shoes if s.lower().startswith(shoe.lower())) or _none_if_dash(shoe),
        board=next(b for b in boards if b.lower().startswith(board.lower())) or _none_if_dash(board),
        notes=_none_if_dash(notes),
        **discipline_flags,
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

    engine = get_engine()
    with DBSession(engine) as db:
        statement = select(Session).where(Session.day >= start, Session.day < end)
        sessions = db.exec(statement)
        for session in sessions:
            table.add_row(str(session.day), session.where or "-", session.shoe or "-", session.board or "-", session.notes or "-")
    console.print(table)

def main() -> None:
    app()

if __name__ == "__main__":
    main()
