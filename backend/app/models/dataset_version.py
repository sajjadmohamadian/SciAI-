from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class DatasetVersion(BaseModel):
    """Versioned representation of a SciAI dataset."""

    id: UUID = Field(default_factory=uuid4)
    dataset_id: UUID
    version: int = Field(default=1, ge=1)
    record_count: int = Field(default=0, ge=0)
    processing_status: str = "raw"
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )