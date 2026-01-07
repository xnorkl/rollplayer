"""Application entry point."""

import logging
import os

import uvicorn

from .api.app import create_app
from .discord.startup import start_discord_bot, stop_discord_bot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = create_app()


@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    # Start Discord bot if token is configured
    if os.getenv("DISCORD_BOT_TOKEN"):
        try:
            await start_discord_bot()
            logger.info("Discord bot started")
        except Exception as e:
            logger.error(f"Failed to start Discord bot: {e}", exc_info=True)
    else:
        logger.info("DISCORD_BOT_TOKEN not set, skipping Discord bot startup")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    await stop_discord_bot()
    logger.info("Application shutdown complete")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
