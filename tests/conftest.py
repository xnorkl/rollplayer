"""Pytest configuration and fixtures."""

# Import all fixtures from fixtures modules
from tests.fixtures.store import artifact_store, temp_campaigns_dir
from tests.fixtures.services import (
    campaign_service,
    character_service,
    player_service,
    session_service,
)
from tests.fixtures.data import (
    player,
    campaign,
    campaign_with_members,
    character,
    active_session,
    ended_session,
)

# Keep existing fixtures for backward compatibility
import pytest
from gm_chatbot.services.game_state_service import GameStateService
from gm_chatbot.tools.registry import DiceToolRegistry


@pytest.fixture
def game_state_service(artifact_store, character_service):
    """Create game state service."""
    return GameStateService(store=artifact_store, character_service=character_service)


@pytest.fixture
def dice_tool_registry():
    """Create dice tool registry."""
    return DiceToolRegistry()
