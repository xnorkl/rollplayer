"""Discord bot client."""

import logging

import discord
from discord.ext import commands

from ..artifacts.store import ArtifactStore
from ..services.campaign_service import CampaignService
from ..services.character_service import CharacterService
from ..services.discord_binding_service import DiscordBindingService
from ..services.discord_context_service import DiscordContextService
from ..services.discord_linking_service import DiscordLinkingService
from ..services.player_service import PlayerService
from ..services.session_service import SessionService
from .config import DiscordConfig

logger = logging.getLogger(__name__)


class DiscordBot(commands.Bot):
    """Discord bot for GM Chatbot."""

    def __init__(
        self,
        config: DiscordConfig,
        store: ArtifactStore | None = None,
    ):
        """
        Initialize Discord bot.

        Args:
            config: Discord configuration
            store: Optional artifact store
        """
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True

        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None,  # Disable default help command
        )

        self.config = config
        self.store = store or ArtifactStore()

        # Initialize services
        self.linking_service = DiscordLinkingService(self.store)
        self.binding_service = DiscordBindingService(self.store)
        self.context_service = DiscordContextService(self.store)
        self.campaign_service = CampaignService(self.store)
        self.player_service = PlayerService(self.store)
        self.session_service = SessionService(self.store)
        self.character_service = CharacterService(self.store)

    async def setup_hook(self) -> None:
        """Called when the bot is starting up."""
        logger.info("Discord bot setup hook called")
        # Commands will be registered by command modules
        # This is where we'd sync app commands if needed

    async def on_ready(self) -> None:
        """Called when the bot is ready."""
        logger.info(f"Discord bot ready: {self.user} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guilds")

        # Sync app commands
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} command(s)")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")

    async def on_guild_join(self, guild: discord.Guild) -> None:
        """Called when the bot joins a guild."""
        logger.info(f"Joined guild: {guild.name} (ID: {guild.id})")

    async def on_guild_remove(self, guild: discord.Guild) -> None:
        """Called when the bot leaves a guild."""
        logger.info(f"Left guild: {guild.name} (ID: {guild.id})")

    async def close(self) -> None:
        """Called when the bot is closing."""
        logger.info("Discord bot closing")
        await super().close()
