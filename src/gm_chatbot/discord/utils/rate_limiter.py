"""Rate limiting for Discord commands."""

import time
from collections import defaultdict
from typing import Optional


class RateLimiter:
    """Rate limiter for Discord commands."""

    def __init__(
        self,
        commands_per_user: tuple[int, int] = (20, 60),
        messages_per_channel: tuple[int, int] = (30, 60),
        api_calls_per_guild: tuple[int, int] = (100, 60),
    ):
        """
        Initialize rate limiter.

        Args:
            commands_per_user: (limit, window_seconds) for commands per user
            messages_per_channel: (limit, window_seconds) for messages per channel
            api_calls_per_guild: (limit, window_seconds) for API calls per guild
        """
        self.commands_per_user = commands_per_user
        self.messages_per_channel = messages_per_channel
        self.api_calls_per_guild = api_calls_per_guild

        # Track usage
        self.user_commands: dict[str, list[float]] = defaultdict(list)
        self.channel_messages: dict[str, list[float]] = defaultdict(list)
        self.guild_api_calls: dict[str, list[float]] = defaultdict(list)

    def check_user_command(self, user_id: str) -> bool:
        """
        Check if user can execute a command.

        Args:
            user_id: User ID

        Returns:
            True if allowed, False if rate limited
        """
        limit, window = self.commands_per_user
        now = time.time()

        # Clean old entries
        self.user_commands[user_id] = [
            t for t in self.user_commands[user_id] if now - t < window
        ]

        # Check limit
        if len(self.user_commands[user_id]) >= limit:
            return False

        # Record command
        self.user_commands[user_id].append(now)
        return True

    def check_channel_message(self, channel_id: str) -> bool:
        """
        Check if channel can receive a message.

        Args:
            channel_id: Channel ID

        Returns:
            True if allowed, False if rate limited
        """
        limit, window = self.messages_per_channel
        now = time.time()

        # Clean old entries
        self.channel_messages[channel_id] = [
            t for t in self.channel_messages[channel_id] if now - t < window
        ]

        # Check limit
        if len(self.channel_messages[channel_id]) >= limit:
            return False

        # Record message
        self.channel_messages[channel_id].append(now)
        return True

    def check_guild_api_call(self, guild_id: str) -> bool:
        """
        Check if guild can make an API call.

        Args:
            guild_id: Guild ID

        Returns:
            True if allowed, False if rate limited
        """
        limit, window = self.api_calls_per_guild
        now = time.time()

        # Clean old entries
        self.guild_api_calls[guild_id] = [
            t for t in self.guild_api_calls[guild_id] if now - t < window
        ]

        # Check limit
        if len(self.guild_api_calls[guild_id]) >= limit:
            return False

        # Record API call
        self.guild_api_calls[guild_id].append(now)
        return True
