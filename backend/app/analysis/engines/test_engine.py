from typing import Any
from uuid import UUID

from backend.app.analysis.base import AnalysisEngine


class TestAnalysisEngine(AnalysisEngine):
    """
    Simple test engine used to verify the SciAI analysis registry.
    """

    name = "test"
    version = "0.1.0"

    def analyze(
        self,
        dataset_version_id: UUID,
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "status": "completed",
            "engine": self.name,
            "version": self.version,
            "dataset_version_id": str(dataset_version_id),
            "parameters": parameters or {},
        }