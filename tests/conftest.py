"""Pytest configuration and fixtures."""

import pytest
from pathlib import Path
import tempfile
import shutil

from gm_chatbot.artifacts.store import ArtifactStore
from gm_chatbot.services.campaign_service import CampaignService
from gm_chatbot.services.character_service import CharacterService
from gm_chatbot.services.game_state_service import GameStateService
from gm_chatbot.tools.registry import DiceToolRegistry


@pytest.fixture
def temp_campaigns_dir():
    """Create temporary campaigns directory."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def artifact_store(temp_campaigns_dir):
    """Create artifact store with temp directory."""
    return ArtifactStore(campaigns_dir=temp_campaigns_dir)


@pytest.fixture
def campaign_service(artifact_store):
    """Create campaign service."""
    return CampaignService(store=artifact_store)


@pytest.fixture
def character_service(artifact_store):
    """Create character service."""
    return CharacterService(store=artifact_store)


@pytest.fixture
def game_state_service(artifact_store, character_service):
    """Create game state service."""
    return GameStateService(store=artifact_store, character_service=character_service)


@pytest.fixture
def dice_tool_registry():
    """Create dice tool registry."""
    return DiceToolRegistry()
