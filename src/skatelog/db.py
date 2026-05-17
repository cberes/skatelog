from pathlib import Path
from sqlalchemy import Engine
from sqlmodel import SQLModel, create_engine

DEFAULT_DB_PATH = Path.home() / ".skatelog" / "skatelog.db"

def get_engine(db_path: Path | None = None) -> Engine:
    path = db_path or DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{path}")
    SQLModel.metadata.create_all(engine)
    return engine
