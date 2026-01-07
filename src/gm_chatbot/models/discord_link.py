"""Discord link model for linking Discord users to players."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from .base import BaseArtifact


class GuildInfo(BaseModel):
    """Information about a Discord guild (server) where a user is linked."""

    guild_id: str = Field(..., min_length=1)
    guild_name: str = Field(..., min_length=1)
    joined_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DiscordLink(BaseArtifact):
    """Discord link artifact linking a Discord user to a GM Chatbot player."""

    player_id: str = Field(..., min_length=1)
    discord_user_id: str = Field(..., min_length=1)  # Discord snowflake
    discord_username: str = Field(..., min_length=1)
    linked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    guilds: list[GuildInfo] = Field(default_factory=list)  # List of guild info

    def model_post_init(self, __context: Any) -> None:
        """Update metadata after initialization."""
        if not self.metadata.created_at:
            self.metadata.created_at = datetime.now(UTC)
        if not self.metadata.updated_at:
            self.metadata.updated_at = datetime.now(UTC)
