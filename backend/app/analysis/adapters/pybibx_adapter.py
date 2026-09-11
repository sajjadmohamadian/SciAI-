from pathlib import Path
from typing import Any
from uuid import UUID

from backend.app.analysis.base import AnalysisEngine
from backend.app.db.repositories.dataset_version import (
    DatasetVersionRepository,
)
from backend.app.services.pybibx_service import PyBibXService


class PyBibXAdapter(AnalysisEngine):

    name = "pybibx"
    version = "0.1.0"

    description = (
        "Selected bibliometric and text-analysis capabilities "
        "implemented using PyBibX components."
    )

    capabilities = [
        "bibliographic_processing",
        "descriptive_statistics",
        "keyword_analysis",
        "text_analysis",
        "topic_modeling",
        "semantic_analysis",
        "citation_analysis",
        "coauthor_analysis",
    ]

    providers = [
        "pyBibX",
        "Sentence-BERT",
        "BERTopic",
        "KeyBERT",
    ]

    def __init__(self) -> None:
        self.dataset_version_repository = DatasetVersionRepository()
        self.pybibx_service = PyBibXService()

    def analyze(
        self,
        dataset_version_id: UUID,
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        parameters = parameters or {}

        dataset_version = self.dataset_version_repository.get(
            dataset_version_id
        )

        if dataset_version is None:
            raise ValueError(
                f"Dataset version '{dataset_version_id}' not found."
            )

        result = self.pybibx_service.run(
            dataset_version,
            parameters=parameters,
        )

        result_dir = Path(
            "data",
            "projects",
            "results",
            str(dataset_version_id),
        )

        result_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        result_file = result_dir / "pybibx_records.csv"

        result.data.to_csv(
            result_file,
            index=False,
            encoding="utf-8-sig",
        )

        return {
            "status": "completed",
            "engine": self.name,
            "version": self.version,
            "dataset_version_id": str(dataset_version_id),
            "rows": int(result.data.shape[0]),
            "columns": int(result.data.shape[1]),
            "column_names": list(result.data.columns),
            "result_path": str(result_file),
            "parameters": parameters,
        }