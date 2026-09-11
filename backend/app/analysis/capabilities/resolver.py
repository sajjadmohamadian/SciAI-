from backend.app.analysis.capabilities.models import Provider
from backend.app.analysis.capabilities.registry import (
    capability_registry,
)


class CapabilityResolver:
    """
    Resolves a SciAI capability to the best available provider.
    """

    def __init__(self) -> None:
        self.registry = capability_registry

    def resolve(
        self,
        capability: str,
    ) -> Provider:
        providers = self.registry.get_providers(
            capability
        )

        available = [
            provider
            for provider in providers
            if provider.is_available()
        ]

        if not available:
            raise RuntimeError(
                f"No available provider found "
                f"for capability '{capability}'."
            )

        return available[0]

    def resolve_all(
        self,
        capability: str,
    ) -> list[Provider]:
        providers = self.registry.get_providers(
            capability
        )

        return [
            provider
            for provider in providers
            if provider.is_available()
        ]


resolver = CapabilityResolver()