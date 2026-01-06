"""Admin commands for Discord bot."""

import logging

import discord
from discord import app_commands

from ..bot import DiscordBot

logger = logging.getLogger(__name__)


def setup_admin_commands(bot: DiscordBot) -> None:
    """
    Set up admin commands.

    Args:
        bot: Discord bot instance
    """
    admin_group = app_commands.Group(
        name="admin",
        description="Administrative commands",
    )

    @admin_group.command(name="setup", description="Initial bot configuration")
    async def admin_setup(interaction: discord.Interaction) -> None:
        """Initial bot configuration."""
        await interaction.response.defer(ephemeral=True)

        # Check if user is administrator
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                title="Error",
                description="You need administrator permissions to use this command.",
                color=discord.Color.red(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(
            title="Not Implemented",
            description="Admin setup will be implemented in a future update.",
            color=discord.Color.orange(),
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    bot.tree.add_command(admin_group)
