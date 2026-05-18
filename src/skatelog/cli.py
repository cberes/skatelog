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

@app.command("add")
def add_cmd() -> None:
    """Interactively log a session."""
    console.print("[red]Not implemented yet[/red]")

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
