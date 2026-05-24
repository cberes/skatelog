from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date
from sqlalchemy import func
from sqlmodel import Session as DBSession
from sqlmodel import col, select
from skatelog.db import get_engine
from skatelog.models import Discipline, Session
from typing import Any

def find_session(db: DBSession, target: date) -> Session | None:
    """Show a day's session."""
    return db.get(Session, target)

@dataclass
class SessionAggregate:
    key: str
    count: int
    start: date
    end: date

    @property
    def days_since(self) -> int | None:
        delta = date.today() - self.end
        return delta.days if delta.days >= 0 else None

    @classmethod
    def from_tuple(cls, t: tuple[Any, int, date, date]) -> SessionAggregate:
        return SessionAggregate(str(t[0]), t[1], t[2], t[3])

def _find_values(db: DBSession, column: Any, start: date | None, end: date | None) -> list[SessionAggregate]:
    statement = select(column, func.count(col(Session.day)), func.min(col(Session.day)), func.max(col(Session.day))) \
        .where(column != None, Session.day >= (start or date.min), Session.day < (end or date.max)) \
        .group_by(column)
    return [SessionAggregate.from_tuple(it) for it in db.exec(statement)]

def find_location_counts(db: DBSession, start: date | None = None, end: date | None = None) -> list[SessionAggregate]:
    return _find_values(db, Session.where, start, end)

def find_shoe_counts(db: DBSession, start: date | None = None, end: date | None = None) -> list[SessionAggregate]:
    return _find_values(db, Session.shoe, start, end)

def find_board_counts(db: DBSession, start: date | None = None, end: date | None = None) -> list[SessionAggregate]:
    return _find_values(db, Session.board, start, end)

def find_locations(db: DBSession, start: date | None = None) -> set[str]:
    return set(it.key for it in find_location_counts(db, start))

def find_shoes(db: DBSession, start: date | None = None) -> set[str]:
    return set(it.key for it in find_shoe_counts(db, start))

def find_boards(db: DBSession, start: date | None = None) -> set[str]:
    return set(it.key for it in find_board_counts(db, start))

def _delete_by_day(db: DBSession, day: date) -> None:
    existing = db.get(Session, day)
    if existing is not None:
        db.delete(existing)
        db.flush()

def find_most_recent_session(db: DBSession) -> Session | None:
    statement = select(Session) \
        .where(Session.where != None, Session.shoe != None, Session.board != None) \
        .order_by(col(Session.day).desc()) \
        .limit(1)
    return db.exec(statement).first()

def create_session(db: DBSession, session: Session) -> None:
    _delete_by_day(db, session.day)
    db.add(session)
    db.commit()

def delete_session(db: DBSession, target: date) -> None:
    _delete_by_day(db, target)
    db.commit()

def find_by_date_range(db: DBSession, start: date, end: date) -> Iterator[Session]:
    statement = select(Session).where(Session.day >= start, Session.day < end) \
        .order_by(col(Session.day))
    sessions = db.exec(statement)
    for session in sessions:
        yield session

def find_discipline_counts(db: DBSession, start: date | None = None, end: date | None = None) -> list[SessionAggregate]:
    aggs = {d: SessionAggregate(str(d), 0, date.max, date.max) for d in Discipline}
    for session in find_by_date_range(db, start or date.min, end or date.max):
        for d in session.disciplines:
            agg = aggs[d]
            agg.count += 1
            agg.start = min(session.day, agg.start)
            agg.end = session.day
    return list(aggs.values())
