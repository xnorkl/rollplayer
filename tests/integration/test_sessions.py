"""Integration tests for session API endpoints."""

import pytest
from fastapi.testclient import TestClient

from gm_chatbot.api.app import create_app
from gm_chatbot.services.campaign_service import CampaignService
from gm_chatbot.services.player_service import PlayerService
from tests.fixtures.store import artifact_store


@pytest.mark.asyncio
async def test_create_session_api(artifact_store):
    """Test creating a session via API."""
    campaign_service = CampaignService(store=artifact_store)
    player_service = PlayerService(store=artifact_store)

    campaign = await campaign_service.create_campaign(
        name="Test Campaign",
        rule_system="shadowdark",
    )
    player = await player_service.create_player(
        username="gm",
        display_name="Game Master",
    )

    client = TestClient(create_app())
    response = client.post(
        f"/api/v1/campaigns/{campaign.metadata.id}/sessions",
        params={
            "started_by": player.metadata.id,
            "name": "Test Session",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "active"


@pytest.mark.asyncio
async def test_single_active_session_constraint_api(artifact_store):
    """Test single active session per campaign constraint via API."""
    campaign_service = CampaignService(store=artifact_store)
    player_service = PlayerService(store=artifact_store)

    campaign = await campaign_service.create_campaign(
        name="Test Campaign",
        rule_system="shadowdark",
    )
    player = await player_service.create_player(
        username="gm",
        display_name="Game Master",
    )

    client = TestClient(create_app())

    # Create first session
    response1 = client.post(
        f"/api/v1/campaigns/{campaign.metadata.id}/sessions",
        params={"started_by": player.metadata.id},
    )
    assert response1.status_code == 201

    # Attempt to create second session
    response2 = client.post(
        f"/api/v1/campaigns/{campaign.metadata.id}/sessions",
        params={"started_by": player.metadata.id},
    )
    assert response2.status_code == 409
    assert response2.json()["error"]["code"] == "SESSION_ALREADY_ACTIVE"


@pytest.mark.asyncio
async def test_end_session_api(artifact_store):
    """Test ending a session via API."""
    from gm_chatbot.services.session_service import SessionService

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

    client = TestClient(create_app())
    response = client.post(
        f"/api/v1/campaigns/{campaign.metadata.id}/sessions/{session.metadata.id}/end"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "ended"


@pytest.mark.asyncio
async def test_delete_ended_session_api(artifact_store):
    """Test deleting an ended session via API."""
    from gm_chatbot.services.session_service import SessionService

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
    await session_service.end_session(campaign.metadata.id, session.metadata.id)

    client = TestClient(create_app())
    response = client.delete(
        f"/api/v1/campaigns/{campaign.metadata.id}/sessions/{session.metadata.id}"
    )

    assert response.status_code == 204
