from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.db.repositories.analysis import AnalysisRepository
from backend.app.db.repositories.dataset import DatasetRepository
from backend.app.db.repositories.project import ProjectRepository
from backend.app.models.project import Project


router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
)

project_repository = ProjectRepository()
dataset_repository = DatasetRepository()
analysis_repository = AnalysisRepository()


class ProjectCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None


@router.get("")
def list_projects() -> dict[str, Any]:
    """
    Return all projects.
    """
    projects = project_repository.list()

    return {
        "count": len(projects),
        "projects": [
            {
                "id": str(project.id),
                "name": project.name,
                "description": project.description,
                "status": project.status,
                "created_at": project.created_at,
                "updated_at": project.updated_at,
            }
            for project in projects
        ],
    }


@router.get("/{project_id}/overview")
def get_project_overview(project_id: UUID) -> dict[str, Any]:
    """
    Return an aggregated overview of a project for dashboard use.
    """
    project = project_repository.get(project_id)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail=f"Project '{project_id}' not found.",
        )

    datasets = dataset_repository.list(project_id)
    analyses = analysis_repository.list(project_id)

    completed_count = sum(
        1
        for analysis in analyses
        if analysis.status == "completed"
    )

    pending_count = sum(
        1
        for analysis in analyses
        if analysis.status == "pending"
    )

    running_count = sum(
        1
        for analysis in analyses
        if analysis.status == "running"
    )

    failed_count = sum(
        1
        for analysis in analyses
        if analysis.status == "failed"
    )

    return {
        "project": {
            "id": str(project.id),
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
        },
        "statistics": {
            "dataset_count": len(datasets),
            "analysis_count": len(analyses),
            "completed_analysis_count": completed_count,
            "pending_analysis_count": pending_count,
            "running_analysis_count": running_count,
            "failed_analysis_count": failed_count,
            "total_records": sum(
                dataset.record_count
                for dataset in datasets
            ),
        },
        "latest_datasets": [
            {
                "id": str(dataset.id),
                "name": dataset.name,
                "source": dataset.source,
                "format": dataset.format,
                "record_count": dataset.record_count,
                "created_at": dataset.created_at,
            }
            for dataset in datasets[:5]
        ],
        "latest_analyses": [
            {
                "id": str(analysis.id),
                "dataset_version_id": str(
                    analysis.dataset_version_id
                ),
                "analysis_type": analysis.analysis_type,
                "status": analysis.status,
                "result_path": analysis.result_path,
                "created_at": analysis.created_at,
                "started_at": analysis.started_at,
                "completed_at": analysis.completed_at,
            }
            for analysis in analyses[:5]
        ],
    }


@router.get("/{project_id}/dashboard")
def get_project_dashboard(project_id: UUID) -> dict[str, Any]:
    """
    Return dashboard-ready data for a project.
    """
    project = project_repository.get(project_id)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail=f"Project '{project_id}' not found.",
        )

    datasets = dataset_repository.list(project_id)
    analyses = analysis_repository.list(project_id)

    completed_count = sum(
        analysis.status == "completed"
        for analysis in analyses
    )

    pending_count = sum(
        analysis.status == "pending"
        for analysis in analyses
    )

    running_count = sum(
        analysis.status == "running"
        for analysis in analyses
    )

    failed_count = sum(
        analysis.status == "failed"
        for analysis in analyses
    )

    return {
        "project": {
            "id": str(project.id),
            "name": project.name,
            "description": project.description,
            "status": project.status,
        },
        "kpis": {
            "datasets": len(datasets),
            "analyses": len(analyses),
            "completed": completed_count,
            "pending": pending_count,
            "running": running_count,
            "failed": failed_count,
            "records": sum(
                dataset.record_count
                for dataset in datasets
            ),
        },
        "datasets": [
            {
                "id": str(dataset.id),
                "name": dataset.name,
                "source": dataset.source,
                "format": dataset.format,
                "record_count": dataset.record_count,
                "created_at": dataset.created_at,
            }
            for dataset in datasets[:10]
        ],
        "analyses": [
            {
                "id": str(analysis.id),
                "dataset_version_id": str(
                    analysis.dataset_version_id
                ),
                "analysis_type": analysis.analysis_type,
                "status": analysis.status,
                "created_at": analysis.created_at,
                "completed_at": analysis.completed_at,
            }
            for analysis in analyses[:10]
        ],
    }


@router.get("/{project_id}")
def get_project(project_id: UUID) -> dict[str, Any]:
    """
    Return a single project.
    """
    project = project_repository.get(project_id)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail=f"Project '{project_id}' not found.",
        )

    return {
        "id": str(project.id),
        "name": project.name,
        "description": project.description,
        "status": project.status,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
    }


@router.get("/{project_id}/datasets")
def list_project_datasets(project_id: UUID) -> dict[str, Any]:
    """
    Return all datasets belonging to a project.
    """
    project = project_repository.get(project_id)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail=f"Project '{project_id}' not found.",
        )

    datasets = dataset_repository.list(project_id)

    return {
        "project_id": str(project_id),
        "count": len(datasets),
        "datasets": [
            {
                "id": str(dataset.id),
                "project_id": str(dataset.project_id),
                "name": dataset.name,
                "source": dataset.source,
                "format": dataset.format,
                "record_count": dataset.record_count,
                "created_at": dataset.created_at,
            }
            for dataset in datasets
        ],
    }


@router.get("/{project_id}/analyses")
def list_project_analyses(project_id: UUID) -> dict[str, Any]:
    """
    Return all analyses belonging to a project.
    """
    project = project_repository.get(project_id)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail=f"Project '{project_id}' not found.",
        )

    analyses = analysis_repository.list(project_id)

    return {
        "project_id": str(project_id),
        "count": len(analyses),
        "analyses": [
            {
                "id": str(analysis.id),
                "project_id": str(analysis.project_id),
                "dataset_version_id": str(analysis.dataset_version_id),
                "analysis_type": analysis.analysis_type,
                "status": analysis.status,
                "parameters": analysis.parameters,
                "result_path": analysis.result_path,
                "created_at": analysis.created_at,
                "started_at": analysis.started_at,
                "completed_at": analysis.completed_at,
            }
            for analysis in analyses
        ],
    }


@router.post("")
def create_project(
    request: ProjectCreateRequest,
) -> dict[str, Any]:
    """
    Create a new project.
    """
    project = Project(
        name=request.name,
        description=request.description,
    )

    project = project_repository.create(project)

    return {
        "id": str(project.id),
        "name": project.name,
        "description": project.description,
        "status": project.status,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
    }


@router.put("/{project_id}")
def update_project(
    project_id: UUID,
    request: ProjectCreateRequest,
) -> dict[str, Any]:
    """
    Update an existing project.
    """
    project = project_repository.get(project_id)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail=f"Project '{project_id}' not found.",
        )

    project.name = request.name
    project.description = request.description

    project = project_repository.update(project)

    return {
        "id": str(project.id),
        "name": project.name,
        "description": project.description,
        "status": project.status,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
    }


@router.delete("/{project_id}")
def delete_project(project_id: UUID) -> dict[str, Any]:
    """
    Delete a project.
    """
    deleted = project_repository.delete(project_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Project '{project_id}' not found.",
        )

    return {
        "deleted": True,
        "project_id": str(project_id),
    }