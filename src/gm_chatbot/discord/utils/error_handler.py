"""Error handling for Discord commands."""

import logging

import discord

logger = logging.getLogger(__name__)


async def handle_command_error(
    interaction: discord.Interaction,
    error: Exception,
    ephemeral: bool = True,
) -> None:
    """
    Handle command error and send user-friendly message.

    Args:
        interaction: Discord interaction
        error: Exception that occurred
        ephemeral: Whether message should be ephemeral
    """
    logger.error(f"Error in command: {error}", exc_info=True)

    # Create error embed
    embed = discord.Embed(
        title="Error",
        description=f"An error occurred: {error!s}",
        color=discord.Color.red(),
    )

    # Send error message
    try:
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=ephemeral)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=ephemeral)
    except Exception as e:
        logger.error(f"Failed to send error message: {e}", exc_info=True)
