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
    session = _session_skatepark(day)
    db.add(session)
    db.commit()
    found = q.find_session(db, day)
    assert found is not None
    assert found.day == day
    assert found.disciplines == {Discipline.A_FRAME}

def test_create_session_persists_new_session(db: DBSession) -> None:
    day = date(2026, 1, 1)
    session = _session_skatepark(day)
    q.create_session(db, session)
    found = db.get(Session, day)
    assert found is not None
    assert found.day == day
    assert found.disciplines == {Discipline.A_FRAME}

def test_create_session_deletes_duplicate_session(db: DBSession) -> None:
    day = date(2026, 1, 1)
    session1 = _session_skatepark(day)
    db.add(session1)
    db.commit()
    session2 = _session_tennis_court(day)
    q.create_session(db, session2)
    found = db.get(Session, day)
    assert found is not None
    assert found.day == day
    assert found.disciplines == {Discipline.BOWL}

def test_delete_session(db: DBSession) -> None:
    day = date(2026, 1, 1)
    session = _session_skatepark(day)
    db.add(session)
    db.commit()
    assert db.get(Session, day) is not None
    q.delete_session(db, day)
    assert db.get(Session, day) is None

def test_find_most_recent_session_returns_most_recent(db: DBSession) -> None:
    day1, day2, day3 = (date(2026, 1, i + 1) for i in range(3))
    session1 = _session_skatepark(day1)
    session2 = _session_skatepark(day2)
    session3 = _session_tennis_court(day3)
    [db.add(s) for s in (session1, session3, session2)]
    db.commit()
    most_recent = q.find_most_recent_session(db)
    assert most_recent == session3

def test_find_most_recent_session_skips_empty_sessions(db: DBSession) -> None:
    day1, day2 = (date(2026, 1, i + 1) for i in range(2))
    session1 = _session_skatepark(day1)
    session2 = _session_empty(day2)
    [db.add(s) for s in (session1, session2)]
    db.commit()
    most_recent = q.find_most_recent_session(db)
    assert most_recent == session1

def test_find_by_date_range(db: DBSession) -> None:
    days = [date(2026, 1, i + 1) for i in range(10)]
    sessions = [_session_skatepark(d) for d in days]
    [db.add(s) for s in sessions]
    db.commit()
    found = q.find_by_date_range(db, days[1], days[9])
    assert list(found) == sessions[1:9]

class TestCountByDateRange:
    @pytest.fixture(autouse=True)
    def setup_db(self, db: DBSession) -> None:
        days = [date(2026, 1, i + 1) for i in range(15)]
        self.days = days
        sessions1 = [_session_skatepark(d) for d in days[0:10]]
        sessions2 = [_session_tennis_court(d) for d in days[10:15]]
        [db.add(s) for s in (sessions1 + sessions2)]
        db.commit()

    def test_find_locations_with_start_filters_by_day(self, db: DBSession) -> None:
        found = q.find_locations(db, start=self.days[-1])
        assert found == {"Tennis Court"}

    def test_find_locations_without_start_includes_all(self, db: DBSession) -> None:
        found = q.find_locations(db)
        assert found == {"Skatepark", "Tennis Court"}

    def test_find_shoes_with_start_filters_by_day(self, db: DBSession) -> None:
        found = q.find_shoes(db, start=self.days[-1])
        assert found == {"Cupsole"}

    def test_find_shoes_without_start_includes_all(self, db: DBSession) -> None:
        found = q.find_shoes(db)
        assert found == {"Vulc", "Cupsole"}

    def test_find_boards_with_start_filters_by_day(self, db: DBSession) -> None:
        found = q.find_boards(db, start=self.days[-1])
        assert found == {"Popsicle"}

    def test_find_boards_without_start_includes_all(self, db: DBSession) -> None:
        found = q.find_boards(db)
        assert found == {"Egg", "Popsicle"}

    def test_find_location_counts_with_start_end_filters_by_day(self, db: DBSession) -> None:
        counts = q.find_location_counts(db, start=self.days[1], end=self.days[14])
        assert counts["Skatepark"] == 9
        assert counts["Tennis Court"] == 4
        assert len(counts) == 2

    def test_find_location_counts_without_start_end_includes_all(self, db: DBSession) -> None:
        counts = q.find_location_counts(db)
        assert counts["Skatepark"] == 10
        assert counts["Tennis Court"] == 5
        assert len(counts) == 2

    def test_find_shoe_counts_with_start_end_filters_by_day(self, db: DBSession) -> None:
        counts = q.find_shoe_counts(db, start=self.days[1], end=self.days[14])
        assert counts["Vulc"] == 9
        assert counts["Cupsole"] == 4
        assert len(counts) == 2

    def test_find_shoe_counts_without_start_end_includes_all(self, db: DBSession) -> None:
        counts = q.find_shoe_counts(db)
        assert counts["Vulc"] == 10
        assert counts["Cupsole"] == 5
        assert len(counts) == 2

    def test_find_board_counts_with_start_end_filters_by_day(self, db: DBSession) -> None:
        counts = q.find_board_counts(db, start=self.days[1], end=self.days[14])
        assert counts["Egg"] == 9
        assert counts["Popsicle"] == 4
        assert len(counts) == 2

    def test_find_board_counts_without_start_end_includes_all(self, db: DBSession) -> None:
        counts = q.find_board_counts(db)
        assert counts["Egg"] == 10
        assert counts["Popsicle"] == 5
        assert len(counts) == 2

    def test_find_discipline_counts_with_start_end_filters_by_day(self, db: DBSession) -> None:
        counts = q.find_discipline_counts(db, start=self.days[1], end=self.days[14])
        assert counts[Discipline.A_FRAME] == 9
        assert counts[Discipline.BOWL] == 4
        assert counts[Discipline.FLAT] == 0

    def test_find_discipline_counts_without_start_end_includes_all(self, db: DBSession) -> None:
        counts = q.find_discipline_counts(db)
        assert counts[Discipline.A_FRAME] == 10
        assert counts[Discipline.BOWL] == 5
        assert counts[Discipline.FLAT] == 0

def _session_skatepark(day: date) -> Session:
    return Session(
        day=day,
        where="Skatepark",
        shoe="Vulc",
        board="Egg",
        notes="kickflip",
        a_frame=True,
    )

def _session_tennis_court(day: date) -> Session:
    return Session(
        day=day,
        where="Tennis Court",
        shoe="Cupsole",
        board="Popsicle",
        notes="heelflip",
        bowl=True,
    )

def _session_empty(day: date) -> Session:
    return Session(day=day)
