from uuid import UUID

from backend.app.db.database import get_connection
from backend.app.models.dataset_version import DatasetVersion


class DatasetVersionRepository:
    """Repository for DatasetVersion persistence."""

    def create(self, version: DatasetVersion) -> DatasetVersion:
        connection = get_connection()

        try:
            connection.execute(
                """
                INSERT INTO dataset_versions (
                    id,
                    dataset_id,
                    version,
                    record_count,
                    processing_status,
                    storage_path,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(version.id),
                    str(version.dataset_id),
                    version.version,
                    version.record_count,
                    version.processing_status,
                    version.storage_path,
                    version.created_at.isoformat(),
                ),
            )

            connection.commit()
            return version

        finally:
            connection.close()

    def get(self, version_id: UUID) -> DatasetVersion | None:
        connection = get_connection()

        try:
            row = connection.execute(
                """
                SELECT
                    id,
                    dataset_id,
                    version,
                    record_count,
                    processing_status,
                    storage_path,
                    created_at
                FROM dataset_versions
                WHERE id = ?
                """,
                (str(version_id),),
            ).fetchone()

            if row is None:
                return None

            return DatasetVersion(
                id=UUID(row["id"]),
                dataset_id=UUID(row["dataset_id"]),
                version=row["version"],
                record_count=row["record_count"],
                processing_status=row["processing_status"],
                storage_path=row["storage_path"],
                created_at=row["created_at"],
            )

        finally:
            connection.close()

    def list(self, dataset_id: UUID) -> list[DatasetVersion]:
        connection = get_connection()

        try:
            rows = connection.execute(
                """
                SELECT
                    id,
                    dataset_id,
                    version,
                    record_count,
                    processing_status,
                    storage_path,
                    created_at
                FROM dataset_versions
                WHERE dataset_id = ?
                ORDER BY version
                """,
                (str(dataset_id),),
            ).fetchall()

            return [
                DatasetVersion(
                    id=UUID(row["id"]),
                    dataset_id=UUID(row["dataset_id"]),
                    version=row["version"],
                    record_count=row["record_count"],
                    processing_status=row["processing_status"],
                    storage_path=row["storage_path"],
                    created_at=row["created_at"],
                )
                for row in rows
            ]

        finally:
            connection.close()