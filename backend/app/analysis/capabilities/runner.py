from pathlib import Path
from typing import Any

from backend.app.analysis.capabilities.resolver import resolver


class CapabilityRunner:
    """
    Executes a registered SciAI capability through its resolved provider.

    The runner does not know implementation details of individual
    providers. It only resolves a capability and invokes the provider's
    registered implementation.
    """

    def execute(
        self,
        capability: str,
        file_path: str | Path,
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        parameters = parameters or {}

        provider = resolver.resolve(capability)

        if provider.implementation is None:
            raise RuntimeError(
                f"Provider '{provider.name}' has no implementation "
                f"for capability '{capability}'."
            )

        implementation = provider.implementation

        result = implementation(
            file_path=file_path,
            parameters=parameters,
        )

        if not isinstance(result, dict):
            raise RuntimeError(
                f"Provider '{provider.name}' returned an invalid result "
                f"for capability '{capability}'. Expected dict, "
                f"got {type(result).__name__}."
            )

        result.setdefault("capability", capability)
        result.setdefault("provider", provider.name)
        result.setdefault("package", provider.package)
        result.setdefault("package_version", provider.version)
        result.setdefault("parameters", parameters)

        return result


runner = CapabilityRunner()