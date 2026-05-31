from datetime import date
from pathlib import Path
from rich.console import Console
from rich.table import Table
from sqlmodel import Session as DBSession
from skatelog.cli_util import find_by_startswith, find_disciplines, date_range
from skatelog.db import get_engine
from skatelog.exporter import export_csv
from skatelog.importer import import_csv
from skatelog.models import Session
import skatelog.queries as query
import typer
from typing import Annotated

app = typer.Typer(help="Skateboarding session log.")
console = Console()

@app.command("import")
def import_cmd(csv_path: Annotated[Path, typer.Argument(exists=True, readable=True, dir_okay=False)]) -> None:
    """Imports sessions from a CSV file."""
    with DBSession(get_engine()) as db:
        n = import_csv(csv_path, db)
    console.print(f"[green]Imported {n} sessions[/green]")

@app.command("export")
def export_cmd(csv_path: Annotated[Path, typer.Argument(writable=True, dir_okay=False)]) -> None:
    """Exports sessions to a CSV file."""
    with DBSession(get_engine()) as db:
        n = export_csv(csv_path, db)
    console.print(f"[green]Exported {n} sessions[/green]")

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
    with DBSession(get_engine()) as db:
        session = query.find_session(db, target)
        if session is None:
            console.print(f"[yellow]No session logged for {target}[/yellow]")
            raise typer.Exit(code=1)
        console.print(_session_table(session))

def _find_recent_locations() -> set[str]:
    with DBSession(get_engine()) as db:
        return query.find_locations(db)

def _find_recent_shoes() -> set[str]:
    with DBSession(get_engine()) as db:
        return query.find_shoes(db)

def _find_recent_boards() -> set[str]:
    with DBSession(get_engine()) as db:
        return query.find_boards(db)

def _most_recent_location() -> str:
    with DBSession(get_engine()) as db:
        session = query.find_most_recent_session(db)
        return (session is not None and session.where) or ""

def _most_recent_shoe() -> str:
    with DBSession(get_engine()) as db:
        session = query.find_most_recent_session(db)
        return (session is not None and session.shoe) or ""

def _most_recent_board() -> str:
    with DBSession(get_engine()) as db:
        session = query.find_most_recent_session(db)
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
    disc_result = find_disciplines(disciplines)
    with DBSession(get_engine()) as db:
        where_result = find_by_startswith(where, query.find_locations(db))
        shoe_result = find_by_startswith(shoe, query.find_shoes(db))
        board_result = find_by_startswith(board, query.find_boards(db))
    for category, result in (("location", where_result), ("shoe", shoe_result), ("board", board_result)):
        if result.new:
            console.print(f"[yellow]Adding new {category}: {result.found}[/yellow]")
    for k, values in [("ambiguous", disc_result.ambiguous), ("unknown", disc_result.unknown)]:
        for v in values:
            console.print(f"[red]Skipping {k} discipline: {v}[/red]")
    session = Session(
        day=date.fromisoformat(day),
        where=where_result.found,
        shoe=shoe_result.found,
        board=board_result.found,
        notes=_none_if_dash(notes),
        tricks=[],
        **disc_result.found,
    )
    session.parse_tricks()

    if not session.is_good:
        console.print("[red]Not saving incomplete session[/red]")
        raise typer.Exit(code=1)

    with DBSession(get_engine()) as db:
        query.create_session(db, session)
        console.print(f"[green]Saving session for {session.day}[/green]")
        console.print(_session_table(session))

@app.command("delete")
def delete_cmd(day: Annotated[str, typer.Argument(help="Date as YYYY-MM-DD")]) -> None:
    target = date.fromisoformat(day)
    with DBSession(get_engine()) as db:
        query.delete_session(db, target)

