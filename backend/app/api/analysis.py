from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.analysis.registry import registry
from backend.app.analysis.registry_setup import setup_analysis_registry


router = APIRouter(prefix="/analysis", tags=["Analysis"])

setup_analysis_registry()


class AnalysisRequest(BaseModel):
    dataset_version_id: UUID
    engine: str = "pybibx"
    parameters: dict[str, Any] = Field(default_factory=dict)


@router.get("/engines")
def list_analysis_engines() -> dict[str, Any]:
    """
    Return all registered analysis engines.
    """
    return {
        "engines": registry.list(),
    }


@router.post("/run")
def run_analysis(request: AnalysisRequest) -> dict[str, Any]:
    """
    Run an analysis using a registered engine.
    """
    try:
        engine_class = registry.get(request.engine)
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    engine = engine_class()

    return engine.analyze(
        dataset_version_id=request.dataset_version_id,
        parameters=request.parameters,
    )