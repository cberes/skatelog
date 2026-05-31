from collections.abc import Iterator
from datetime import date
from pathlib import Path
import pytest
from sqlmodel import Session as DBSession
from sqlmodel import SQLModel, create_engine, select
from skatelog.importer import import_csv, parse_rows
from skatelog.models import Discipline, Session, Stance, Trick

FIXTURE = Path(__file__).parent / "fixtures" / "journal_sample.csv"

@pytest.fixture
def db() -> Iterator[DBSession]:
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with DBSession(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

def _by_date(csv_path: Path) -> dict[str, Session]:
    return {s.day.isoformat(): s for s in parse_rows(csv_path)}

def test_parse_skips_future_empty_rows() -> None:
    sessions = list(parse_rows(FIXTURE))
    assert len(sessions) == 4
    assert "2026-08-15" not in {s.day.isoformat() for s in sessions}

def test_parse_rest_day_keeps_notes_but_marks_not_skated() -> None:
    rest = _by_date(FIXTURE)["2026-02-10"]
    assert rest.notes == "Snowboarding"
    assert rest.disciplines == set()
    assert rest.skated is False

def test_parse_real_session_normalizes_fields() -> None:
    s = _by_date(FIXTURE)["2026-01-04"]
    assert Discipline.MANUAL in s.disciplines
    assert Discipline.TRANSITION in s.disciplines
    assert s.where == "Home"
    assert s.shoe == "Blazer mid"
    assert s.board == "Ishod"
    assert s.notes == "blunt nose grabs (3 regular, 3 switch)"
    assert s.skated is True

def test_parse_real_session_parses_tricks() -> None:
    s = _by_date(FIXTURE)["2026-01-04"]
    assert sorted(s.tricks, key=lambda it: it.stance) == [Trick(day=s.day, name="blunt nose grab", stance=stance, count=3) for stance in (Stance.REGULAR, Stance.SWITCH)]
    assert s.trick_count == 6

def test_parse_empty_notes_become_none() -> None:
    s = _by_date(FIXTURE)["2026-04-23"]
    assert s.notes is None
    assert s.trick_count == 0

def test_import_csv_is_idempotent(db: DBSession) -> None:
    n1 = import_csv(FIXTURE, db)
    n2 = import_csv(FIXTURE, db)
    assert n1 == n2 == 4
    all_sessions = db.exec(select(Session)).all()
    assert len(all_sessions) == n1

def test_import_csv_saves_tricks(db: DBSession) -> None:
    import_csv(FIXTURE, db)
    day = date(2026, 1, 4)
    tricks = db.exec(select(Trick).where(Trick.day == day)).all()
    for t in tricks:
        t.id = None
    assert sorted(tricks, key=lambda it: it.stance) == [Trick(day=day, name="blunt nose grab", stance=stance, count=3) for stance in (Stance.REGULAR, Stance.SWITCH)]
