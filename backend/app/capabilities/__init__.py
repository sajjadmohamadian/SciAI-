from backend.app.capabilities.models import CapabilityDefinition
from backend.app.capabilities.registry import capability_registry


def setup_capabilities() -> None:
    """
    Register SciAI's core scientific capabilities.
    """

    capabilities = [
        CapabilityDefinition(
            id="citation.h_index",
            name="H-Index",
            category="citation",
            description="Calculate the h-index of a scientific dataset.",
        ),
        CapabilityDefinition(
            id="citation.g_index",
            name="G-Index",
            category="citation",
            description="Calculate the g-index of a scientific dataset.",
        ),
        CapabilityDefinition(
            id="productivity.authors",
            name="Author Productivity",
            category="productivity",
            description="Analyze author productivity and publication output.",
        ),
        CapabilityDefinition(
            id="network.co_authorship",
            name="Co-Authorship Network",
            category="network",
            description="Build and analyze author collaboration networks.",
        ),
        CapabilityDefinition(
            id="network.co_citation",
            name="Co-Citation Network",
            category="network",
            description="Build and analyze co-citation networks.",
        ),
        CapabilityDefinition(
            id="network.bibliographic_coupling",
            name="Bibliographic Coupling",
            category="network",
            description="Analyze bibliographic coupling relationships.",
        ),
        CapabilityDefinition(
            id="network.keyword_cooccurrence",
            name="Keyword Co-Occurrence",
            category="network",
            description="Analyze keyword co-occurrence networks.",
        ),
        CapabilityDefinition(
            id="topic.modeling",
            name="Topic Modeling",
            category="topic",
            description="Discover thematic structures in scientific documents.",
        ),
        CapabilityDefinition(
            id="topic.evolution",
            name="Topic Evolution",
            category="topic",
            description="Analyze thematic evolution over time.",
        ),
        CapabilityDefinition(
            id="comparison.overlap",
            name="Group Overlap",
            category="comparison",
            description="Analyze overlap between bibliographic groups.",
        ),
        CapabilityDefinition(
            id="comparison.bibliogroup",
            name="BiblioGroup Analysis",
            category="comparison",
            description="Perform comparative bibliometric group analysis.",
        ),
        CapabilityDefinition(
            id="citation.rpys",
            name="Reference Publication Year Spectroscopy",
            category="citation",
            description="Detect historical peaks in cited references.",
        ),
        CapabilityDefinition(
            id="data.deduplicate",
            name="Bibliographic Deduplication",
            category="data",
            description="Detect and resolve duplicate bibliographic records.",
        ),
        CapabilityDefinition(
            id="data.smart_merge",
            name="Smart Metadata Merge",
            category="data",
            description="Merge records from multiple bibliographic databases.",
        ),
    ]

    for capability in capabilities:
        if capability.id not in {
            item.id
            for item in capability_registry.list_capabilities()
        }:
            capability_registry.register_capability(
                capability
            )