from pathlib import Path
import sqlite3

from backend.app.core.config import get_settings


SCHEMA_VERSION = "1"


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
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def initialize_database() -> None:
    """Initialize the application database schema."""
    connection = get_connection()

    try:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS schema_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS datasets (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                source TEXT NOT NULL,
                format TEXT NOT NULL,
                record_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,

                FOREIGN KEY (project_id)
                    REFERENCES projects(id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS dataset_versions (
                id TEXT PRIMARY KEY,
                dataset_id TEXT NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                record_count INTEGER NOT NULL DEFAULT 0,
                processing_status TEXT NOT NULL DEFAULT 'raw',
                created_at TEXT NOT NULL,

                FOREIGN KEY (dataset_id)
                    REFERENCES datasets(id)
                    ON DELETE CASCADE,

                UNIQUE(dataset_id, version)
            );

            CREATE TABLE IF NOT EXISTS analyses (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                dataset_version_id TEXT NOT NULL,
                analysis_type TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                parameters TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                completed_at TEXT,

                FOREIGN KEY (project_id)
                    REFERENCES projects(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (dataset_version_id)
                    REFERENCES dataset_versions(id)
                    ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_datasets_project_id
                ON datasets(project_id);

            CREATE INDEX IF NOT EXISTS idx_dataset_versions_dataset_id
                ON dataset_versions(dataset_id);

            CREATE INDEX IF NOT EXISTS idx_analyses_project_id
                ON analyses(project_id);

            CREATE INDEX IF NOT EXISTS idx_analyses_dataset_version_id
                ON analyses(dataset_version_id);

            INSERT INTO schema_metadata (key, value)
            VALUES ('schema_version', '1')
            ON CONFLICT(key)
            DO UPDATE SET value = excluded.value;
            """
        )
        # Schema migration: add storage_path to dataset_versions
        columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(dataset_versions)"
            ).fetchall()
        }

        if "storage_path" not in columns:
            connection.execute(
                """
                ALTER TABLE dataset_versions
                ADD COLUMN storage_path TEXT
                """
            )        
	# Schema migration: add analysis execution fields
        columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(analyses)"
            ).fetchall()
        }

        if "result_path" not in columns:
            connection.execute(
                """
                ALTER TABLE analyses
                ADD COLUMN result_path TEXT
                """
            )

        if "started_at" not in columns:
            connection.execute(
                """
                ALTER TABLE analyses
                ADD COLUMN started_at TEXT
                """
            )
        connection.commit()

    finally:
        connection.close()