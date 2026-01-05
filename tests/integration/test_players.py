"""Integration tests for player API endpoints."""

import pytest
from fastapi.testclient import TestClient

from gm_chatbot.api.app import create_app
from tests.fixtures.store import artifact_store


@pytest.fixture
def client(artifact_store):
    """Create test client."""
    app = create_app()
    return TestClient(app)


@pytest.mark.asyncio
async def test_create_player_api(artifact_store):
    """Test creating a player via API."""
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/players",
        params={
            "username": "testuser",
            "display_name": "Test User",
            "email": "test@example.com",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["username"] == "testuser"


@pytest.mark.asyncio
async def test_get_player_api(artifact_store):
    """Test getting a player via API."""
    from gm_chatbot.services.player_service import PlayerService

    service = PlayerService(store=artifact_store)
    player = await service.create_player(
        username="testuser",
        display_name="Test User",
    )

    client = TestClient(create_app())
    response = client.get(f"/api/v1/players/{player.metadata.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["username"] == "testuser"


@pytest.mark.asyncio
async def test_username_uniqueness_api(artifact_store):
    """Test username uniqueness enforcement via API."""
    from gm_chatbot.services.player_service import PlayerService

    service = PlayerService(store=artifact_store)
    await service.create_player(username="testuser", display_name="Test User")

    client = TestClient(create_app())
    response = client.post(
        "/api/v1/players",
        params={
            "username": "testuser",
            "display_name": "Another User",
        },
    )

    assert response.status_code == 409
    data = response.json()
    assert data["error"]["code"] == "USERNAME_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_list_players_api(artifact_store):
    """Test listing players via API."""
    from gm_chatbot.services.player_service import PlayerService

    service = PlayerService(store=artifact_store)
    await service.create_player(username="user1", display_name="User One")
    await service.create_player(username="user2", display_name="User Two")

    client = TestClient(create_app())
    response = client.get("/api/v1/players")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) == 2
    # Email should be excluded from list
    for player in data["data"]:
        assert player.get("email") is None


@pytest.mark.asyncio
async def test_get_active_session_no_session(artifact_store):
    """Test getting active session when player has none."""
    from gm_chatbot.services.player_service import PlayerService

    service = PlayerService(store=artifact_store)
    player = await service.create_player(username="testuser", display_name="Test User")

    client = TestClient(create_app())
    response = client.get(f"/api/v1/players/{player.metadata.id}/active-session")

    assert response.status_code == 204
