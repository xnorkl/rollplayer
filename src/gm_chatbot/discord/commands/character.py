"""Character commands for Discord bot."""

import logging

import discord
from discord import app_commands

from ..bot import DiscordBot

logger = logging.getLogger(__name__)


def setup_character_commands(bot: DiscordBot) -> None:
    """
    Set up character commands.

    Args:
        bot: Discord bot instance
    """
    character_group = app_commands.Group(
        name="character",
        description="Character management commands",
    )

    @character_group.command(name="create", description="Create a new character")
    @app_commands.describe(name="Character name")
    async def create_character(
        interaction: discord.Interaction,
        name: str,
    ) -> None:
        """Create a new character."""
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(
            title="Not Implemented",
            description="Character creation will be implemented in a future update.",
            color=discord.Color.orange(),
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @character_group.command(name="list", description="List characters in campaign")
    async def list_characters(interaction: discord.Interaction) -> None:
        """List characters in campaign."""
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(
            title="Not Implemented",
            description="Character listing will be implemented in a future update.",
            color=discord.Color.orange(),
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @character_group.command(name="sheet", description="Display character sheet")
    @app_commands.describe(character_id="Character ID (optional)")
    async def character_sheet(
        interaction: discord.Interaction,
        character_id: str | None = None,
    ) -> None:
        """Display character sheet."""
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(
            title="Not Implemented",
            description="Character sheet display will be implemented in a future update.",
            color=discord.Color.orange(),
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    bot.tree.add_command(character_group)
