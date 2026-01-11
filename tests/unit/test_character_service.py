"""Unit tests for CharacterService."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from gm_chatbot.models.character import CharacterSheet, CharacterIdentity
from gm_chatbot.models.membership import CampaignMembership
from gm_chatbot.services.character_service import CharacterService
from gm_chatbot.services.campaign_service import CampaignService


@pytest.mark.asyncio
async def test_get_character_by_player_with_existing_character(artifact_store):
    """Test get_character_by_player with existing character linked."""
    campaign_service = CampaignService(store=artifact_store)
    character_service = CharacterService(
        store=artifact_store, campaign_service=campaign_service
    )

    # Create campaign
    campaign = await campaign_service.create_campaign(
        name="Test Campaign",
        rule_system="shadowdark",
    )

    # Create player
    from gm_chatbot.services.player_service import PlayerService

    player_service = PlayerService(store=artifact_store)
    player = await player_service.create_player(
        username="testplayer",
        display_name="Test Player",
    )

    # Add player to campaign
    await campaign_service.add_player(
        campaign_id=campaign.metadata.id,
        player_id=player.metadata.id,
        role="player",
    )

    # Create character
    character = await character_service.create_character(
        campaign_id=campaign.metadata.id,
        character_type="player_character",
        name="Test Hero",
    )

    # Link character to membership
    await campaign_service.update_membership(
        campaign_id=campaign.metadata.id,
        player_id=player.metadata.id,
        character_id=character.metadata.id,
    )

    # Get character by player
    retrieved = await character_service.get_character_by_player(
        campaign_id=campaign.metadata.id,
        player_id=player.metadata.id,
    )

    assert retrieved is not None
    assert retrieved.metadata.id == character.metadata.id
    assert retrieved.identity.name == "Test Hero"


@pytest.mark.asyncio
async def test_get_character_by_player_no_character_linked(artifact_store):
    """Test get_character_by_player when no character is linked."""
    campaign_service = CampaignService(store=artifact_store)
    character_service = CharacterService(
        store=artifact_store, campaign_service=campaign_service
    )

    # Create campaign
    campaign = await campaign_service.create_campaign(
        name="Test Campaign",
        rule_system="shadowdark",
    )

    # Create player
    from gm_chatbot.services.player_service import PlayerService

    player_service = PlayerService(store=artifact_store)
    player = await player_service.create_player(
        username="testplayer",
        display_name="Test Player",
    )

    # Add player to campaign (without character)
    await campaign_service.add_player(
        campaign_id=campaign.metadata.id,
        player_id=player.metadata.id,
        role="player",
    )

    # Get character by player (should return None)
    retrieved = await character_service.get_character_by_player(
        campaign_id=campaign.metadata.id,
        player_id=player.metadata.id,
    )

    assert retrieved is None


@pytest.mark.asyncio
async def test_get_character_by_player_membership_not_found(artifact_store):
    """Test get_character_by_player when membership doesn't exist."""
    campaign_service = CampaignService(store=artifact_store)
    character_service = CharacterService(
        store=artifact_store, campaign_service=campaign_service
    )

    # Create campaign
    campaign = await campaign_service.create_campaign(
        name="Test Campaign",
        rule_system="shadowdark",
    )

    # Create player (but don't add to campaign)
    from gm_chatbot.services.player_service import PlayerService

    player_service = PlayerService(store=artifact_store)
    player = await player_service.create_player(
        username="testplayer",
        display_name="Test Player",
    )

    # Get character by player (membership doesn't exist, returns None)
    retrieved = await character_service.get_character_by_player(
        campaign_id=campaign.metadata.id,
        player_id=player.metadata.id,
    )

    assert retrieved is None


@pytest.mark.asyncio
async def test_get_character_by_player_with_mocked_campaign_service():
    """Test get_character_by_player with mocked CampaignService."""
    mock_store = MagicMock()
    mock_campaign_service = AsyncMock()

    # Mock membership with character_id
    mock_membership = MagicMock()
    mock_membership.character_id = "character-123"
    mock_campaign_service.get_membership.return_value = mock_membership

    # Mock character with proper structure
    mock_character = MagicMock()
    mock_metadata = MagicMock()
    mock_metadata.id = "character-123"
    mock_character.metadata = mock_metadata
    mock_identity = MagicMock()
    mock_identity.name = "Test Hero"
    mock_character.identity = mock_identity

    character_service = CharacterService(
        store=mock_store, campaign_service=mock_campaign_service
    )

    # Mock get_character method
    character_service.get_character = AsyncMock(return_value=mock_character)

    # Call get_character_by_player
    result = await character_service.get_character_by_player(
        campaign_id="campaign-1",
        player_id="player-1",
    )

    assert result is not None
    assert result.metadata.id == "character-123"
    mock_campaign_service.get_membership.assert_called_once_with(
        "campaign-1", "player-1"
    )
    character_service.get_character.assert_called_once_with(
        "campaign-1", "character-123"
    )


@pytest.mark.asyncio
async def test_get_character_by_player_mocked_no_character():
    """Test get_character_by_player with mocked service returning None for character_id."""
    mock_store = MagicMock()
    mock_campaign_service = AsyncMock()

    # Mock membership without character_id
    mock_membership = MagicMock()
    mock_membership.character_id = None
    mock_campaign_service.get_membership.return_value = mock_membership

    character_service = CharacterService(
        store=mock_store, campaign_service=mock_campaign_service
    )

    # Call get_character_by_player
    result = await character_service.get_character_by_player(
        campaign_id="campaign-1",
        player_id="player-1",
    )

    assert result is None
    mock_campaign_service.get_membership.assert_called_once_with(
        "campaign-1", "player-1"
    )
