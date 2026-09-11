from uuid import UUID

from backend.app.db.database import get_connection
from backend.app.models.dataset import Dataset


class DatasetRepository:
    """Repository for Dataset persistence."""

    def create(self, dataset: Dataset) -> Dataset:
        connection = get_connection()

        try:
            connection.execute(
                """
                INSERT INTO datasets (
                    id,
                    project_id,
                    name,
                    source,
                    format,
                    record_count,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(dataset.id),
                    str(dataset.project_id),
                    dataset.name,
                    dataset.source,
                    dataset.format,
                    dataset.record_count,
                    dataset.created_at.isoformat(),
                ),
            )

            connection.commit()
            return dataset

        finally:
            connection.close()

    def get(self, dataset_id: UUID) -> Dataset | None:
        connection = get_connection()

        try:
            row = connection.execute(
                """
                SELECT
                    id,
                    project_id,
                    name,
                    source,
                    format,
                    record_count,
                    created_at
                FROM datasets
                WHERE id = ?
                """,
                (str(dataset_id),),
            ).fetchone()

            if row is None:
                return None

            return Dataset(
                id=UUID(row["id"]),
                project_id=UUID(row["project_id"]),
                name=row["name"],
                source=row["source"],
                format=row["format"],
                record_count=row["record_count"],
                created_at=row["created_at"],
            )

        finally:
            connection.close()

    def list(self, project_id: UUID | None = None) -> list[Dataset]:
        connection = get_connection()

        try:
            if project_id is None:
                rows = connection.execute(
                    """
                    SELECT
                        id,
                        project_id,
                        name,
                        source,
                        format,
                        record_count,
                        created_at
                    FROM datasets
                    ORDER BY created_at
                    """
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT
                        id,
                        project_id,
                        name,
                        source,
                        format,
                        record_count,
                        created_at
                    FROM datasets
                    WHERE project_id = ?
                    ORDER BY created_at
                    """,
                    (str(project_id),),
                ).fetchall()

            return [
                Dataset(
                    id=UUID(row["id"]),
                    project_id=UUID(row["project_id"]),
                    name=row["name"],
                    source=row["source"],
                    format=row["format"],
                    record_count=row["record_count"],
                    created_at=row["created_at"],
                )
                for row in rows
            ]

        finally:
            connection.close()