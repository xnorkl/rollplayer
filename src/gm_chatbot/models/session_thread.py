"""Session thread model for tracking Discord thread mappings."""

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import Field

from .base import ArtifactMetadata, BaseArtifact


class SessionThread(BaseArtifact):
    """Session thread artifact tracking Discord thread mappings for sessions."""

    session_id: str = Field(..., min_length=1)
    thread_id: str = Field(..., min_length=1)  # Discord snowflake
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    archived_at: Optional[datetime] = None

    def model_post_init(self, __context: Any) -> None:
        """Update metadata after initialization."""
        if not self.metadata.created_at:
            self.metadata.created_at = datetime.now(timezone.utc)
        if not self.metadata.updated_at:
            self.metadata.updated_at = datetime.now(timezone.utc)
