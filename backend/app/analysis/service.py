from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from backend.app.analysis.capabilities.runner import runner
from backend.app.analysis.capabilities.setup import setup_capability_registry
from backend.app.analysis.registry import registry
from backend.app.analysis.registry_setup import setup_analysis_registry
from backend.app.db.repositories.analysis import AnalysisRepository
from backend.app.db.repositories.dataset_version import DatasetVersionRepository
from backend.app.models.analysis import Analysis


class AnalysisService:
    """Application service for creating and executing analyses."""

    def __init__(self) -> None:
        setup_analysis_registry()
        setup_capability_registry()

        self.analysis_repository = AnalysisRepository()
        self.dataset_version_repository = DatasetVersionRepository()

    def create(
        self,
        project_id: UUID,
        dataset_version_id: UUID,
        analysis_type: str = "pybibx",
        parameters: dict | None = None,
    ) -> Analysis:

        dataset_version = self.dataset_version_repository.get(
            dataset_version_id
        )

        if dataset_version is None:
            raise ValueError(
                f"Dataset version '{dataset_version_id}' not found."
            )

        parameters = parameters or {}

        # New Capability-based analysis
        from backend.app.analysis.capabilities.registry import (
            capability_registry,
        )

        if analysis_type in capability_registry.list_capabilities():
            pass

        # Legacy Engine-based analysis
        else:
            try:
                registry.get(analysis_type)
            except KeyError as exc:
                raise ValueError(str(exc)) from exc

        analysis = Analysis(
            project_id=project_id,
            dataset_version_id=dataset_version_id,
            analysis_type=analysis_type,
            status="pending",
            parameters=parameters,
        )

        return self.analysis_repository.create(analysis)

    def run(self, analysis_id: UUID) -> dict:

        analysis = self.analysis_repository.get(analysis_id)

        if analysis is None:
            raise ValueError(
                f"Analysis '{analysis_id}' not found."
            )

        dataset_version = self.dataset_version_repository.get(
            analysis.dataset_version_id
        )

        if dataset_version is None:
            raise ValueError(
                f"Dataset version '{analysis.dataset_version_id}' not found."
            )

        analysis.status = "running"
        analysis.started_at = datetime.now(timezone.utc)
        self.analysis_repository.update(analysis)

        try:
            from backend.app.analysis.capabilities.registry import (
                capability_registry,
            )

            analysis_type = analysis.analysis_type

            # ==========================================================
            # NEW CAPABILITY-BASED EXECUTION
            # ==========================================================

            if analysis_type in capability_registry.list_capabilities():

                provider = None

                # Resolve provider first so we can expose provenance.
                from backend.app.analysis.capabilities.resolver import resolver

                provider = resolver.resolve(analysis_type)

                if not dataset_version.storage_path:
                    raise ValueError(
                        "Dataset version does not have a storage path."
                    )

                result = runner.execute(
                    capability=analysis_type,
                    file_path=dataset_version.storage_path,
                    parameters=analysis.parameters,
                )

                # Store tabular records when available.
                result_path = None

                records = result.get("records")

                if isinstance(records, list) and records:
                    result_dir = Path(
                        "data",
                        "projects",
                        "results",
                        str(analysis.id),
                    )

                    result_dir.mkdir(
                        parents=True,
                        exist_ok=True,
                    )

                    result_file = (
                        result_dir
                        / f"{analysis_type.replace('.', '_')}.csv"
                    )

                    import pandas as pd

                    pd.DataFrame(records).to_csv(
                        result_file,
                        index=False,
                        encoding="utf-8-sig",
                    )

                    result_path = str(result_file)
                    analysis.result_path = result_path

                analysis.status = "completed"
                analysis.completed_at = datetime.now(timezone.utc)

                self.analysis_repository.update(analysis)

                return {
                    "analysis_id": str(analysis.id),
                    "status": analysis.status,
                    "analysis_type": analysis_type,
                    "capability": analysis_type,
                    "provider": provider.name,
                    "package": provider.package,
                    "package_version": provider.version,
                    "dataset_version_id": str(
                        analysis.dataset_version_id
                    ),
                    "result": result,
                    "result_path": result_path,
                }

            # ==========================================================
            # LEGACY ENGINE-BASED EXECUTION
            # ==========================================================

            engine_name = analysis.analysis_type

            try:
                engine_class = registry.get(engine_name)
            except KeyError as exc:
                raise ValueError(str(exc)) from exc

            engine = engine_class()

            result = engine.analyze(
                dataset_version_id=analysis.dataset_version_id,
                parameters=analysis.parameters,
            )

            if result.get("result_path"):
                analysis.result_path = result["result_path"]

            analysis.status = "completed"
            analysis.completed_at = datetime.now(timezone.utc)

            self.analysis_repository.update(analysis)

            return {
                "analysis_id": str(analysis.id),
                "status": analysis.status,
                "engine": engine.name,
                "engine_version": engine.version,
                "dataset_version_id": str(
                    analysis.dataset_version_id
                ),
                "result": result,
            }

        except Exception:
            analysis.status = "failed"
            analysis.completed_at = datetime.now(timezone.utc)

            self.analysis_repository.update(analysis)

            raise