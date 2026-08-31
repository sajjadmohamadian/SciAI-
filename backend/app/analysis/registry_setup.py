from backend.app.analysis.adapters.pybibx_adapter import PyBibXAdapter
from backend.app.analysis.registry import registry


def setup_analysis_registry() -> None:
    """
    Register all available SciAI analysis engines.
    """
    if "pybibx" not in registry.list():
        registry.register(PyBibXAdapter)