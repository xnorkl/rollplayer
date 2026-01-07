"""Pytest configuration and fixtures."""

import os
import tempfile
from pathlib import Path

# Keep existing fixtures for backward compatibility
import pytest

from gm_chatbot.services.game_state_service import GameStateService
from gm_chatbot.tools.registry import DiceToolRegistry

# Import all fixtures from fixtures modules
pytest_plugins = [
    "tests.fixtures.data",
    "tests.fixtures.services",
    "tests.fixtures.store",
]


@pytest.fixture(scope="function", autouse=True)
def setup_test_env():
    """Set up test environment variables for integration tests."""
    from gm_chatbot.api.dependencies import reset_dependencies

    # Reset dependencies before each test to ensure fresh initialization
    reset_dependencies()

    # Create temporary directories for integration tests
    temp_base = tempfile.mkdtemp()
    campaigns_dir = Path(temp_base) / "campaigns"
    players_dir = Path(temp_base) / "players"
    rules_dir = Path(temp_base) / "rules"

    campaigns_dir.mkdir(parents=True, exist_ok=True)
    players_dir.mkdir(parents=True, exist_ok=True)
    rules_dir.mkdir(parents=True, exist_ok=True)

    # Set environment variables (override any existing values for test isolation)
    os.environ["CAMPAIGNS_DIR"] = str(campaigns_dir)
    os.environ["PLAYERS_DIR"] = str(players_dir)
    os.environ["RULES_DIR"] = str(rules_dir)

    yield

    # Cleanup
    import shutil

    shutil.rmtree(temp_base, ignore_errors=True)

    # Reset dependencies after test
    reset_dependencies()


@pytest.fixture
def game_state_service(artifact_store, character_service):
    """Create game state service."""
    return GameStateService(store=artifact_store, character_service=character_service)


@pytest.fixture
def dice_tool_registry():
    """Create dice tool registry."""
    return DiceToolRegistry()
