"""Application entry point."""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

import uvicorn

# #region agent log
try:
    import subprocess
    log_data = {
        "sessionId": "debug-session",
        "runId": "pre-import",
        "location": "main.py:18",
        "message": "Python environment check before discord import",
        "data": {
            "python_version": sys.version,
            "python_executable": sys.executable,
            "sys_path": sys.path,
            "path_env": os.environ.get("PATH", ""),
            "pythonpath_env": os.environ.get("PYTHONPATH", ""),
            "venv_exists": os.path.exists("/app/.venv"),
            "venv_bin_exists": os.path.exists("/app/.venv/bin"),
            "venv_site_packages": str(Path("/app/.venv/lib").glob("python*/site-packages")) if os.path.exists("/app/.venv") else None,
        },
        "timestamp": int(asyncio.get_event_loop().time() * 1000) if hasattr(asyncio, "get_event_loop") else 0,
    }
    with open("/Users/thomasgordon/Engagements/Etc/roll20_chatbot/.cursor/debug.log", "a") as f:
        f.write(json.dumps(log_data) + "\n")
except Exception:
    pass
# #endregion

# #region agent log
try:
    import subprocess
    result = subprocess.run([sys.executable, "-m", "pip", "list"], capture_output=True, text=True, timeout=5)
    log_data = {
        "sessionId": "debug-session",
        "runId": "pre-import",
        "hypothesisId": "A",
        "location": "main.py:42",
        "message": "Installed packages check",
        "data": {
            "pip_list_stdout": result.stdout[:1000] if result.stdout else None,
            "pip_list_stderr": result.stderr[:500] if result.stderr else None,
            "pip_list_returncode": result.returncode,
            "discord_in_output": "discord" in (result.stdout or "").lower(),
        },
        "timestamp": int(asyncio.get_event_loop().time() * 1000) if hasattr(asyncio, "get_event_loop") else 0,
    }
    with open("/Users/thomasgordon/Engagements/Etc/roll20_chatbot/.cursor/debug.log", "a") as f:
        f.write(json.dumps(log_data) + "\n")
except Exception as e:
    try:
        log_data = {
            "sessionId": "debug-session",
            "runId": "pre-import",
            "hypothesisId": "A",
            "location": "main.py:58",
            "message": "pip list failed",
            "data": {"error": str(e)},
            "timestamp": int(asyncio.get_event_loop().time() * 1000) if hasattr(asyncio, "get_event_loop") else 0,
        }
        with open("/Users/thomasgordon/Engagements/Etc/roll20_chatbot/.cursor/debug.log", "a") as f:
            f.write(json.dumps(log_data) + "\n")
    except Exception:
        pass
# #endregion

# #region agent log
try:
    import importlib.util
    discord_spec = importlib.util.find_spec("discord")
    log_data = {
        "sessionId": "debug-session",
        "runId": "pre-import",
        "hypothesisId": "B",
        "location": "main.py:70",
        "message": "Discord module find_spec check",
        "data": {
            "discord_spec_found": discord_spec is not None,
            "discord_spec_origin": str(discord_spec.origin) if discord_spec else None,
            "discord_spec_loader": str(discord_spec.loader) if discord_spec and discord_spec.loader else None,
        },
        "timestamp": int(asyncio.get_event_loop().time() * 1000) if hasattr(asyncio, "get_event_loop") else 0,
    }
    with open("/Users/thomasgordon/Engagements/Etc/roll20_chatbot/.cursor/debug.log", "a") as f:
        f.write(json.dumps(log_data) + "\n")
except Exception as e:
    try:
        log_data = {
            "sessionId": "debug-session",
            "runId": "pre-import",
            "hypothesisId": "B",
            "location": "main.py:84",
            "message": "find_spec check failed",
            "data": {"error": str(e)},
            "timestamp": int(asyncio.get_event_loop().time() * 1000) if hasattr(asyncio, "get_event_loop") else 0,
        }
        with open("/Users/thomasgordon/Engagements/Etc/roll20_chatbot/.cursor/debug.log", "a") as f:
            f.write(json.dumps(log_data) + "\n")
    except Exception:
        pass
# #endregion

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
