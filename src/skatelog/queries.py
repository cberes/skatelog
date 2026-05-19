from collections.abc import Iterator
from datetime import date
from sqlalchemy import func
from sqlmodel import Session as DBSession
from sqlmodel import select
from skatelog.db import get_engine
from skatelog.models import Discipline, Session

def find_session(target: date) -> Session | None:
    """Show a day's session."""
    engine = get_engine()
    with DBSession(engine) as db:
        return db.get(Session, target)

# TODO what's the type of col?
def _find_values(col, start: date | None, end: date | None) -> dict[str, int]:
    engine = get_engine()
    with DBSession(engine) as db:
        statement = select(col, func.count(Session.day)) \
            .where(Session.day >= (start or date.min), Session.day < (end or date.max)) \
            .group_by(col)
        return {str(x[0]): x[1] for x in db.exec(statement) if x[0] is not None}

def find_location_counts(start: date | None = None, end: date | None = None) -> dict[str, int]:
    return _find_values(Session.where, start, end)

def find_shoe_counts(start: date | None = None, end: date | None = None) -> dict[str, int]:
    return _find_values(Session.shoe, start, end)

def find_board_counts(start: date | None = None, end: date | None = None) -> dict[str, int]:
    return _find_values(Session.board, start, end)

def find_locations(start: date | None = None) -> list[str]:
    return list(find_location_counts(start).keys())

def find_shoes(start: date | None = None) -> list[str]:
    return list(find_shoe_counts(start).keys())

def find_boards(start: date | None = None) -> list[str]:
    return list(find_board_counts(start).keys())

def _delete_by_day(db: DBSession, day: date) -> None:
    existing = db.get(Session, day)
    if existing is not None:
        db.delete(existing)
        db.flush()

def find_most_recent_session() -> Session | None:
    engine = get_engine()
    with DBSession(engine) as db:
        statement = select(Session) \
            .where(Session.where is not None, Session.shoe is not None, Session.board is not None) \
            .order_by(Session.day.desc()) \
            .limit(1)
        return db.exec(statement).first()

def create_session(session: Session) -> None:
    engine = get_engine()
    with DBSession(engine) as db:
        _delete_by_day(db, session.day)
        db.add(session)
        db.commit()

def delete_session(target: date) -> None:
    engine = get_engine()
    with DBSession(engine) as db:
        _delete_by_day(db, target)
        db.commit()

def find_by_date_range(start: date, end: date) -> Iterator[Session]:
    engine = get_engine()
    with DBSession(engine) as db:
        statement = select(Session).where(Session.day >= start, Session.day < end)
        sessions = db.exec(statement)
        for session in sessions:
            yield session

def find_discipline_counts(start: date | None = None, end: date | None = None) -> dict[Discipline, int]:
    counts = {d: 0 for d in Discipline}
    for session in find_by_date_range(start or date.min, end or date.max):
        for d in session.disciplines:
            counts[d] += 1
    return counts
