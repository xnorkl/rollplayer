"""Gameplay commands for Discord bot."""

import logging

import discord
from discord import app_commands

from ..bot import DiscordBot

logger = logging.getLogger(__name__)


def setup_gameplay_commands(bot: DiscordBot) -> None:
    """
    Set up gameplay commands.

    Args:
        bot: Discord bot instance
    """
    roll_group = app_commands.Group(
        name="roll",
        description="Dice rolling commands",
    )

    @roll_group.command(name="dice", description="Roll dice")
    @app_commands.describe(
        expression="Dice expression (e.g., 2d6+3)", reason="Reason for roll (optional)"
    )
    async def roll_dice(
        interaction: discord.Interaction,
        expression: str,
        reason: str | None = None,
    ) -> None:
        """Roll dice."""
        await interaction.response.defer(ephemeral=False)
        embed = discord.Embed(
            title="Not Implemented",
            description="Dice rolling will be implemented in a future update.",
            color=discord.Color.orange(),
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="r", description="Quick roll alias")
    @app_commands.describe(expression="Dice expression")
    async def quick_roll(
        interaction: discord.Interaction,
        expression: str,
    ) -> None:
        """Quick roll alias."""
        await interaction.response.defer(ephemeral=False)
        embed = discord.Embed(
            title="Not Implemented",
            description="Dice rolling will be implemented in a future update.",
            color=discord.Color.orange(),
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="action", description="Submit narrative action")
    @app_commands.describe(description="Action description")
    async def submit_action(
        interaction: discord.Interaction,
        description: str,
    ) -> None:
        """Submit narrative action."""
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(
            title="Not Implemented",
            description="Action submission will be implemented in a future update.",
            color=discord.Color.orange(),
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    bot.tree.add_command(roll_group)
    bot.tree.add_command(quick_roll)
    bot.tree.add_command(submit_action)
