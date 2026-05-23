import csv
from collections.abc import Iterable
from pathlib import Path
from sqlmodel import Session as DBSession
from sqlmodel import col, select
from skatelog.models import Discipline, Session
from typing import TypeAlias

CsvRow: TypeAlias = dict[str, str | None]

_DISCIPLINE_COLUMNS: dict[Discipline, str] = {
    Discipline.A_FRAME: "A",
    Discipline.BANK: "Bank",
    Discipline.BOWL: "Bowl",
    Discipline.BOX: "Box",
    Discipline.FLAT: "Flat",
    Discipline.FREE: "Free",
    Discipline.HIP: "Hip",
    Discipline.MANUAL: "Mnl",
    Discipline.RAIL: "Rail",
    Discipline.SLAPPY: "Slappy",
    Discipline.TRANSITION: "Tran",
    Discipline.VERT: "Vert",
}

def _write_rows(csv_path: Path, rows: Iterable[CsvRow]) -> None:
    field_names = ["Date", "Flat", "Free", "Box", "Rail", "Slappy",
                   "A", "Hip", "Bank", "Mnl", "Tran", "Bowl",
                   "Vert", "Where", "Shoe", "Deck", "Notes"]
    with csv_path.open(mode="w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=field_names)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

def _to_row(session: Session) -> CsvRow:
    disciplines = session.disciplines
    disc_args = {v: "TRUE" if k in disciplines else "FALSE" for k, v in _DISCIPLINE_COLUMNS.items()}
    return {
        "Date": session.day.isoformat(),
        "Where": session.where,
        "Shoe": session.shoe,
        "Deck": session.board,
        "Notes": session.notes,
        **disc_args,
    }

def export_csv(csv_path: Path, db: DBSession) -> int:
    statement = select(Session).order_by(col(Session.day))
    sessions = db.exec(statement)
    rows = [_to_row(s) for s in sessions]
    _write_rows(csv_path, rows)
    return len(rows)
