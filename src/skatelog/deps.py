from collections.abc import Iterator

from sqlmodel import Session as DBSession

from skatelog.db import get_engine


def get_db() -> Iterator[DBSession]:
    with DBSession(get_engine()) as db:
        yield db
