"""Base command infrastructure."""

import logging

import discord
from discord.ext import commands

from ...services.discord_context_service import DiscordContextService

logger = logging.getLogger(__name__)


class BaseCommand:
    """Base class for Discord commands with common functionality."""

    def __init__(
        self,
        bot: commands.Bot,
        context_service: DiscordContextService,
    ):
        """
        Initialize base command.

        Args:
            bot: Discord bot instance
            context_service: Discord context service
        """
        self.bot = bot
        self.context_service = context_service

    async def resolve_context(
        self,
        interaction: discord.Interaction,
    ) -> object | None:
        """
        Resolve Discord context from interaction.

        Args:
            interaction: Discord interaction

        Returns:
            DiscordContext or None
        """
        if not interaction.guild or not interaction.channel:
            return None

        guild_id = str(interaction.guild.id)
        channel_id = str(interaction.channel.id)
        user_id = str(interaction.user.id)

        return await self.context_service.resolve_context(
            guild_id=guild_id,
            channel_id=channel_id,
            user_id=user_id,
        )

    async def check_permission(
        self,
        interaction: discord.Interaction,
        campaign_id: str,
        required_role: str = "player",
    ) -> bool:
        """
        Check if user has required permission.

        Args:
            interaction: Discord interaction
            campaign_id: Campaign identifier
            required_role: Required role

        Returns:
            True if user has permission, False otherwise
        """
        if not interaction.user:
            return False

        user_id = str(interaction.user.id)
        return await self.context_service.validate_permission(
            user_id=user_id,
            campaign_id=campaign_id,
            required_role=required_role,
        )

    async def send_error(
        self,
        interaction: discord.Interaction,
        error_message: str,
        ephemeral: bool = True,
    ) -> None:
        """
        Send error message to user.

        Args:
            interaction: Discord interaction
            error_message: Error message
            ephemeral: Whether message should be ephemeral
        """
        embed = discord.Embed(
            title="Error",
            description=error_message,
            color=discord.Color.red(),
        )

        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=ephemeral)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=ephemeral)


def error_handler(func):
    """Decorator for error handling in commands."""

    async def wrapper(self, interaction: discord.Interaction, *args, **kwargs):
        try:
            return await func(self, interaction, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in command {func.__name__}: {e}", exc_info=True)
            await self.send_error(
                interaction,
                f"An error occurred: {e!s}",
            )

    return wrapper
