"""Integration tests for characters."""

import pytest

from gm_chatbot.models.character import CharacterSheet, CharacterIdentity


@pytest.mark.asyncio
async def test_create_character(campaign_service, character_service):
    """Test creating a character."""
    campaign = await campaign_service.create_campaign(
        name="Test Campaign",
        rule_system="shadowdark",
    )

    from gm_chatbot.models.character import CharacterIdentity

    character = await character_service.create_character(
        campaign_id=campaign.metadata.id,
        character_type="player_character",
        name="Test Character",
        identity=CharacterIdentity(name="Test Character", level=3).model_dump(),
    )

    assert character.identity.name == "Test Character"
    assert character.character_type == "player_character"
    assert character.metadata.id is not None


@pytest.mark.asyncio
async def test_list_characters(campaign_service, character_service):
    """Test listing characters."""
    campaign = await campaign_service.create_campaign(
        name="Test Campaign",
        rule_system="shadowdark",
    )

    await character_service.create_character(
        campaign_id=campaign.metadata.id,
        character_type="player_character",
        name="PC 1",
    )
    await character_service.create_character(
        campaign_id=campaign.metadata.id,
        character_type="non_player_character",
        name="NPC 1",
    )

    characters = await character_service.list_characters(campaign.metadata.id)
    assert len(characters) == 2

    pcs = await character_service.list_characters(
        campaign.metadata.id,
        character_type="player_character",
    )
    assert len(pcs) == 1
