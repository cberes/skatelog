from collections.abc import Iterator
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session as DBSession
from sqlmodel import SQLModel, col, create_engine, select
from sqlmodel.pool import StaticPool

from skatelog.api import app
from skatelog.deps import get_db
from skatelog.models import Discipline, Session, Stance, Trick

_base_url = "/api/v1"


@pytest.fixture
def db() -> Iterator[DBSession]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with DBSession(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def client(db: DBSession) -> Iterator[TestClient]:
    def override_get_db() -> Iterator[DBSession]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_get_session_returns_404_when_no_session(client: TestClient) -> None:
    assert client.get(f"{_base_url}/sessions/2026-01-01").status_code == 404


def test_get_session_returns_session(db: DBSession, client: TestClient) -> None:
    day = date(2026, 1, 1)
    session = _session_skatepark(day)
    db.add(session)
    db.commit()

    resp = client.get(f"{_base_url}/sessions/{day.isoformat()}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["where"] == "Skatepark"


def test_add_session_persists_new_session(db: DBSession, client: TestClient) -> None:
    day = date(2026, 1, 1)
    json = {"day": day.isoformat(), "where": "Skatepark", "a_frame": True}
    resp = client.post(f"{_base_url}/sessions", json=json)

    assert resp.status_code == 201
    body = resp.json()
    assert body["day"] == day.isoformat()
    assert body["where"] == "Skatepark"
    assert body["a_frame"]
    assert db.get(Session, day) is not None


def test_add_session_returns_400_when_bad_session(db: DBSession, client: TestClient) -> None:
    day = date(2026, 1, 1)
    resp = client.post(f"{_base_url}/sessions", json={"day": day.isoformat()})

    assert resp.status_code == 400
    body = resp.json()
    assert body["detail"] == "Bad session"
    assert db.get(Session, day) is None


def test_add_session_persists_new_tricks(db: DBSession, client: TestClient) -> None:
    day = date(2026, 1, 1)
    notes = "kickflip, 3 switch noseslides"
    tricks = [
        Trick(day=day, name="kickflip"),
        Trick(day=day, stance=Stance.SWITCH, name="noseslide", count=3),
    ]
    json = {"day": day.isoformat(), "where": "Skatepark", "a_frame": True, "notes": notes}
    resp = client.post(f"{_base_url}/sessions", json=json)

    assert resp.status_code == 201
    body = resp.json()
    assert body["day"] == day.isoformat()
    assert body["where"] == "Skatepark"
    assert body["a_frame"]
    assert "tricks" not in body
    session = db.get(Session, day)
    assert session is not None
    sorted_tricks = sorted(session.tricks, key=lambda it: it.count)
    for i in range(len(tricks)):
        tricks[i].id = sorted_tricks[i].id
    assert sorted_tricks == tricks

    stmt = select(Trick).where(Trick.day == session.day).order_by(col(Trick.count))
    found_tricks = db.exec(stmt).all()
    assert found_tricks == tricks


def test_add_session_deletes_duplicate_session(db: DBSession, client: TestClient) -> None:
    day = date(2026, 1, 1)
    session1 = _session_skatepark(day)
    db.add(session1)
    db.commit()
    json = {"day": day.isoformat(), "where": "Tennis Court", "bowl": True}
    resp = client.post(f"{_base_url}/sessions", json=json)

    assert resp.status_code == 201
    body = resp.json()
    assert body["day"] == day.isoformat()
    assert body["where"] == "Tennis Court"
    assert body["bowl"]

    found = db.get(Session, day)
    assert found is not None
    assert found.day == day
    assert found.disciplines == {Discipline.BOWL}


def test_add_session_deletes_duplicate_tricks(db: DBSession, client: TestClient) -> None:
    day = date(2026, 1, 1)
    session1 = _session_skatepark(day)
    session1.tricks = [Trick(day=session1.day, name="kickflip")]
    db.add(session1)
    db.commit()
    tricks = [Trick(day=day, name="heelflip")]
    json = {"day": day.isoformat(), "where": "Tennis Court", "bowl": True, "notes": "heelflip"}
    resp = client.post(f"{_base_url}/sessions", json=json)

    assert resp.status_code == 201
    found = db.get(Session, day)
    assert found is not None
    assert found.where == "Tennis Court"
    found_tricks = db.exec(select(Trick).where(Trick.day == day)).all()
    tricks[0].id = found_tricks[0].id
    assert found_tricks == tricks


def test_delete_session(db: DBSession, client: TestClient) -> None:
    day = date(2026, 1, 1)
    session = _session_skatepark(day)
    db.add(session)
    db.commit()
    assert db.get(Session, day) is not None

    resp = client.delete(f"{_base_url}/sessions/{day.isoformat()}")
    assert resp.status_code == 200
    assert resp.text == ""
    assert db.get(Session, day) is None


def test_delete_session_returns_empty_when_not_found(client: TestClient) -> None:
    resp = client.delete(f"{_base_url}/sessions/{date(2026, 1, 1).isoformat()}")
    assert resp.status_code == 200
    assert resp.text == ""


def test_get_sessions(db: DBSession, client: TestClient) -> None:
    days = [date(2026, 1, 25) + timedelta(days=i) for i in range(10)]
    sessions = [_session_skatepark(d) for d in days]
    db.add_all(sessions)
    db.commit()

    resp = client.get(f"{_base_url}/sessions")
    assert resp.status_code == 200
    body = resp.json()
    assert sorted([it["day"] for it in body]) == [s.day.isoformat() for s in sessions]


def test_get_sessions_with_month_and_year_filter(db: DBSession, client: TestClient) -> None:
    days = [date(2026, 1, 25) + timedelta(days=i) for i in range(10)]
    sessions = [_session_skatepark(d) for d in days]
    db.add_all(sessions)
    db.commit()

    resp = client.get(f"{_base_url}/sessions?month=1&year=2026")
    assert resp.status_code == 200
    body = resp.json()
    assert sorted([it["day"] for it in body]) == [s.day.isoformat() for s in sessions[:7]]


def test_get_sessions_returns_empty_list_when_no_sessions(client: TestClient) -> None:
    resp = client.get(f"{_base_url}/sessions")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_tricks(db: DBSession, client: TestClient) -> None:
    days = [date(2026, 1, 25) + timedelta(days=i) for i in range(10)]
    tricks = [Trick(day=d, name=f"Kickflip {d}") for d in days]
    db.add_all(tricks)
    db.commit()

    resp = client.get(f"{_base_url}/tricks")
    assert resp.status_code == 200
    body = resp.json()
    assert sorted([it["day"] for it in body]) == [t.day.isoformat() for t in tricks]


def test_get_tricks_with_month_and_year_filter(db: DBSession, client: TestClient) -> None:
    days = [date(2026, 1, 25) + timedelta(days=i) for i in range(10)]
    tricks = [Trick(day=d, name=f"Kickflip {d}") for d in days]
    db.add_all(tricks)
    db.commit()

    resp = client.get(f"{_base_url}/tricks?month=1&year=2026")
    assert resp.status_code == 200
    body = resp.json()
    assert sorted([it["day"] for it in body]) == [t.day.isoformat() for t in tricks[:7]]


def test_get_tricks_returns_empty_list_when_no_sessions(client: TestClient) -> None:
    resp = client.get(f"{_base_url}/tricks")
    assert resp.status_code == 200
    assert resp.json() == []


class TestCountByDateRange:
    @pytest.fixture(autouse=True)
    def setup_db(self, db: DBSession) -> None:
        days = [date(2026, 1, 25) + timedelta(days=i) for i in range(15)]
        self.days = days
        sessions1 = [_session_skatepark(d) for d in days if d.day % 2 == 0]
        sessions2 = [_session_tennis_court(d) for d in days if d.day % 2 == 1]
        db.add_all(sessions1 + sessions2)
        db.commit()

    def test_get_locations(self, client: TestClient) -> None:
        resp = client.get(f"{_base_url}/locations")
        assert resp.status_code == 200
        body = sorted(resp.json(), key=lambda it: it["count"])
        assert [it["count"] for it in body] == [7, 8]
        assert [it["key"] for it in body] == ["Skatepark", "Tennis Court"]
        assert [it["start"] for it in body] == [d.isoformat() for d in reversed(self.days[:2])]
        assert [it["end"] for it in body] == [d.isoformat() for d in reversed(self.days[-2:])]

    def test_get_locations_with_month_and_year_filter(self, client: TestClient) -> None:
        resp = client.get(f"{_base_url}/locations?month=1&year=2026")
        assert resp.status_code == 200
        body = sorted(resp.json(), key=lambda it: it["count"])
        assert [it["count"] for it in body] == [3, 4]
        assert [it["key"] for it in body] == ["Skatepark", "Tennis Court"]
        assert [it["start"] for it in body] == [d.isoformat() for d in reversed(self.days[:2])]
        assert [it["end"] for it in body] == [d.isoformat() for d in self.days[5:7]]

    def test_get_shoes(self, client: TestClient) -> None:
        resp = client.get(f"{_base_url}/shoes")
        assert resp.status_code == 200
        body = sorted(resp.json(), key=lambda it: it["count"])
        assert [it["count"] for it in body] == [7, 8]
        assert [it["key"] for it in body] == ["Vulc", "Cupsole"]
        assert [it["start"] for it in body] == [d.isoformat() for d in reversed(self.days[:2])]
        assert [it["end"] for it in body] == [d.isoformat() for d in reversed(self.days[-2:])]

    def test_get_shoes_with_month_and_year_filter(self, client: TestClient) -> None:
        resp = client.get(f"{_base_url}/shoes?month=1&year=2026")
        assert resp.status_code == 200
        body = sorted(resp.json(), key=lambda it: it["count"])
        assert [it["count"] for it in body] == [3, 4]
        assert [it["key"] for it in body] == ["Vulc", "Cupsole"]
        assert [it["start"] for it in body] == [d.isoformat() for d in reversed(self.days[:2])]
        assert [it["end"] for it in body] == [d.isoformat() for d in self.days[5:7]]

    def test_get_boards(self, client: TestClient) -> None:
        resp = client.get(f"{_base_url}/boards")
        assert resp.status_code == 200
        body = sorted(resp.json(), key=lambda it: it["count"])
        assert [it["count"] for it in body] == [7, 8]
        assert [it["key"] for it in body] == ["Egg", "Popsicle"]
        assert [it["start"] for it in body] == [d.isoformat() for d in reversed(self.days[:2])]
        assert [it["end"] for it in body] == [d.isoformat() for d in reversed(self.days[-2:])]

    def test_get_boards_with_month_and_year_filter(self, client: TestClient) -> None:
        resp = client.get(f"{_base_url}/boards?month=1&year=2026")
        assert resp.status_code == 200
        body = sorted(resp.json(), key=lambda it: it["count"])
        assert [it["count"] for it in body] == [3, 4]
        assert [it["key"] for it in body] == ["Egg", "Popsicle"]
        assert [it["start"] for it in body] == [d.isoformat() for d in reversed(self.days[:2])]
        assert [it["end"] for it in body] == [d.isoformat() for d in self.days[5:7]]

    def test_get_disciplines(self, client: TestClient) -> None:
        resp = client.get(f"{_base_url}/disciplines")
        assert resp.status_code == 200
        body = sorted(resp.json(), key=lambda it: it["key"])
        assert [it["count"] for it in body[:3]] == [7, 0, 8]
        assert [it["key"] for it in body[:3]] == ["a_frame", "bank", "bowl"]
        assert [it["start"] for it in body[:3]] == [
            d.isoformat() for d in (self.days[1], date.max, self.days[0])
        ]
        assert [it["end"] for it in body[:3]] == [
            d.isoformat() for d in (self.days[14], date.max, self.days[13])
        ]

    def test_get_disciplines_with_month_and_year_filter(self, client: TestClient) -> None:
        resp = client.get(f"{_base_url}/disciplines?month=1&year=2026")
        assert resp.status_code == 200
        body = sorted(resp.json(), key=lambda it: it["key"])
        assert [it["count"] for it in body[:3]] == [3, 0, 4]
        assert [it["key"] for it in body[:3]] == ["a_frame", "bank", "bowl"]
        assert [it["start"] for it in body[:3]] == [
            d.isoformat() for d in (self.days[1], date.max, self.days[0])
        ]
        assert [it["end"] for it in body[:3]] == [
            d.isoformat() for d in (self.days[5], date.max, self.days[6])
        ]

    def test_get_streak(self, client: TestClient) -> None:
        resp = client.get(f"{_base_url}/streak")
        assert resp.status_code == 200
        body = resp.json()
        assert body["best"] == 15
        print(body["days"])
        assert body["days"] == [
            {"day": self.days[i].isoformat(), "streak": i + 1} for i in range(len(self.days))
        ]

    def test_get_streak_with_month_and_year_filter(self, client: TestClient) -> None:
        resp = client.get(f"{_base_url}/streak?month=1&year=2026")
        assert resp.status_code == 200
        body = resp.json()
        assert body["best"] == 7
        assert body["days"] == [
            {"day": self.days[i].isoformat(), "streak": i + 1} for i in range(7)
        ]


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
