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
    db.add_all([session1, session3, session2])
    db.commit()
    most_recent = q.find_most_recent_session(db)
    assert most_recent == session3

def test_find_most_recent_session_skips_empty_sessions(db: DBSession) -> None:
    day1, day2 = (date(2026, 1, i + 1) for i in range(2))
    session1 = _session_skatepark(day1)
    session2 = _session_empty(day2)
    db.add_all([session1, session2])
    db.commit()
    most_recent = q.find_most_recent_session(db)
    assert most_recent == session1

def test_find_by_date_range(db: DBSession) -> None:
    days = [date(2026, 1, i + 1) for i in range(10)]
    sessions = [_session_skatepark(d) for d in days]
    db.add_all(sessions)
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
        db.add_all(sessions1 + sessions2)
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
        aggs = q.find_location_counts(db, start=self.days[1], end=self.days[14])
        aggs = sorted(aggs, key=lambda it: it.count)
        assert len(aggs) == 2
        assert aggs[0].key == "Tennis Court"
        assert aggs[0].count == 4
        assert aggs[0].start == self.days[10]
        assert aggs[0].end == self.days[13]
        assert aggs[1].key == "Skatepark"
        assert aggs[1].count == 9
        assert aggs[1].start == self.days[1]
        assert aggs[1].end == self.days[9]

    def test_find_location_aggs_without_start_end_includes_all(self, db: DBSession) -> None:
        aggs = q.find_location_counts(db)
        aggs = sorted(aggs, key=lambda it: it.count)
        assert len(aggs) == 2
        assert aggs[0].key == "Tennis Court"
        assert aggs[0].count == 5
        assert aggs[0].start == self.days[10]
        assert aggs[0].end == self.days[14]
        assert aggs[1].key == "Skatepark"
        assert aggs[1].count == 10
        assert aggs[1].start == self.days[0]
        assert aggs[1].end == self.days[9]

    def test_find_shoe_aggs_with_start_end_filters_by_day(self, db: DBSession) -> None:
        aggs = q.find_shoe_counts(db, start=self.days[1], end=self.days[14])
        aggs = sorted(aggs, key=lambda it: it.count)
        assert len(aggs) == 2
        assert aggs[0].key == "Cupsole"
        assert aggs[0].count == 4
        assert aggs[0].start == self.days[10]
        assert aggs[0].end == self.days[13]
        assert aggs[1].key == "Vulc"
        assert aggs[1].count == 9
        assert aggs[1].start == self.days[1]
        assert aggs[1].end == self.days[9]

    def test_find_shoe_aggs_without_start_end_includes_all(self, db: DBSession) -> None:
        aggs = q.find_shoe_counts(db)
        aggs = sorted(aggs, key=lambda it: it.count)
        assert len(aggs) == 2
        assert aggs[0].key == "Cupsole"
        assert aggs[0].count == 5
        assert aggs[0].start == self.days[10]
        assert aggs[0].end == self.days[14]
        assert aggs[1].key == "Vulc"
        assert aggs[1].count == 10
        assert aggs[1].start == self.days[0]
        assert aggs[1].end == self.days[9]

    def test_find_board_aggs_with_start_end_filters_by_day(self, db: DBSession) -> None:
        aggs = q.find_board_counts(db, start=self.days[1], end=self.days[14])
        aggs = sorted(aggs, key=lambda it: it.count)
        assert len(aggs) == 2
        assert aggs[0].key == "Popsicle"
        assert aggs[0].count == 4
        assert aggs[0].start == self.days[10]
        assert aggs[0].end == self.days[13]
        assert aggs[1].key == "Egg"
        assert aggs[1].count == 9
        assert aggs[1].start == self.days[1]
        assert aggs[1].end == self.days[9]

    def test_find_board_aggs_without_start_end_includes_all(self, db: DBSession) -> None:
        aggs = q.find_board_counts(db)
        aggs = sorted(aggs, key=lambda it: it.count)
        assert len(aggs) == 2
        assert aggs[0].key == "Popsicle"
        assert aggs[0].count == 5
        assert aggs[0].start == self.days[10]
        assert aggs[0].end == self.days[14]
        assert aggs[1].key == "Egg"
        assert aggs[1].count == 10
        assert aggs[1].start == self.days[0]
        assert aggs[1].end == self.days[9]

    def test_find_discipline_counts_with_start_end_filters_by_day(self, db: DBSession) -> None:
        aggs = q.find_discipline_counts(db, start=self.days[1], end=self.days[14])
        aggs = sorted(aggs, key=lambda it: it.key)
        assert aggs[0].key == str(Discipline.A_FRAME)
        assert aggs[0].count == 9
        assert aggs[0].start == self.days[1]
        assert aggs[0].end == self.days[9]
        assert aggs[1].key == str(Discipline.BANK)
        assert aggs[1].count == 0
        assert aggs[2].key == str(Discipline.BOWL)
        assert aggs[2].count == 4
        assert aggs[2].start == self.days[10]
        assert aggs[2].end == self.days[13]

    def test_find_discipline_counts_without_start_end_includes_all(self, db: DBSession) -> None:
        aggs = q.find_discipline_counts(db)
        aggs = sorted(aggs, key=lambda it: it.key)
        assert aggs[0].key == str(Discipline.A_FRAME)
        assert aggs[0].count == 10
        assert aggs[0].start == self.days[0]
        assert aggs[0].end == self.days[9]
        assert aggs[1].key == str(Discipline.BANK)
        assert aggs[1].count == 0
        assert aggs[2].key == str(Discipline.BOWL)
        assert aggs[2].count == 5
        assert aggs[2].start == self.days[10]
        assert aggs[2].end == self.days[14]

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
