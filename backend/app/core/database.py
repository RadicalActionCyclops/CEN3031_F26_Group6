from collections.abc import Generator
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.config import get_settings

class Base(DeclarativeBase):
    pass

def create_database_engine(database_url: str) -> Engine:
    engine_options: dict[str, object] = {}
    if database_url.startswith("sqlite"):
        engine_options["connect_args"] = {"check_same_thread": False}
        if database_url in {"sqlite://", "sqlite:///:memory:"}:
            engine_options["poolclass"] = StaticPool
    database_engine = create_engine(database_url, **engine_options)

    if database_url.startswith("sqlite"):

        @event.listens_for(database_engine, "connect")
        def enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return database_engine


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

engine = create_database_engine(get_settings().database_url)
SessionLocal = create_session_factory(engine)

def get_db() -> Generator[Session, None, None]:
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()

def initialize_database(database_engine: Engine = engine) -> None:
    # Import model modules here so every table is registered on shared metadata.
    from app.features.auth import models as auth_models  # noqa: F401
    from app.features.community import models as community_models  # noqa: F401
    from app.features.messages import models as message_models  # noqa: F401
    from app.features.profiles import models as profile_models  # noqa: F401

    Base.metadata.create_all(bind=database_engine)
