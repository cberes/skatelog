import sys
from pathlib import Path
from rich.console import Console
from sqlmodel import Session as DBSession
from skatelog.db import get_engine
from skatelog.importer import import_csv

console = Console()

def main() -> None:
    engine = get_engine()
    with DBSession(engine) as db:
        n = import_csv(Path(sys.argv[1]), db)
    console.print(f"[green]Imported {n} sessions[/green]")

if __name__ == "__main__":
    main()
