from pathlib import Path
import sqlite3

from backend.app.core.config import get_settings


def get_database_path() -> Path:
    """Return the path to the application SQLite database."""
    settings = get_settings()

    data_dir = Path(settings.project_data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    return data_dir / "sciai.db"


def get_connection() -> sqlite3.Connection:
    """Create and return a SQLite database connection."""
    database_path = get_database_path()

    connection = sqlite3.connect(
        database_path,
        check_same_thread=False,
    )

    connection.row_factory = sqlite3.Row

    return connection


def initialize_database() -> None:
    """Initialize the application database."""
    connection = get_connection()

    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )

        connection.commit()

    finally:
        connection.close()