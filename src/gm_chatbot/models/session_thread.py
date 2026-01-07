"""Session thread model for tracking Discord thread mappings."""

from datetime import UTC, datetime
from typing import Any

from pydantic import Field

from .base import BaseArtifact


class SessionThread(BaseArtifact):
    """Session thread artifact tracking Discord thread mappings for sessions."""

    session_id: str = Field(..., min_length=1)
    thread_id: str = Field(..., min_length=1)  # Discord snowflake
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    archived_at: datetime | None = None

    def model_post_init(self, __context: Any) -> None:
        """Update metadata after initialization."""
        if not self.metadata.created_at:
            self.metadata.created_at = datetime.now(UTC)
        if not self.metadata.updated_at:
            self.metadata.updated_at = datetime.now(UTC)
