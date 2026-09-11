from backend.app.analysis.capabilities.models import (
    Capability,
    Provider,
)


class CapabilityRegistry:
    """
    Central registry of SciAI capabilities and their providers.
    """

    def __init__(self) -> None:
        self._capabilities: dict[str, Capability] = {}
        self._providers: dict[str, list[Provider]] = {}

    def register_capability(
        self,
        capability: Capability,
    ) -> None:
        if not capability.name:
            raise ValueError(
                "Capability name must not be empty."
            )

        if capability.name in self._capabilities:
            raise ValueError(
                f"Capability '{capability.name}' "
                "is already registered."
            )

        self._capabilities[capability.name] = capability
        self._providers.setdefault(
            capability.name,
            [],
        )

    def register_provider(
        self,
        provider: Provider,
    ) -> None:
        if provider.capability not in self._capabilities:
            raise ValueError(
                f"Capability '{provider.capability}' "
                "is not registered."
            )

        providers = self._providers[
            provider.capability
        ]

        if any(
            existing.name == provider.name
            and existing.package == provider.package
            for existing in providers
        ):
            raise ValueError(
                f"Provider '{provider.name}' "
                f"from package '{provider.package}' "
                f"is already registered for "
                f"capability '{provider.capability}'."
            )

        providers.append(provider)

        providers.sort(
            key=lambda item: item.priority
        )

    def get_capability(
        self,
        name: str,
    ) -> Capability:
        try:
            return self._capabilities[name]
        except KeyError:
            raise KeyError(
                f"Capability '{name}' is not registered."
            ) from None

    def get_providers(
        self,
        capability: str,
    ) -> list[Provider]:
        if capability not in self._capabilities:
            raise KeyError(
                f"Capability '{capability}' "
                "is not registered."
            )

        return list(
            self._providers.get(
                capability,
                [],
            )
        )

    def list_capabilities(self) -> list[str]:
        return sorted(
            self._capabilities.keys()
        )

    def list_providers(
        self,
        capability: str,
    ) -> list[dict]:
        return [
            {
                "name": provider.name,
                "package": provider.package,
                "version": provider.version,
                "capability": provider.capability,
                "priority": provider.priority,
                "available": provider.is_available(),
                "metadata": provider.metadata,
            }
            for provider in self.get_providers(
                capability
            )
        ]


capability_registry = CapabilityRegistry()