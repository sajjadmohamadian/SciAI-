from typing import Any, List, Type

from backend.app.analysis.base import AnalysisEngine


class AnalysisRegistry:
    """
    Registry of SciAI analytical engines.

    Each registered engine represents a selected analytical
    capability, not an entire external package.
    """

    def __init__(self) -> None:
        self._engines: dict[str, Type[AnalysisEngine]] = {}

    def register(self, engine: Type[AnalysisEngine]) -> None:
        if not engine.name:
            raise ValueError("Analysis engine must have a name.")

        if engine.name in self._engines:
            raise ValueError(
                f"Analysis engine '{engine.name}' is already registered."
            )

        self._engines[engine.name] = engine

    def get(self, name: str) -> Type[AnalysisEngine]:
        try:
            return self._engines[name]
        except KeyError:
            raise KeyError(
                f"Analysis engine '{name}' is not registered."
            ) from None

    def list(self) -> List[str]:
        return sorted(self._engines.keys())

    def metadata(self) -> List[dict[str, Any]]:
        return [
            engine.metadata()
            for engine in self._engines.values()
        ]


registry = AnalysisRegistry()