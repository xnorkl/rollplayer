"""Session commands for Discord bot."""

import logging

import discord
from discord import app_commands

from ..bot import DiscordBot

logger = logging.getLogger(__name__)


def setup_session_commands(bot: DiscordBot) -> None:
    """
    Set up session commands.

    Args:
        bot: Discord bot instance
    """
    session_group = app_commands.Group(
        name="session",
        description="Session management commands",
    )

    @session_group.command(name="start", description="Start a new session")
    @app_commands.describe(name="Session name (optional)")
    async def start_session(
        interaction: discord.Interaction,
        name: str | None = None,
    ) -> None:
        """Start a new session."""
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(
            title="Not Implemented",
            description="Session management will be implemented in a future update.",
            color=discord.Color.orange(),
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @session_group.command(name="end", description="End current session")
    async def end_session(interaction: discord.Interaction) -> None:
        """End current session."""
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(
            title="Not Implemented",
            description="Session management will be implemented in a future update.",
            color=discord.Color.orange(),
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @session_group.command(name="status", description="Show session status")
    async def session_status(interaction: discord.Interaction) -> None:
        """Show session status."""
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(
            title="Not Implemented",
            description="Session management will be implemented in a future update.",
            color=discord.Color.orange(),
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    bot.tree.add_command(session_group)
