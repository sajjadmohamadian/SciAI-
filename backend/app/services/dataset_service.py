from pathlib import Path
from uuid import UUID

from backend.app.core.config import get_settings
from backend.app.db.repositories.dataset import DatasetRepository
from backend.app.db.repositories.dataset_version import DatasetVersionRepository
from backend.app.models.dataset import Dataset
from backend.app.models.dataset_version import DatasetVersion


class DatasetService:
    """Application service for creating datasets and dataset versions."""

    def __init__(self) -> None:
        self.dataset_repository = DatasetRepository()
        self.version_repository = DatasetVersionRepository()
        self.settings = get_settings()

    def create_dataset(
        self,
        project_id: UUID,
        name: str,
        source: str,
        file_path: str,
        record_count: int = 0,
    ) -> tuple[Dataset, DatasetVersion]:

        source_path = Path(file_path)

        if not source_path.exists():
            raise ValueError(
                f"Dataset file not found: {source_path}"
            )

        if not source_path.is_file():
            raise ValueError(
                f"Dataset path is not a file: {source_path}"
            )

        dataset = Dataset(
            project_id=project_id,
            name=name,
            source=source,
            format=source_path.suffix.lstrip(".").lower(),
            record_count=record_count,
        )

        dataset = self.dataset_repository.create(dataset)

        version = DatasetVersion(
            dataset_id=dataset.id,
            version=1,
            record_count=record_count,
            processing_status="raw",
            storage_path=str(source_path),
        )

        version = self.version_repository.create(version)

        return dataset, version