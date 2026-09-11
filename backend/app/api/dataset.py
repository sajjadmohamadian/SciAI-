from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from backend.app.db.repositories.dataset import DatasetRepository
from backend.app.db.repositories.dataset_version import DatasetVersionRepository
from backend.app.services.dataset_service import DatasetService


router = APIRouter(
    prefix="/datasets",
    tags=["Datasets"],
)

dataset_service = DatasetService()
dataset_repository = DatasetRepository()
dataset_version_repository = DatasetVersionRepository()


@router.post("/upload")
async def upload_dataset(
    project_id: UUID = Form(...),
    name: str = Form(...),
    source: str = Form(...),
    record_count: int = Form(0),
    file: UploadFile = File(...),
) -> dict[str, Any]:
    """
    Upload a dataset file and create Dataset and DatasetVersion.
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file must have a filename.",
        )

    upload_dir = Path("data/projects/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_filename = Path(file.filename).name
    destination = upload_dir / safe_filename

    try:
        contents = await file.read()
        destination.write_bytes(contents)

        dataset, version = dataset_service.create_dataset(
            project_id=project_id,
            name=name,
            source=source,
            file_path=str(destination),
            record_count=record_count,
        )

        return {
            "dataset": {
                "id": str(dataset.id),
                "project_id": str(dataset.project_id),
                "name": dataset.name,
                "source": dataset.source,
                "format": dataset.format,
                "record_count": dataset.record_count,
            },
            "version": {
                "id": str(version.id),
                "dataset_id": str(version.dataset_id),
                "version": version.version,
                "record_count": version.record_count,
                "processing_status": version.processing_status,
                "storage_path": version.storage_path,
            },
            "file": {
                "filename": safe_filename,
                "content_type": file.content_type,
                "size": len(contents),
            },
        }

    except ValueError as exc:
        if destination.exists():
            destination.unlink()

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception:
        if destination.exists():
            destination.unlink()

        raise


@router.get("")
def list_datasets(
    project_id: UUID | None = None,
) -> dict[str, Any]:
    """
    Return datasets, optionally filtered by project.
    """

    datasets = dataset_repository.list(project_id)

    return {
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


@router.get("/{dataset_id}")
def get_dataset(
    dataset_id: UUID,
) -> dict[str, Any]:
    """
    Return a single dataset.
    """

    dataset = dataset_repository.get(dataset_id)

    if dataset is None:
        raise HTTPException(
            status_code=404,
            detail=f"Dataset '{dataset_id}' not found.",
        )

    return {
        "id": str(dataset.id),
        "project_id": str(dataset.project_id),
        "name": dataset.name,
        "source": dataset.source,
        "format": dataset.format,
        "record_count": dataset.record_count,
        "created_at": dataset.created_at,
    }


@router.get("/{dataset_id}/versions")
def list_dataset_versions(
    dataset_id: UUID,
) -> dict[str, Any]:
    """
    Return all versions of a dataset.
    """

    dataset = dataset_repository.get(dataset_id)

    if dataset is None:
        raise HTTPException(
            status_code=404,
            detail=f"Dataset '{dataset_id}' not found.",
        )

    versions = dataset_version_repository.list(dataset_id)

    return {
        "dataset_id": str(dataset_id),
        "count": len(versions),
        "versions": [
            {
                "id": str(version.id),
                "dataset_id": str(version.dataset_id),
                "version": version.version,
                "record_count": version.record_count,
                "processing_status": version.processing_status,
                "storage_path": version.storage_path,
                "created_at": version.created_at,
            }
            for version in versions
        ],
    }