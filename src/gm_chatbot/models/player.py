"""Player model."""

from datetime import datetime, timezone
from typing import Any, Literal, Optional

from pydantic import Field

from .base import ArtifactMetadata, BaseArtifact


class Player(BaseArtifact):
    """Player artifact representing a real human user."""

    username: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    status: Literal["online", "offline", "away"] = Field(default="offline")

    def model_post_init(self, __context: Any) -> None:
        """Update metadata after initialization."""
        if not self.metadata.created_at:
            self.metadata.created_at = datetime.now(timezone.utc)
        if not self.metadata.updated_at:
            self.metadata.updated_at = datetime.now(timezone.utc)
