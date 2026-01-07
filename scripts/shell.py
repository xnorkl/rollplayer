#!/usr/bin/env python
"""Interactive shell with GM Chatbot context loaded.

Usage:
    just shell
    uv run python scripts/shell.py

Features:
    - Pre-imported services and models
    - Isolated temp directory (no production data affected)
    - Helper functions for quick entity creation
    - Tab completion and command history
"""

from __future__ import annotations

import asyncio
import code
import readline
import rlcompleter
import shutil
import tempfile
from pathlib import Path


def create_test_context() -> dict:
    """
    Initialize isolated test environment and return namespace.

    Returns:
        Dictionary of objects available in shell namespace
    """
    # Lazy imports to speed up shell startup
    from gm_chatbot.artifacts.store import ArtifactStore
    from gm_chatbot.services.campaign_service import CampaignService
    from gm_chatbot.services.player_service import PlayerService
    from gm_chatbot.services.session_service import SessionService
    from gm_chatbot.models import (
        Player,
        Campaign,
        Session,
        CharacterSheet,
        GameAction,
    )
    from gm_chatbot.lib import utc_now, parse_datetime, ensure_utc

    # Create isolated environment
    temp_dir = Path(tempfile.mkdtemp(prefix="gm_shell_"))
    store = ArtifactStore(campaigns_dir=temp_dir / "campaigns", players_dir=temp_dir / "players")

    # Initialize services
    campaign_svc = CampaignService(store)
    player_svc = PlayerService(store)
    session_svc = SessionService(store)

    # Helper functions (sync wrappers for async services)
    def quick_player(name: str = "test") -> Player:
        """Create a player with minimal input."""
        import time
        username = f"{name}_{int(time.time())}"
        return asyncio.run(player_svc.create_player(username, name.title()))

    def quick_campaign(name: str = "Test Quest", system: str = "dnd5e") -> Campaign:
        """Create a campaign with minimal input."""
        return asyncio.run(campaign_svc.create_campaign(name, system))

    def quick_session(campaign_id: str, gm_id: str) -> Session:
        """Start a session with minimal input."""
        return asyncio.run(session_svc.create_session(campaign_id, gm_id))

    def cleanup():
        """Remove temp directory."""
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"Cleaned up: {temp_dir}")

    return {
        # Services
        "store": store,
        "campaign_svc": campaign_svc,
        "player_svc": player_svc,
        "session_svc": session_svc,
        # Models
        "Player": Player,
        "Campaign": Campaign,
        "Session": Session,
        "CharacterSheet": CharacterSheet,
        "GameAction": GameAction,
        # Utilities
        "utc_now": utc_now,
        "parse_datetime": parse_datetime,
        "ensure_utc": ensure_utc,
        # Helpers
        "quick_player": quick_player,
        "quick_campaign": quick_campaign,
        "quick_session": quick_session,
        "cleanup": cleanup,
        # Async support
        "asyncio": asyncio,
        # Metadata
        "_temp_dir": temp_dir,
    }


def main() -> None:
    """Start interactive shell."""
    namespace = create_test_context()

    # Setup tab completion
    readline.set_completer(rlcompleter.Completer(namespace).complete)
    readline.parse_and_bind("tab: complete")

    # Enable history
    import os
    history_file = Path.home() / ".gm_shell_history"
    try:
        readline.read_history_file(history_file)
    except FileNotFoundError:
        pass

    import atexit
    atexit.register(readline.write_history_file, history_file)

    banner = """
╔══════════════════════════════════════════════════════════════════╗
║  GM Chatbot Smoke Test Shell                                     ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  Services:   campaign_svc, player_svc, session_svc, store        ║
║  Models:     Player, Campaign, Session, CharacterSheet           ║
║  Utilities:  utc_now, parse_datetime, ensure_utc                 ║
║  Helpers:    quick_player(), quick_campaign(), quick_session()   ║
║                                                                  ║
║  Example:                                                        ║
║    >>> player = quick_player("hero")                             ║
║    >>> campaign = quick_campaign("Dragon Hunt")                  ║
║    >>> campaign_svc.add_player(campaign.id, player.id)          ║
║                                                                  ║
║  Note: Services are async - use asyncio.run() for async calls   ║
║  Type cleanup() before exit to remove temp files.               ║
╚══════════════════════════════════════════════════════════════════╝
"""

    code.interact(banner=banner, local=namespace, exitmsg="Goodbye!")


if __name__ == "__main__":
    main()
