"""Campaign membership model."""

from datetime import datetime, timezone
from typing import Any, Literal, Optional

from pydantic import Field

from .base import ArtifactMetadata, BaseArtifact


class CampaignMembership(BaseArtifact):
    """Campaign membership artifact representing a player's relationship to a campaign."""

    player_id: str = Field(..., min_length=1)
    campaign_id: str = Field(..., min_length=1)
    role: Literal["player", "gm", "spectator"] = Field(default="player")
    character_id: Optional[str] = None  # Default character this player controls
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def model_post_init(self, __context: Any) -> None:
        """Update metadata after initialization."""
        if not self.metadata.created_at:
            self.metadata.created_at = datetime.now(timezone.utc)
        if not self.metadata.updated_at:
            self.metadata.updated_at = datetime.now(timezone.utc)
