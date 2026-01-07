"""Session model."""

from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, Field

from ..lib.datetime import utc_now
from ..lib.types import UTC_DATETIME, SessionStatus
from .base import BaseArtifact


class SessionParticipant(BaseModel):
    """Session participant representing a player's participation in a session."""

    player_id: str = Field(..., min_length=1)
    character_id: str | None = None  # Character being played (nullable for GMs)
    joined_at: UTC_DATETIME = Field(default_factory=utc_now)
    left_at: UTC_DATETIME | None = None
    is_gm: bool = Field(default=False)


def _validate_session_status(v: SessionStatus | str) -> SessionStatus:
    """Convert string to SessionStatus enum."""
    if isinstance(v, str):
        return SessionStatus(v)
    return v


class Session(BaseArtifact):
    """Session artifact representing an instance of active gameplay for a campaign."""

    campaign_id: str = Field(..., min_length=1)
    session_number: int = Field(..., ge=1)
    name: str | None = None
    status: Annotated[SessionStatus, BeforeValidator(_validate_session_status)] = Field(
        default=SessionStatus.ACTIVE
    )
    started_at: UTC_DATETIME = Field(default_factory=utc_now)
    ended_at: UTC_DATETIME | None = None
    started_by: str = Field(..., min_length=1)  # Player ID who initiated the session
    notes: str | None = None
    participants: list[SessionParticipant] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        """Update metadata after initialization."""
        # Metadata timestamps are handled by ArtifactMetadata defaults
        pass
