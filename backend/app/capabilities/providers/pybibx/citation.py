from typing import Any

from backend.app.capabilities.base import CapabilityProvider


class PyBibXCitationProvider(CapabilityProvider):
    """
    Citation metrics provider backed by PyBibX.
    """

    provider_id = "pybibx.citation"
    package = "pybibx"
    package_version = "0.1.0"

    def execute(
        self,
        capability_id: str,
        data: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Execute a PyBibX citation capability.

        The actual PyBibX function will be connected here
        after verifying the installed package API.
        """

        raise NotImplementedError(
            f"PyBibX implementation for "
            f"'{capability_id}' has not been connected yet."
        )