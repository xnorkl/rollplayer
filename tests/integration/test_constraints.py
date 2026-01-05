"""Integration tests for business rule constraints."""

import pytest
from fastapi.testclient import TestClient

from gm_chatbot.api.app import create_app
from gm_chatbot.services.campaign_service import CampaignService
from gm_chatbot.services.player_service import PlayerService
from gm_chatbot.services.session_service import SessionService
from tests.fixtures.store import artifact_store


@pytest.mark.asyncio
async def test_single_active_session_per_player(artifact_store):
    """Test that a player can only be in one active session at a time."""
    campaign_service = CampaignService(store=artifact_store)
    player_service = PlayerService(store=artifact_store)
    session_service = SessionService(store=artifact_store)

    # Create two campaigns
    campaign1 = await campaign_service.create_campaign(
        name="Campaign 1",
        rule_system="shadowdark",
    )
    campaign2 = await campaign_service.create_campaign(
        name="Campaign 2",
        rule_system="shadowdark",
    )

    # Create players
    player = await player_service.create_player(
        username="testplayer",
        display_name="Test Player",
    )
    gm1 = await player_service.create_player(
        username="gm1",
        display_name="GM One",
    )
    gm2 = await player_service.create_player(
        username="gm2",
        display_name="GM Two",
    )

    # Add player to both campaigns
    await campaign_service.add_player(campaign1.metadata.id, player.metadata.id)
    await campaign_service.add_player(campaign2.metadata.id, player.metadata.id)

    # Create sessions
    session1 = await session_service.create_session(
        campaign_id=campaign1.metadata.id,
        started_by=gm1.metadata.id,
    )
    session2 = await session_service.create_session(
        campaign_id=campaign2.metadata.id,
        started_by=gm2.metadata.id,
    )

    # Join first session
    await session_service.join_session(
        campaign_id=campaign1.metadata.id,
        session_id=session1.metadata.id,
        player_id=player.metadata.id,
    )

    # Attempt to join second session
    with pytest.raises(ValueError, match="already in active session"):
        await session_service.join_session(
            campaign_id=campaign2.metadata.id,
            session_id=session2.metadata.id,
            player_id=player.metadata.id,
        )


@pytest.mark.asyncio
async def test_single_active_session_per_campaign(artifact_store):
    """Test that a campaign can only have one active session."""
    campaign_service = CampaignService(store=artifact_store)
    player_service = PlayerService(store=artifact_store)
    session_service = SessionService(store=artifact_store)

    campaign = await campaign_service.create_campaign(
        name="Test Campaign",
        rule_system="shadowdark",
    )
    gm = await player_service.create_player(
        username="gm",
        display_name="Game Master",
    )

    # Create first session
    await session_service.create_session(
        campaign_id=campaign.metadata.id,
        started_by=gm.metadata.id,
    )

    # Attempt to create second session
    with pytest.raises(ValueError, match="already has an active"):
        await session_service.create_session(
            campaign_id=campaign.metadata.id,
            started_by=gm.metadata.id,
        )


@pytest.mark.asyncio
async def test_membership_required(artifact_store):
    """Test that players must be campaign members before joining sessions."""
    campaign_service = CampaignService(store=artifact_store)
    player_service = PlayerService(store=artifact_store)
    session_service = SessionService(store=artifact_store)

    campaign = await campaign_service.create_campaign(
        name="Test Campaign",
        rule_system="shadowdark",
    )
    gm = await player_service.create_player(
        username="gm",
        display_name="Game Master",
    )
    player = await player_service.create_player(
        username="testplayer",
        display_name="Test Player",
    )

    # Create session
    session = await session_service.create_session(
        campaign_id=campaign.metadata.id,
        started_by=gm.metadata.id,
    )

    # Attempt to join without membership
    with pytest.raises(ValueError, match="not a member"):
        await session_service.join_session(
            campaign_id=campaign.metadata.id,
            session_id=session.metadata.id,
            player_id=player.metadata.id,
        )


@pytest.mark.asyncio
async def test_session_immutability(artifact_store):
    """Test that ended sessions cannot be modified."""
    campaign_service = CampaignService(store=artifact_store)
    player_service = PlayerService(store=artifact_store)
    session_service = SessionService(store=artifact_store)

    campaign = await campaign_service.create_campaign(
        name="Test Campaign",
        rule_system="shadowdark",
    )
    gm = await player_service.create_player(
        username="gm",
        display_name="Game Master",
    )

    session = await session_service.create_session(
        campaign_id=campaign.metadata.id,
        started_by=gm.metadata.id,
    )

    # End session
    await session_service.end_session(campaign.metadata.id, session.metadata.id)

    # Attempt to modify
    session.status = "active"
    with pytest.raises(ValueError, match="Cannot modify an ended session"):
        await session_service.update_session(campaign.metadata.id, session)


@pytest.mark.asyncio
async def test_delete_player_in_active_session(artifact_store):
    """Test that players in active sessions cannot be deleted."""
    campaign_service = CampaignService(store=artifact_store)
    player_service = PlayerService(store=artifact_store)
    session_service = SessionService(store=artifact_store)

    campaign = await campaign_service.create_campaign(
        name="Test Campaign",
        rule_system="shadowdark",
    )
    gm = await player_service.create_player(
        username="gm",
        display_name="Game Master",
    )
    player = await player_service.create_player(
        username="testplayer",
        display_name="Test Player",
    )

    await campaign_service.add_player(campaign.metadata.id, player.metadata.id)

    session = await session_service.create_session(
        campaign_id=campaign.metadata.id,
        started_by=gm.metadata.id,
    )

    await session_service.join_session(
        campaign_id=campaign.metadata.id,
        session_id=session.metadata.id,
        player_id=player.metadata.id,
    )

    # Attempt to delete player
    with pytest.raises(ValueError, match="active session"):
        await player_service.delete_player(player.metadata.id)
