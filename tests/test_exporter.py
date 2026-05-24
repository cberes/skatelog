from collections.abc import Iterator
from datetime import date
from pathlib import Path
import pytest
from sqlmodel import Session as DBSession
from sqlmodel import SQLModel, create_engine
from skatelog.exporter import export_csv
from skatelog.models import Session, Discipline

FIXTURE_CSV_EMPTY = Path(__file__).parent / "fixtures" / "export_empty.csv"
FIXTURE_CSV_NON_EMPTY = Path(__file__).parent / "fixtures" / "export_expected.csv"

@pytest.fixture
def db() -> Iterator[DBSession]:
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with DBSession(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

def test_export_csv_with_empty_db(db: DBSession, tmp_path: Path) -> None:
    csv_path = tmp_path / "empty.csv"
    exported = export_csv(csv_path, db)
    assert exported == 0
    assert list(csv_path.open()) == list(FIXTURE_CSV_EMPTY.open())

def test_export_csv_with_sessions(db: DBSession, tmp_path: Path) -> None:
    day1, day2, day3, day4 = (date(2026, 1, i + 1) for i in range(4))
    sessions = [
        _session_skatepark(day1),
        _session_tennis_court(day2),
        _session_notes_only(day3, "rest day"),
        _session_streets(day4),
    ]
    db.add_all(sessions)
    db.commit()
    csv_path = tmp_path / "sessions.csv"
    exported = export_csv(csv_path, db)
    assert exported == len(sessions)
    assert list(csv_path.open()) == list(FIXTURE_CSV_NON_EMPTY.open())

def _session_skatepark(day: date) -> Session:
    return Session(
        day=day,
        where="Skatepark",
        shoe="Vulc",
        board="Egg",
        notes="kickflip",
        a_frame=True,
        hip=True,
    )

def _session_tennis_court(day: date) -> Session:
    return Session(
        day=day,
        where="Tennis Court",
        shoe="Cupsole",
        board="Popsicle",
        notes="heelflip",
        bowl=True,
        manual=True,
        transition=True,
    )

def _session_streets(day: date) -> Session:
    return Session(
        day=day,
        where="The streets",
        shoe="Vulc",
        board="Popsicle",
        box=True,
        flat=True,
    )

def _session_notes_only(day: date, notes: str) -> Session:
    return Session(day=day, notes=notes)

