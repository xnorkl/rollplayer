"""Unit tests for CampaignService membership operations."""

import pytest

from gm_chatbot.services.campaign_service import CampaignService
from gm_chatbot.services.player_service import PlayerService
from tests.fixtures.store import artifact_store


@pytest.mark.asyncio
async def test_add_player_to_campaign(artifact_store):
    """Test adding a player to a campaign."""
    campaign_service = CampaignService(store=artifact_store)
    player_service = PlayerService(store=artifact_store)

    campaign = await campaign_service.create_campaign(
        name="Test Campaign",
        rule_system="shadowdark",
    )
    player = await player_service.create_player(
        username="testplayer",
        display_name="Test Player",
    )

    membership = await campaign_service.add_player(
        campaign_id=campaign.metadata.id,
        player_id=player.metadata.id,
        role="player",
    )

    assert membership.player_id == player.metadata.id
    assert membership.campaign_id == campaign.metadata.id
    assert membership.role == "player"


@pytest.mark.asyncio
async def test_duplicate_membership(artifact_store):
    """Test that duplicate memberships are prevented."""
    campaign_service = CampaignService(store=artifact_store)
    player_service = PlayerService(store=artifact_store)

    campaign = await campaign_service.create_campaign(
        name="Test Campaign",
        rule_system="shadowdark",
    )
    player = await player_service.create_player(
        username="testplayer",
        display_name="Test Player",
    )

    await campaign_service.add_player(
        campaign_id=campaign.metadata.id,
        player_id=player.metadata.id,
    )

    # Attempt to add again
    with pytest.raises(ValueError, match="already a member"):
        await campaign_service.add_player(
            campaign_id=campaign.metadata.id,
            player_id=player.metadata.id,
        )


@pytest.mark.asyncio
async def test_list_members(artifact_store):
    """Test listing campaign members."""
    campaign_service = CampaignService(store=artifact_store)
    player_service = PlayerService(store=artifact_store)

    campaign = await campaign_service.create_campaign(
        name="Test Campaign",
        rule_system="shadowdark",
    )
    player1 = await player_service.create_player(
        username="player1",
        display_name="Player One",
    )
    player2 = await player_service.create_player(
        username="player2",
        display_name="Player Two",
    )

    await campaign_service.add_player(campaign.metadata.id, player1.metadata.id)
    await campaign_service.add_player(campaign.metadata.id, player2.metadata.id)

    members = await campaign_service.list_members(campaign.metadata.id)
    assert len(members) == 2


@pytest.mark.asyncio
async def test_update_membership(artifact_store):
    """Test updating a membership."""
    campaign_service = CampaignService(store=artifact_store)
    player_service = PlayerService(store=artifact_store)

    campaign = await campaign_service.create_campaign(
        name="Test Campaign",
        rule_system="shadowdark",
    )
    player = await player_service.create_player(
        username="testplayer",
        display_name="Test Player",
    )

    await campaign_service.add_player(
        campaign_id=campaign.metadata.id,
        player_id=player.metadata.id,
        role="player",
    )

    # Update role
    updated = await campaign_service.update_membership(
        campaign_id=campaign.metadata.id,
        player_id=player.metadata.id,
        role="gm",
    )

    assert updated.role == "gm"
