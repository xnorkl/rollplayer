"""Player model."""

from typing import Annotated, Any

from pydantic import BeforeValidator, Field

from ..lib.types import PlayerStatus
from .base import BaseArtifact


def _validate_player_status(v: PlayerStatus | str) -> PlayerStatus:
    """Convert string to PlayerStatus enum."""
    if isinstance(v, str):
        return PlayerStatus(v)
    return v


class Player(BaseArtifact):
    """Player artifact representing a real human user."""

    username: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    email: str | None = None
    avatar_url: str | None = None
    status: Annotated[PlayerStatus, BeforeValidator(_validate_player_status)] = Field(
        default=PlayerStatus.OFFLINE
    )

    def model_post_init(self, __context: Any) -> None:
        """Update metadata after initialization."""
        # Metadata timestamps are handled by ArtifactMetadata defaults
        pass
