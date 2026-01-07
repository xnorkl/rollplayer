"""Discord bot startup module."""

import asyncio
import logging

from ..artifacts.store import ArtifactStore
from .bot import DiscordBot
from .commands import admin, campaign, character, gameplay, session
from .config import DiscordConfig

logger = logging.getLogger(__name__)

_bot_task: asyncio.Task | None = None
_bot: DiscordBot | None = None


async def start_discord_bot(
    config: DiscordConfig | None = None,
    store: ArtifactStore | None = None,
) -> None:
    """
    Start Discord bot.

    Args:
        config: Optional Discord config (creates from env if not provided)
        store: Optional artifact store
    """
    global _bot, _bot_task

    if _bot is not None:
        logger.warning("Discord bot already started")
        return

    if config is None:
        config = DiscordConfig.from_env()

    # Create bot
    _bot = DiscordBot(config, store)

    # Register commands
    campaign.setup_campaign_commands(_bot)
    character.setup_character_commands(_bot)
    session.setup_session_commands(_bot)
    gameplay.setup_gameplay_commands(_bot)
    admin.setup_admin_commands(_bot)

    # Start bot in background
    async def run_bot():
        try:
            await _bot.start(config.bot_token)
        except Exception as e:
            logger.error(f"Discord bot error: {e}", exc_info=True)
            raise

    _bot_task = asyncio.create_task(run_bot())
    logger.info("Discord bot startup task created")


async def stop_discord_bot() -> None:
    """Stop Discord bot."""
    global _bot, _bot_task

    if _bot is None:
        return

    logger.info("Stopping Discord bot...")
    await _bot.close()
    _bot = None

    if _bot_task:
        _bot_task.cancel()
        try:
            await _bot_task
        except asyncio.CancelledError:
            pass
        _bot_task = None

    logger.info("Discord bot stopped")
