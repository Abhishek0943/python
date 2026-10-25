from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from app.config.setting import settings

engine = create_engine(settings.DB_URL, echo=False)


def create_db_and_tables() -> None:
    import app.model.url  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """One database session per request. FastAPI calls this through Depends()
    and closes the session automatically when the request finishes."""
    with Session(engine) as session:
        yield session