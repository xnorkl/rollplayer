"""Session model."""

from datetime import datetime, timezone
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from .base import ArtifactMetadata, BaseArtifact


class SessionParticipant(BaseModel):
    """Session participant representing a player's participation in a session."""

    player_id: str = Field(..., min_length=1)
    character_id: Optional[str] = None  # Character being played (nullable for GMs)
    joined_at: datetime = Field(default_factory=datetime.now(timezone.utc))
    left_at: Optional[datetime] = None
    is_gm: bool = Field(default=False)


class Session(BaseArtifact):
    """Session artifact representing an instance of active gameplay for a campaign."""

    campaign_id: str = Field(..., min_length=1)
    session_number: int = Field(..., ge=1)
    name: Optional[str] = None
    status: Literal["active", "paused", "ended"] = Field(default="active")
    started_at: datetime = Field(default_factory=datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None
    started_by: str = Field(..., min_length=1)  # Player ID who initiated the session
    notes: Optional[str] = None
    participants: list[SessionParticipant] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        """Update metadata after initialization."""
        if not self.metadata.created_at:
            self.metadata.created_at = datetime.now(timezone.utc)
        if not self.metadata.updated_at:
            self.metadata.updated_at = datetime.now(timezone.utc)
