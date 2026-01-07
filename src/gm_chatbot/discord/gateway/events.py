"""Discord event handlers."""

import logging

import discord

from ..bot import DiscordBot

logger = logging.getLogger(__name__)


async def setup_event_handlers(bot: DiscordBot) -> None:
    """
    Set up event handlers for Discord bot.

    Args:
        bot: Discord bot instance
    """
    # Event handlers are defined as methods on the bot class
    # This function can be used to register additional handlers if needed
    pass


async def handle_message_event(
    bot: DiscordBot,
    message: discord.Message,
) -> None:
    """
    Handle message event for chat forwarding during active sessions.

    Args:
        bot: Discord bot instance
        message: Discord message
    """
    # Skip bot messages
    if message.author.bot:
        return

    # Skip if message doesn't mention bot or isn't in a bound channel
    # This will be implemented when chat integration is added
    # For now, this is a placeholder
    logger.debug(f"Message received: {message.content[:50]}")
