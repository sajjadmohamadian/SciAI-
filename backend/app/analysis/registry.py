from typing import Type

from backend.app.analysis.base import AnalysisEngine


class AnalysisRegistry:
    """
    Central registry for SciAI analysis engines.
    """

    def __init__(self) -> None:
        self._engines: dict[str, Type[AnalysisEngine]] = {}

    def register(self, engine: Type[AnalysisEngine]) -> None:
        """
        Register an analysis engine.
        """
        if not engine.name:
            raise ValueError("Analysis engine must have a name.")

        if engine.name in self._engines:
            raise ValueError(
                f"Analysis engine '{engine.name}' is already registered."
            )

        self._engines[engine.name] = engine

    def get(self, name: str) -> Type[AnalysisEngine]:
        """
        Get an analysis engine by name.
        """
        try:
            return self._engines[name]
        except KeyError:
            raise KeyError(
                f"Analysis engine '{name}' is not registered."
            ) from None

    def list(self) -> list[str]:
        """
        Return registered analysis engine names.
        """
        return sorted(self._engines.keys())


registry = AnalysisRegistry()