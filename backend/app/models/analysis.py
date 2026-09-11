from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Analysis(BaseModel):
    """Analysis job/model for SciAI."""

    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    dataset_version_id: UUID
    analysis_type: str = Field(min_length=1, max_length=100)
    status: str = "pending"
    parameters: dict = Field(default_factory=dict)
    result_path: str | None = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    started_at: datetime | None = None
    completed_at: datetime | None = None