import csv
from collections.abc import Iterator
from datetime import date
from pathlib import Path
from sqlmodel import Session as DBSession
from skatelog.models import Session
from typing import TypeAlias

CsvRow: TypeAlias = dict[str, str | None]

_DISCIPLINE_COLUMNS: dict[str, str] = {
    "a/hip": "a_frame",
    "bank": "bank",
    "bowl": "bowl",
    "box": "box",
    "flat": "flat",
    "free": "free",
    "hip": "hip",
    "mnl": "manual",
    "rail": "rail",
    "slappy": "slappy",
    "tran": "transition",
    "vert": "vert",
}

def _to_bool(row: CsvRow, key: str) -> bool:
    return (row.get(key) or "").strip().lower() == 'true'

def _to_date(row: CsvRow, key: str) -> date:
    return date.fromisoformat((row.get(key) or "").strip())

def _to_str(row: CsvRow, key: str) -> str | None:
    value = row.get(key)
    if value is None:
        return None
    return value.strip() or None

def parse_rows(csv_path: Path) -> Iterator[Session]:
    with csv_path.open(newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for raw_row in reader:
            row = {(k or "").strip().lower(): v for k, v in raw_row.items()}
            discipline_flags = {
                attr: _to_bool(row, csv_col) for csv_col, attr in _DISCIPLINE_COLUMNS.items()
            }

            session = Session(
                day=_to_date(row, "date"),
                where=_to_str(row, "where"),
                shoe=_to_str(row, "shoe"),
                board=_to_str(row, "deck"),
                notes=_to_str(row, "notes"),
                **discipline_flags,
            )

            if session.is_good:
                yield session


def import_csv(csv_path: Path, db: DBSession) -> int:
    count = 0
    for session in parse_rows(csv_path):
        existing = db.get(Session, session.day)
        if existing is not None:
            db.delete(existing)
            db.flush()
        print(session)
        db.add(session)
        count += 1
    db.commit()
    return count
