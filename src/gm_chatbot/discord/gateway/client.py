"""Discord gateway client wrapper."""

import logging
from typing import Optional

from discord.ext import commands

from ..bot import DiscordBot
from ..config import DiscordConfig
from ...artifacts.store import ArtifactStore

logger = logging.getLogger(__name__)


class DiscordGatewayClient:
    """Wrapper around Discord bot client for connection management."""

    def __init__(
        self,
        config: DiscordConfig,
        store: Optional[ArtifactStore] = None,
    ):
        """
        Initialize gateway client.

        Args:
            config: Discord configuration
            store: Optional artifact store
        """
        self.config = config
        self.store = store
        self.bot: Optional[DiscordBot] = None

    async def connect(self) -> None:
        """Establish connection to Discord."""
        if self.bot is not None:
            logger.warning("Bot already connected")
            return

        self.bot = DiscordBot(self.config, self.store)
        await self.bot.start(self.config.bot_token)

    async def disconnect(self) -> None:
        """Gracefully disconnect from Discord."""
        if self.bot is None:
            return

        await self.bot.close()
        self.bot = None

    async def reconnect(self) -> None:
        """Reconnect to Discord."""
        await self.disconnect()
        await self.connect()

    def is_connected(self) -> bool:
        """
        Check if bot is connected.

        Returns:
            True if connected, False otherwise
        """
        return self.bot is not None and self.bot.is_ready()
