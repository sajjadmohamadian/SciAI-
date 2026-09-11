from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True)
class Capability:
    """
    A capability exposed by SciAI.

    A capability describes WHAT SciAI can do.
    It does not describe which package performs it.
    """

    name: str
    description: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Provider:
    """
    A concrete implementation provider for a capability.

    A provider describes HOW a capability is implemented.
    """

    name: str
    package: str
    version: str
    capability: str
    priority: int = 100
    implementation: Callable[..., Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_available(self) -> bool:
        return self.implementation is not None