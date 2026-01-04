"""Campaign model."""

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import Field

from .base import ArtifactMetadata, BaseArtifact


class Campaign(BaseArtifact):
    """Campaign artifact representing a game world."""

    name: str = Field(..., min_length=1)
    rule_system: str = Field(..., min_length=1)  # e.g., "shadowdark", "dnd5e"
    status: Literal["draft", "active", "completed", "archived"] = Field(default="draft")
    description: Optional[str] = None
    created_by: Optional[str] = None
    active_module_id: Optional[str] = None  # ID of currently active session module

    def model_post_init(self, __context: Any) -> None:
        """Update metadata after initialization."""
        if not self.metadata.created_at:
            self.metadata.created_at = datetime.utcnow()
        if not self.metadata.updated_at:
            self.metadata.updated_at = datetime.utcnow()
