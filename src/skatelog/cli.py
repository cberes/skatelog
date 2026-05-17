from datetime import date
from pathlib import Path
from rich.console import Console
from rich.table import Table
from sqlmodel import Session as DBSession
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

@app.command("list")
def list_cmd(month: Annotated[str | None, typer.Option(help="Filter to YYYY-MM")] = None) -> None:
    console.print(f"[red]Not implemented yet: {month}[/red]")

def main() -> None:
    app()

if __name__ == "__main__":
    main()
