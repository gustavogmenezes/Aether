from collections.abc import Callable
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base


class Database:
    def __init__(self, url: str) -> None:
        self.url = url
        self.engine: Engine = create_engine(
            url,
            future=True,
            connect_args=self._sqlite_connect_args(url),
        )
        self.session_factory: Callable[[], Session] = sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
            future=True,
        )

    @classmethod
    def from_path(cls, path: Path) -> "Database":
        return cls(f"sqlite:///{path}")

    def create_schema(self) -> None:
        Base.metadata.create_all(self.engine)

    def dispose(self) -> None:
        self.engine.dispose()

    @staticmethod
    def _sqlite_connect_args(url: str) -> dict[str, object]:
        if url.startswith("sqlite:"):
            return {"check_same_thread": False}
        return {}
