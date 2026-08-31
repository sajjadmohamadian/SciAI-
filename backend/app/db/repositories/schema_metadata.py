from backend.app.db.database import get_connection


def set_metadata(key: str, value: str) -> None:
    """Create or update a schema metadata value."""
    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO schema_metadata (key, value)
            VALUES (?, ?)
            ON CONFLICT(key)
            DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )

        connection.commit()

    finally:
        connection.close()


def get_metadata(key: str) -> str | None:
    """Return a schema metadata value by key."""
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT value
            FROM schema_metadata
            WHERE key = ?
            """,
            (key,),
        ).fetchone()

        if row is None:
            return None

        return row["value"]

    finally:
        connection.close()