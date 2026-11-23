from collections.abc import Callable

from sqlalchemy.orm import Session

from .repository import SqlAlchemySimulationRepository


class SqlAlchemySimulationUnitOfWork:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def __enter__(self) -> "SqlAlchemySimulationUnitOfWork":
        self.session = self._session_factory()
        self.repository = SqlAlchemySimulationRepository(self.session)
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: object | None,
    ) -> None:
        if exception_type is not None:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()

    def commit(self) -> None:
        self.session.commit()
