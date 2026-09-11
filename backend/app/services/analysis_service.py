from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from backend.app.db.repositories.analysis import AnalysisRepository
from backend.app.models.analysis import Analysis
from backend.app.models.dataset_version import DatasetVersion
from backend.app.services.pybibx_service import PyBibXService


class AnalysisService:
    def __init__(self):
        self.repository = AnalysisRepository()
        self.pybibx = PyBibXService()

    def create(
        self,
        project_id: UUID,
        dataset_version_id: UUID,
        analysis_type: str = "pybibx",
        parameters: dict | None = None,
        result_path: str | None = None,
    ) -> Analysis:

        analysis = Analysis(
            project_id=project_id,
            dataset_version_id=dataset_version_id,
            analysis_type=analysis_type,
            status="pending",
            parameters=parameters or {},
            result_path=result_path,
        )

        return self.repository.create(analysis)

    def run(
        self,
        analysis: Analysis,
        dataset_version: DatasetVersion,
    ) -> Analysis:

        analysis.status = "running"
        analysis.started_at = datetime.now(timezone.utc)
        self.repository.update(analysis)

        try:
            if analysis.analysis_type != "pybibx":
                raise ValueError(
                    f"Unsupported analysis type: {analysis.analysis_type}"
                )

            result = self.pybibx.run(dataset_version)

            base_path = Path(
                analysis.result_path
                or f"data/projects/results/{analysis.project_id}"
            )

            base_path.mkdir(parents=True, exist_ok=True)

            output_file = base_path / f"{analysis.id}_records.csv"

            result.data.to_csv(
                output_file,
                index=False,
                encoding="utf-8-sig",
            )

            analysis.result_path = str(output_file)
            analysis.status = "completed"
            analysis.completed_at = datetime.now(timezone.utc)

        except Exception:
            analysis.status = "failed"
            analysis.completed_at = datetime.now(timezone.utc)
            self.repository.update(analysis)
            raise

        self.repository.update(analysis)

        return analysis