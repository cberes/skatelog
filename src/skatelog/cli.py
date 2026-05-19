from collections.abc import Iterator
from datetime import date
from pathlib import Path
from rich.console import Console
from rich.table import Table
from sqlalchemy import func
from sqlmodel import Session as DBSession
from sqlmodel import select
from skatelog.cli_util import find_by_startswith, find_disciplines, date_range
from skatelog.db import get_engine
from skatelog.importer import import_csv
from skatelog.models import Discipline, Session
import skatelog.queries as query
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
    session = query.find_session(target)
    if session is None:
        console.print(f"[yellow]No session logged for {target}[/yellow]")
        raise typer.Exit(code=1)
    console.print(_session_table(session))

def _find_recent_locations() -> list[str]:
    return query.find_locations()

def _find_recent_shoes() -> list[str]:
    return query.find_shoes()

def _find_recent_boards() -> list[str]:
    return query.find_boards()

def _most_recent_location() -> str:
    session = query.find_most_recent_session()
    return (session is not None and session.where) or ""

def _most_recent_shoe() -> str:
    session = query.find_most_recent_session()
    return (session is not None and session.shoe) or ""

def _most_recent_board() -> str:
    session = query.find_most_recent_session()
    return (session is not None and session.board) or ""

def _none_if_dash(s: str | None) -> str | None:
    return None if s == "-" else s

@app.command("add")
def add_cmd(day: Annotated[str, typer.Option(prompt=True, help="Date as YYYY-MM-DD")] = str(date.today()),
            where: Annotated[str, typer.Option(prompt=True, autocompletion=_find_recent_locations)] = _most_recent_location(),
            shoe: Annotated[str, typer.Option(prompt=True, autocompletion=_find_recent_shoes)] = _most_recent_shoe(),
            board: Annotated[str, typer.Option(prompt=True, autocompletion=_find_recent_boards)] = _most_recent_board(),
            disciplines: Annotated[str | None, typer.Option(prompt=True, help="Disciplines trained as CSV")] = "-",
            notes: Annotated[str | None, typer.Option(prompt=True)] = "-") -> None:
    """Interactively log a session."""
    # The spreasdsheet has select inputs, so I can easily pick the right options
    # I'd like to do a prompt with multiple choices and an OTHER option that adds a new value
    # but IDK if I can do that. so...try to find an value from the list of existing values
    new_value = lambda value: console.print(f"[yellow]Adding new value: {value}[/yellow]")
    skipped = lambda d: console.print(f"[red]Skipping ambiguous discipline: {d}[/red]")
    session = Session(
        day=date.fromisoformat(day),
        where=find_by_startswith(where, query.find_locations(), new_value),
        shoe=find_by_startswith(shoe, query.find_shoes(), new_value),
        board=find_by_startswith(board, query.find_boards(), new_value),
        notes=_none_if_dash(notes),
        **find_disciplines(disciplines, skipped),
    )

    if not session.is_good:
        console.print("[red]Not saving incomplete session[/red]")
        raise typer.Exit(code=1)

    query.create_session(session)
    console.print(f"[green]Saved session for {session.day}[/green]")
    console.print(_session_table(session))

@app.command("delete")
def delete_cmd(day: Annotated[str, typer.Argument(help="Date as YYYY-MM-DD")]) -> None:
    target = date.fromisoformat(day)
    query.delete_session(target)

@app.command("list")
def list_cmd(month: Annotated[str | None, typer.Option(help="Filter to YYYY-MM")] = None,
             year: Annotated[str | None, typer.Option(help="Filter to YYYY")] = None) -> None:
    """List sessions."""
    table = Table(title="Sessions")
    table.add_column("Day", justify="right", style="cyan")
    table.add_column("Where", style="green")
    table.add_column("Shoe")
    table.add_column("Board")
    table.add_column("Notes")

    start, end = date_range(month, year)
    for session in query.find_by_date_range(start, end):
        table.add_row(str(session.day), session.where or "-", session.shoe or "-", session.board or "-", session.notes or "-")
    console.print(table)

@app.command("list-disciplines")
def list_disciplines_cmd(month: Annotated[str | None, typer.Option(help="Filter to YYYY-MM")] = None,
                         year: Annotated[str | None, typer.Option(help="Filter to YYYY")] = None) -> None:
    """List all disciplines."""
    table = Table(title="Disciplines")
    table.add_column("Discipline", style="cyan")
    table.add_column("Count", justify="right")
    start, end = date_range(month, year)
    counts = query.find_discipline_counts(start, end)
    for d in sorted(counts.keys()):
        table.add_row(str(d), str(counts[d]))
    console.print(table)

@app.command("list-locations")
def list_locations_cmd(month: Annotated[str | None, typer.Option(help="Filter to YYYY-MM")] = None,
                       year: Annotated[str | None, typer.Option(help="Filter to YYYY")] = None) -> None:
    """List all locations."""
    table = Table(title="Locations")
    table.add_column("Where", style="cyan")
    table.add_column("Count", justify="right")
    start, end = date_range(month, year)
    counts = query.find_location_counts(start, end)
    for loc in sorted(counts.keys()):
        table.add_row(loc, str(counts[loc]))
    console.print(table)

@app.command("list-shoes")
def list_shoes_cmd(month: Annotated[str | None, typer.Option(help="Filter to YYYY-MM")] = None,
                   year: Annotated[str | None, typer.Option(help="Filter to YYYY")] = None) -> None:
    """List all shoes."""
    table = Table(title="Shoes")
    table.add_column("Shoe", style="cyan")
    table.add_column("Count", justify="right")
    start, end = date_range(month, year)
    counts = query.find_shoe_counts(start, end)
    for shoe in sorted(counts.keys()):
        table.add_row(shoe, str(counts[shoe]))
    console.print(table)

@app.command("list-boards")
def list_boards_cmd(month: Annotated[str | None, typer.Option(help="Filter to YYYY-MM")] = None,
                    year: Annotated[str | None, typer.Option(help="Filter to YYYY")] = None) -> None:
    """List all boards."""
    table = Table(title="Boards")
    table.add_column("Board", style="cyan")
    table.add_column("Count", justify="right")
    start, end = date_range(month, year)
    counts = query.find_board_counts(start, end)
    for board in sorted(counts.keys()):
        table.add_row(board, str(counts[board]))
    console.print(table)

def main() -> None:
    app()

if __name__ == "__main__":
    main()
