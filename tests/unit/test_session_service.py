"""Unit tests for SessionService."""

import pytest

from gm_chatbot.services.session_service import SessionService
from gm_chatbot.services.campaign_service import CampaignService
from gm_chatbot.services.player_service import PlayerService
from tests.fixtures.store import artifact_store


@pytest.mark.asyncio
async def test_create_session(artifact_store):
    """Test creating a session."""
    campaign_service = CampaignService(store=artifact_store)
    player_service = PlayerService(store=artifact_store)
    session_service = SessionService(store=artifact_store)

    campaign = await campaign_service.create_campaign(
        name="Test Campaign",
        rule_system="shadowdark",
    )
    player = await player_service.create_player(
        username="gm",
        display_name="Game Master",
    )

    session = await session_service.create_session(
        campaign_id=campaign.metadata.id,
        started_by=player.metadata.id,
        name="Test Session",
    )

    assert session.campaign_id == campaign.metadata.id
    assert session.session_number == 1
    assert session.status == "active"
    assert session.started_by == player.metadata.id


@pytest.mark.asyncio
async def test_single_active_session_per_campaign(artifact_store):
    """Test that only one active session can exist per campaign."""
    campaign_service = CampaignService(store=artifact_store)
    player_service = PlayerService(store=artifact_store)
    session_service = SessionService(store=artifact_store)

    campaign = await campaign_service.create_campaign(
        name="Test Campaign",
        rule_system="shadowdark",
    )
    player = await player_service.create_player(
        username="gm",
        display_name="Game Master",
    )

    # Create first session
    await session_service.create_session(
        campaign_id=campaign.metadata.id,
        started_by=player.metadata.id,
    )

    # Attempt to create second session
    with pytest.raises(ValueError, match="already has an active"):
        await session_service.create_session(
            campaign_id=campaign.metadata.id,
            started_by=player.metadata.id,
        )


@pytest.mark.asyncio
async def test_end_session(artifact_store):
    """Test ending a session."""
    campaign_service = CampaignService(store=artifact_store)
    player_service = PlayerService(store=artifact_store)
    session_service = SessionService(store=artifact_store)

    campaign = await campaign_service.create_campaign(
        name="Test Campaign",
        rule_system="shadowdark",
    )
    player = await player_service.create_player(
        username="gm",
        display_name="Game Master",
    )

    session = await session_service.create_session(
        campaign_id=campaign.metadata.id,
        started_by=player.metadata.id,
    )

    ended = await session_service.end_session(campaign.metadata.id, session.metadata.id)

    assert ended.status == "ended"
    assert ended.ended_at is not None


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
    player = await player_service.create_player(
        username="gm",
        display_name="Game Master",
    )

    session = await session_service.create_session(
        campaign_id=campaign.metadata.id,
        started_by=player.metadata.id,
    )

    # End session
    await session_service.end_session(campaign.metadata.id, session.metadata.id)

    # Attempt to modify ended session
    session.status = "active"
    with pytest.raises(ValueError, match="Cannot modify an ended session"):
        await session_service.update_session(campaign.metadata.id, session)
