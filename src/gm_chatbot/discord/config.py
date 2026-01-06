"""Discord bot configuration."""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class DiscordConfig:
    """Configuration for Discord bot."""

    bot_token: str
    api_base_url: Optional[str] = None
    rate_limit_commands_per_user: tuple[int, int] = (20, 60)  # 20 commands per 60 seconds
    rate_limit_messages_per_channel: tuple[int, int] = (
        30,
        60,
    )  # 30 messages per 60 seconds
    rate_limit_api_calls_per_guild: tuple[int, int] = (
        100,
        60,
    )  # 100 API calls per 60 seconds

    @classmethod
    def from_env(cls) -> "DiscordConfig":
        """
        Create Discord config from environment variables.

        Returns:
            DiscordConfig instance

        Raises:
            ValueError: If DISCORD_BOT_TOKEN is not set
        """
        bot_token = os.getenv("DISCORD_BOT_TOKEN")
        if not bot_token:
            raise ValueError("DISCORD_BOT_TOKEN environment variable is required")

        api_base_url = os.getenv("DISCORD_API_BASE_URL")

        return cls(
            bot_token=bot_token,
            api_base_url=api_base_url,
        )
