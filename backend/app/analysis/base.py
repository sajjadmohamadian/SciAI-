from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID


class AnalysisEngine(ABC):
    """
    Base interface for all SciAI analysis engines.
    """

    name: str = "base"
    version: str = "0.1.0"

    @abstractmethod
    def analyze(
        self,
        dataset_version_id: UUID,
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Execute an analysis on a dataset version.
        """
        raise NotImplementedError