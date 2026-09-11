import json
from datetime import datetime
from uuid import UUID

from backend.app.db.database import get_connection
from backend.app.models.analysis import Analysis


class AnalysisRepository:
    """Repository for Analysis persistence."""

    def create(self, analysis: Analysis) -> Analysis:
        connection = get_connection()

        try:
            connection.execute(
                """
                INSERT INTO analyses (
                    id,
                    project_id,
                    dataset_version_id,
                    analysis_type,
                    status,
                    parameters,
                    result_path,
                    created_at,
                    started_at,
                    completed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(analysis.id),
                    str(analysis.project_id),
                    str(analysis.dataset_version_id),
                    analysis.analysis_type,
                    analysis.status,
                    json.dumps(analysis.parameters),
                    analysis.result_path,
                    analysis.created_at.isoformat(),
                    (
                        analysis.started_at.isoformat()
                        if analysis.started_at
                        else None
                    ),
                    (
                        analysis.completed_at.isoformat()
                        if analysis.completed_at
                        else None
                    ),
                ),
            )

            connection.commit()

        finally:
            connection.close()

        return analysis

    def get(self, analysis_id: UUID) -> Analysis | None:
        connection = get_connection()

        try:
            row = connection.execute(
                """
                SELECT
                    id,
                    project_id,
                    dataset_version_id,
                    analysis_type,
                    status,
                    parameters,
                    result_path,
                    created_at,
                    started_at,
                    completed_at
                FROM analyses
                WHERE id = ?
                """,
                (str(analysis_id),),
            ).fetchone()

        finally:
            connection.close()

        if row is None:
            return None

        return self._row_to_model(row)

    def list(self, project_id: UUID | None = None) -> list[Analysis]:
        connection = get_connection()

        try:
            if project_id is None:
                rows = connection.execute(
                    """
                    SELECT
                        id,
                        project_id,
                        dataset_version_id,
                        analysis_type,
                        status,
                        parameters,
                        result_path,
                        created_at,
                        started_at,
                        completed_at
                    FROM analyses
                    ORDER BY created_at DESC
                    """
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT
                        id,
                        project_id,
                        dataset_version_id,
                        analysis_type,
                        status,
                        parameters,
                        result_path,
                        created_at,
                        started_at,
                        completed_at
                    FROM analyses
                    WHERE project_id = ?
                    ORDER BY created_at DESC
                    """,
                    (str(project_id),),
                ).fetchall()

        finally:
            connection.close()

        return [self._row_to_model(row) for row in rows]

    def update(self, analysis: Analysis) -> Analysis:
        connection = get_connection()

        try:
            cursor = connection.execute(
                """
                UPDATE analyses
                SET
                    project_id = ?,
                    dataset_version_id = ?,
                    analysis_type = ?,
                    status = ?,
                    parameters = ?,
                    result_path = ?,
                    created_at = ?,
                    started_at = ?,
                    completed_at = ?
                WHERE id = ?
                """,
                (
                    str(analysis.project_id),
                    str(analysis.dataset_version_id),
                    analysis.analysis_type,
                    analysis.status,
                    json.dumps(analysis.parameters),
                    analysis.result_path,
                    analysis.created_at.isoformat(),
                    (
                        analysis.started_at.isoformat()
                        if analysis.started_at
                        else None
                    ),
                    (
                        analysis.completed_at.isoformat()
                        if analysis.completed_at
                        else None
                    ),
                    str(analysis.id),
                ),
            )

            connection.commit()

            if cursor.rowcount == 0:
                raise ValueError(
                    f"Analysis '{analysis.id}' not found."
                )

        finally:
            connection.close()

        return analysis

    def delete(self, analysis_id: UUID) -> None:
        connection = get_connection()

        try:
            cursor = connection.execute(
                """
                DELETE FROM analyses
                WHERE id = ?
                """,
                (str(analysis_id),),
            )

            connection.commit()

            if cursor.rowcount == 0:
                raise ValueError(
                    f"Analysis '{analysis_id}' not found."
                )

        finally:
            connection.close()

    @staticmethod
    def _row_to_model(row) -> Analysis:
        return Analysis(
            id=UUID(row["id"]),
            project_id=UUID(row["project_id"]),
            dataset_version_id=UUID(row["dataset_version_id"]),
            analysis_type=row["analysis_type"],
            status=row["status"],
            parameters=json.loads(row["parameters"]),
            result_path=row["result_path"],
            created_at=datetime.fromisoformat(row["created_at"]),
            started_at=(
                datetime.fromisoformat(row["started_at"])
                if row["started_at"]
                else None
            ),
            completed_at=(
                datetime.fromisoformat(row["completed_at"])
                if row["completed_at"]
                else None
            ),
        )
