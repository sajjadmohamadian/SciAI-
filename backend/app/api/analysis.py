from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.analysis.capabilities import capability_registry
from backend.app.analysis.capabilities.setup import setup_capability_registry
from backend.app.analysis.registry import registry
from backend.app.analysis.registry_setup import setup_analysis_registry
from backend.app.analysis.service import AnalysisService
from backend.app.db.repositories.analysis import AnalysisRepository
from backend.app.services.analysis_result_service import AnalysisResultService


router = APIRouter(
    prefix="/analysis",
    tags=["Analysis"],
)

# ---------------------------------------------------------------------------
# Registry setup
# ---------------------------------------------------------------------------

setup_analysis_registry()
setup_capability_registry()


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------

analysis_service = AnalysisService()
result_service = AnalysisResultService()
analysis_repository = AnalysisRepository()


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class AnalysisRequest(BaseModel):
    analysis_id: UUID


class AnalysisCreateRequest(BaseModel):
    project_id: UUID
    dataset_version_id: UUID

    # In the capability-based architecture, analysis_type is
    # the capability name, e.g.:
    # citation.author_h_index
    # publication.year_distribution
    # author.productivity
    analysis_type: str = Field(
        default="citation.author_h_index",
        min_length=1,
        max_length=100,
    )

    parameters: dict[str, Any] = Field(
        default_factory=dict
    )


# ---------------------------------------------------------------------------
# Legacy engine endpoint
# ---------------------------------------------------------------------------

@router.get("/engines")
def list_analysis_engines() -> dict[str, Any]:
    """
    Return metadata for legacy registered analysis engines.

    Kept temporarily for backward compatibility.
    New frontend code should use /analysis/capabilities.
    """
    return {
        "engines": registry.metadata(),
    }


# ---------------------------------------------------------------------------
# Capability endpoint
# ---------------------------------------------------------------------------

@router.get("/capabilities")
def list_analysis_capabilities() -> dict[str, Any]:
    """
    Return all registered analysis capabilities and their providers.
    """

    return {
        "capabilities": [
            {
                "name": capability,
                "providers": capability_registry.list_providers(
                    capability
                ),
            }
            for capability in capability_registry.list_capabilities()
        ]
    }


# ---------------------------------------------------------------------------
# Create analysis
# ---------------------------------------------------------------------------

@router.post("")
def create_analysis(
    request: AnalysisCreateRequest,
) -> dict[str, Any]:
    """
    Create a new analysis.

    analysis_type is treated as a capability name.
    """

    # Validate that the requested capability exists before creating
    # the database analysis record.
    try:
        capability_registry.get_capability(
            request.analysis_type
        )

    except KeyError:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unknown analysis capability: "
                f"'{request.analysis_type}'."
            ),
        ) from None

    try:
        analysis = analysis_service.create(
            project_id=request.project_id,
            dataset_version_id=request.dataset_version_id,
            analysis_type=request.analysis_type,
            parameters=request.parameters,
        )

        return {
            "analysis_id": str(analysis.id),
            "project_id": str(analysis.project_id),
            "dataset_version_id": str(
                analysis.dataset_version_id
            ),
            "analysis_type": analysis.analysis_type,
            "status": analysis.status,
            "parameters": analysis.parameters,
            "created_at": analysis.created_at,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


# ---------------------------------------------------------------------------
# Run analysis
# ---------------------------------------------------------------------------

@router.post("/run")
def run_analysis(
    request: AnalysisRequest,
) -> dict[str, Any]:
    """
    Run an existing analysis.

    AnalysisService is responsible for resolving the capability
    to the appropriate provider.
    """

    try:
        return analysis_service.run(
            request.analysis_id
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


# ---------------------------------------------------------------------------
# Analysis summary
# ---------------------------------------------------------------------------

@router.get("/{analysis_id}")
def get_analysis(
    analysis_id: UUID,
) -> dict[str, Any]:
    """
    Return the summary of an analysis.
    """

    analysis = analysis_repository.get(
        analysis_id
    )

    if analysis is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Analysis '{analysis_id}' not found."
            ),
        )

    return result_service.summary(
        analysis
    )


# ---------------------------------------------------------------------------
# Analysis records
# ---------------------------------------------------------------------------

@router.get("/{analysis_id}/records")
def get_analysis_records(
    analysis_id: UUID,
) -> dict[str, Any]:
    """
    Return analysis result records as JSON.
    """

    analysis = analysis_repository.get(
        analysis_id
    )

    if analysis is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Analysis '{analysis_id}' not found."
            ),
        )

    try:
        data = result_service.read_records(
            analysis
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Result file for analysis "
                f"'{analysis_id}' was not found."
            ),
        ) from None

    return {
        "analysis_id": str(analysis.id),
        "status": analysis.status,
        "rows": int(data.shape[0]),
        "columns": int(data.shape[1]),
        "records": data.to_dict(
            orient="records"
        ),
    }