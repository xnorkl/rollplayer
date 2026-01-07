"""Discord binding model for binding campaigns to Discord channels."""

from datetime import UTC, datetime
from typing import Any

from pydantic import Field

from .base import BaseArtifact


class DiscordBinding(BaseArtifact):
    """Discord binding artifact binding a campaign to a Discord channel."""

    campaign_id: str = Field(..., min_length=1)
    guild_id: str = Field(..., min_length=1)  # Discord snowflake
    channel_id: str = Field(..., min_length=1)  # Discord snowflake
    channel_name: str = Field(..., min_length=1)
    bound_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    bound_by: str = Field(..., min_length=1)  # player_id
    settings: dict = Field(
        default_factory=lambda: {
            "auto_create_session_threads": True,
            "dice_roll_visibility": "public",
            "allow_spectators": True,
        }
    )

    def model_post_init(self, __context: Any) -> None:
        """Update metadata after initialization."""
        if not self.metadata.created_at:
            self.metadata.created_at = datetime.now(UTC)
        if not self.metadata.updated_at:
            self.metadata.updated_at = datetime.now(UTC)
