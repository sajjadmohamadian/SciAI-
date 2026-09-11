from backend.app.analysis.capabilities import Capability, Provider
from backend.app.analysis.capabilities.registry import capability_registry
from backend.app.analysis.providers.pybibx_provider import PyBibXProvider
from backend.app.analysis.providers.scientometric_provider import (
    SciAINativeProvider,
)


def setup_capability_registry() -> None:

    capabilities = {
        "citation.author_h_index": (
            "Calculate author-level H-index.",
            "PyBibX",
            "5.9.5",
        ),
        "document.count": (
            "Count documents in the dataset.",
            "SciAI Native",
            "1.0.0",
        ),
        "publication.year_distribution": (
            "Calculate publication counts by year.",
            "SciAI Native",
            "1.0.0",
        ),
        "author.productivity": (
            "Calculate publication productivity by author.",
            "SciAI Native",
            "1.0.0",
        ),
        "citation.total": (
            "Calculate total citations.",
            "SciAI Native",
            "1.0.0",
        ),
        "citation.average": (
            "Calculate average citations per document.",
            "SciAI Native",
            "1.0.0",
        ),
        "citation.distribution": (
            "Calculate citation frequency distribution.",
            "SciAI Native",
            "1.0.0",
        ),
        "source.productivity": (
            "Calculate document productivity by source.",
            "SciAI Native",
            "1.0.0",
        ),
        "keyword.frequency": (
            "Calculate keyword frequencies.",
            "SciAI Native",
            "1.0.0",
        ),
        "author.co_authorship": (
            "Calculate author co-authorship network edges.",
            "SciAI Native",
            "1.0.0",
        ),
    }

    for name, (
        description,
        provider_name,
        version,
    ) in capabilities.items():

        if name not in capability_registry.list_capabilities():
            capability_registry.register_capability(
                Capability(
                    name=name,
                    description=description,
                )
            )

        existing = capability_registry.get_providers(name)

        if any(
            p.name == provider_name
            and p.package == provider_name
            for p in existing
        ):
            continue

        if name == "citation.author_h_index":

            provider = PyBibXProvider()

            implementation = provider.calculate

            metadata = {
                "level": "author",
                "input_formats": [
                    "csv",
                    "bib",
                    "txt",
                ],
                "output_fields": [
                    "author",
                    "h_index",
                ],
            }

        else:

            provider = SciAINativeProvider(name)

            implementation = provider.execute

            metadata = {
                "input_formats": [
                    "csv",
                ],
                "output_fields": [
                    "records",
                ],
            }

        capability_registry.register_provider(
            Provider(
                name=provider_name,
                package=provider_name,
                version=version,
                capability=name,
                priority=10,
                implementation=implementation,
                metadata=metadata,
            )
        )