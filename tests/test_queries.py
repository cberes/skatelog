from collections.abc import Iterator
from datetime import date
import pytest
from sqlmodel import Session as DBSession
from sqlmodel import SQLModel, create_engine, select
from skatelog.models import Session, Discipline
import skatelog.queries as q

@pytest.fixture
def db() -> Iterator[DBSession]:
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with DBSession(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

def test_find_session_returns_none_when_no_session(db: DBSession) -> None:
    assert q.find_session(db, date(2026, 1, 1)) is None

def test_find_session_returns_session(db: DBSession) -> None:
    day = date(2026, 1, 1)
    session = Session(
        day=day,
        where="Skatepark",
        shoe="Vulc",
        board="Egg",
        notes="kickflip",
        a_frame=True,
    )
    db.add(session)
    db.commit()
    found = q.find_session(db, day)
    assert found is not None
    assert found.day == day
    assert found.disciplines == {Discipline.A_FRAME}

def test_create_session_persists_new_session(db: DBSession) -> None:
    day = date(2026, 1, 1)
    session = Session(
        day=day,
        where="Skatepark",
        shoe="Vulc",
        board="Egg",
        notes="kickflip",
        a_frame=True,
    )
    q.create_session(db, session)
    found = db.get(Session, day)
    assert found is not None
    assert found.day == day
    assert found.disciplines == {Discipline.A_FRAME}

def test_create_session_deletes_duplicate_session(db: DBSession) -> None:
    day = date(2026, 1, 1)
    session1 = Session(
        day=day,
        where="Skatepark",
        shoe="Vulc",
        board="Egg",
        notes="kickflip",
        a_frame=True,
    )
    db.add(session1)
    db.commit()
    session2 = Session(
        day=day,
        where="Tennis Court",
        shoe="Cupsole",
        board="Popsicle",
        notes="heelflip",
        bowl=True,
    )
    q.create_session(db, session2)
    found = db.get(Session, day)
    assert found is not None
    assert found.day == day
    assert found.disciplines == {Discipline.BOWL}

def test_delete_session(db: DBSession) -> None:
    day = date(2026, 1, 1)
    session = Session(
        day=day,
        where="Skatepark",
        shoe="Vulc",
        board="Egg",
        notes="kickflip",
        a_frame=True,
    )
    db.add(session)
    db.commit()
    assert db.get(Session, day) is not None
    q.delete_session(db, day)
    assert db.get(Session, day) is None

