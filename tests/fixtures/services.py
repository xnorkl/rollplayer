"""Service fixtures for testing."""

import pytest

from gm_chatbot.services.campaign_service import CampaignService
from gm_chatbot.services.character_service import CharacterService
from gm_chatbot.services.player_service import PlayerService
from gm_chatbot.services.session_service import SessionService


@pytest.fixture
def campaign_service(artifact_store):
    """Create campaign service."""
    return CampaignService(store=artifact_store)


@pytest.fixture
def character_service(artifact_store):
    """Create character service."""
    return CharacterService(store=artifact_store)


@pytest.fixture
def player_service(artifact_store):
    """Create player service."""
    return PlayerService(store=artifact_store)


@pytest.fixture
def session_service(artifact_store):
    """Create session service."""
    return SessionService(store=artifact_store)
