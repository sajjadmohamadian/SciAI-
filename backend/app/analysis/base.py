from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID


class AnalysisEngine(ABC):
    """
    Base interface for all SciAI analysis engines.

    Every external analysis package integrated into SciAI
    should implement this interface through an adapter.
    """

    name: str = "base"
    version: str = "0.1.0"
    description: str = ""

    # High-level engine classification.
    # Examples:
    # scientometric, comparative, graph, statistical, review
    engine_type: str = "analysis"

    # Capabilities exposed by this engine.
    capabilities: list[str] = []

    # Supported input data sources/databases.
    supported_databases: list[str] = []

    # Supported analysis categories.
    supported_analysis_types: list[str] = []

    # Execution information.
    execution_mode: str = "local"

    # License of the underlying package.
    # This should be explicitly defined for every external engine.
    license: str = "unknown"

    # Optional schemas describing input/output.
    input_schema: dict[str, Any] = {}
    output_schema: dict[str, Any] = {}

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

    @classmethod
    def metadata(cls) -> dict[str, Any]:
        """
        Return public metadata describing the analysis engine.
        """
        return {
            "name": cls.name,
            "version": cls.version,
            "description": cls.description,
            "type": cls.engine_type,
            "capabilities": list(cls.capabilities),
            "supported_databases": list(cls.supported_databases),
            "supported_analysis_types": list(
                cls.supported_analysis_types
            ),
            "license": cls.license,
            "execution_mode": cls.execution_mode,
            "input_schema": dict(cls.input_schema),
            "output_schema": dict(cls.output_schema),
        }