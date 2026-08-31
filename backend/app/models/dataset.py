from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Dataset(BaseModel):
    """Dataset model for SciAI."""

    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    name: str = Field(min_length=1, max_length=200)
    source: str = Field(min_length=1, max_length=100)
    format: str = Field(min_length=1, max_length=50)
    record_count: int = Field(default=0, ge=0)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )