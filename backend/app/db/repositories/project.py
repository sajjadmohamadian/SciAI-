from datetime import datetime, timezone
from uuid import UUID

from backend.app.db.database import get_connection
from backend.app.models.project import Project


class ProjectRepository:
    """Repository for Project persistence."""

    def create(self, project: Project) -> Project:
        connection = get_connection()

        try:
            connection.execute(
                """
                INSERT INTO projects (
                    id,
                    name,
                    description,
                    status,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(project.id),
                    project.name,
                    project.description,
                    project.status,
                    project.created_at.isoformat(),
                    project.updated_at.isoformat(),
                ),
            )

            connection.commit()

            return project

        finally:
            connection.close()

    def get(self, project_id: UUID) -> Project | None:
        connection = get_connection()

        try:
            row = connection.execute(
                """
                SELECT
                    id,
                    name,
                    description,
                    status,
                    created_at,
                    updated_at
                FROM projects
                WHERE id = ?
                """,
                (str(project_id),),
            ).fetchone()

            if row is None:
                return None

            return Project(
                id=UUID(row["id"]),
                name=row["name"],
                description=row["description"],
                status=row["status"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )

        finally:
            connection.close()

    def list(self) -> list[Project]:
        connection = get_connection()

        try:
            rows = connection.execute(
                """
                SELECT
                    id,
                    name,
                    description,
                    status,
                    created_at,
                    updated_at
                FROM projects
                ORDER BY created_at DESC
                """
            ).fetchall()

            return [
                Project(
                    id=UUID(row["id"]),
                    name=row["name"],
                    description=row["description"],
                    status=row["status"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                )
                for row in rows
            ]

        finally:
            connection.close()

    def update(self, project: Project) -> Project:
        connection = get_connection()

        try:
            updated_at = datetime.now(timezone.utc)

            connection.execute(
                """
                UPDATE projects
                SET
                    name = ?,
                    description = ?,
                    status = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    project.name,
                    project.description,
                    project.status,
                    updated_at.isoformat(),
                    str(project.id),
                ),
            )

            connection.commit()

            return Project(
                id=project.id,
                name=project.name,
                description=project.description,
                status=project.status,
                created_at=project.created_at,
                updated_at=updated_at,
            )

        finally:
            connection.close()

    def delete(self, project_id: UUID) -> bool:
        connection = get_connection()

        try:
            cursor = connection.execute(
                """
                DELETE FROM projects
                WHERE id = ?
                """,
                (str(project_id),),
            )

            connection.commit()

            return cursor.rowcount > 0

        finally:
            connection.close()