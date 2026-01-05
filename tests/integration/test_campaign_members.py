"""Integration tests for campaign membership API endpoints."""

import pytest
from fastapi.testclient import TestClient

from gm_chatbot.api.app import create_app
from gm_chatbot.services.campaign_service import CampaignService
from gm_chatbot.services.player_service import PlayerService
from tests.fixtures.store import artifact_store


@pytest.mark.asyncio
async def test_add_player_to_campaign_api(artifact_store):
    """Test adding a player to a campaign via API."""
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

    client = TestClient(create_app())
    response = client.post(
        f"/api/v1/campaigns/{campaign.metadata.id}/players",
        params={
            "player_id": player.metadata.id,
            "role": "player",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["player_id"] == player.metadata.id
    assert data["data"]["role"] == "player"


@pytest.mark.asyncio
async def test_list_campaign_members_api(artifact_store):
    """Test listing campaign members via API."""
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

    client = TestClient(create_app())
    response = client.get(f"/api/v1/campaigns/{campaign.metadata.id}/players")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) == 2


@pytest.mark.asyncio
async def test_update_membership_api(artifact_store):
    """Test updating membership via API."""
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

    client = TestClient(create_app())
    response = client.put(
        f"/api/v1/campaigns/{campaign.metadata.id}/players/{player.metadata.id}",
        params={"role": "gm"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["role"] == "gm"
