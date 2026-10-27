from sqlalchemy import text

from app.core.database import create_database_engine


def test_sqlite_foreign_keys_are_enabled() -> None:
    database_engine = create_database_engine("sqlite:///:memory:")

    try:
        with database_engine.connect() as connection:
            foreign_keys_enabled = connection.scalar(text("PRAGMA foreign_keys"))
    finally:
        database_engine.dispose()

    assert foreign_keys_enabled == 1