@app.command("list")
def list_cmd(month: Annotated[str | None, typer.Option(help="Filter to YYYY-MM")] = None,
             year: Annotated[str | None, typer.Option(help="Filter to YYYY")] = None) -> None:
    """List sessions."""
    table = Table(title="Sessions")
    table.add_column("Day", justify="right", style="cyan")
    table.add_column("Where", style="green")
    table.add_column("Shoe")
    table.add_column("Board")
    table.add_column("Tricks", justify="right")
    table.add_column("Notes")

    start, end = date_range(month, year)
    with DBSession(get_engine()) as db:
        for session in query.find_by_date_range(db, start, end):
            table.add_row(str(session.day), session.where or "-", session.shoe or "-", session.board or "-", str(session.trick_count), session.notes or "-")
    console.print(table)

@app.command("list-disciplines")
def list_disciplines_cmd(month: Annotated[str | None, typer.Option(help="Filter to YYYY-MM")] = None,
                         year: Annotated[str | None, typer.Option(help="Filter to YYYY")] = None) -> None:
    """List all disciplines."""
    table = Table(title="Disciplines")
    table.add_column("Discipline", style="cyan")
    table.add_column("Count", justify="right")
    table.add_column("Last trained", justify="right")
    start, end = date_range(month, year)
    with DBSession(get_engine()) as db:
        aggs = query.find_discipline_counts(db, start, end)
    for row in sorted(aggs, key=lambda it: it.key):
        match row.days_since:
            case None:
                last_trained = "Never"
            case 1:
                last_trained = "1 day  ago"
            case it:
                last_trained = f"{it} days ago"
        table.add_row(row.key, str(row.count), last_trained)
    console.print(table)

@app.command("list-locations")
def list_locations_cmd(month: Annotated[str | None, typer.Option(help="Filter to YYYY-MM")] = None,
                       year: Annotated[str | None, typer.Option(help="Filter to YYYY")] = None) -> None:
    """List all locations."""
    table = Table(title="Locations")
    table.add_column("Where", style="cyan")
    table.add_column("Count", justify="right")
    table.add_column("Start", justify="right")
    table.add_column("End", justify="right")
    start, end = date_range(month, year)
    with DBSession(get_engine()) as db:
        aggs = query.find_location_counts(db, start, end)
    for row in sorted(aggs, key=lambda it: it.count, reverse=True):
        table.add_row(row.key, str(row.count), row.start.isoformat(), row.end.isoformat())
    console.print(table)

@app.command("list-shoes")
def list_shoes_cmd(month: Annotated[str | None, typer.Option(help="Filter to YYYY-MM")] = None,
                   year: Annotated[str | None, typer.Option(help="Filter to YYYY")] = None) -> None:
    """List all shoes."""
    table = Table(title="Shoes")
    table.add_column("Shoe", style="cyan")
    table.add_column("Count", justify="right")
    table.add_column("Start", justify="right")
    table.add_column("End", justify="right")
    start, end = date_range(month, year)
    with DBSession(get_engine()) as db:
        aggs = query.find_shoe_counts(db, start, end)
    for row in sorted(aggs, key=lambda it: it.count, reverse=True):
        table.add_row(row.key, str(row.count), row.start.isoformat(), row.end.isoformat())
    console.print(table)

@app.command("list-boards")
def list_boards_cmd(month: Annotated[str | None, typer.Option(help="Filter to YYYY-MM")] = None,
                    year: Annotated[str | None, typer.Option(help="Filter to YYYY")] = None) -> None:
    """List all boards."""
    table = Table(title="Boards")
    table.add_column("Board", style="cyan")
    table.add_column("Count", justify="right")
    table.add_column("Start", justify="right")
    table.add_column("End", justify="right")
    start, end = date_range(month, year)
    with DBSession(get_engine()) as db:
        aggs = query.find_board_counts(db, start, end)
    for row in sorted(aggs, key=lambda it: it.count, reverse=True):
        table.add_row(row.key, str(row.count), row.start.isoformat(), row.end.isoformat())
    console.print(table)

def main() -> None:
    app()

if __name__ == "__main__":
    main()
