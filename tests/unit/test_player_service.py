"""Unit tests for PlayerService."""

import pytest

from gm_chatbot.services.player_service import PlayerService
from tests.fixtures.store import artifact_store


@pytest.mark.asyncio
async def test_create_player(artifact_store):
    """Test creating a player."""
    service = PlayerService(store=artifact_store)
    player = await service.create_player(
        username="testuser",
        display_name="Test User",
        email="test@example.com",
    )

    assert player.username == "testuser"
    assert player.display_name == "Test User"
    assert player.email == "test@example.com"
    assert player.metadata.id is not None


@pytest.mark.asyncio
async def test_get_player(artifact_store):
    """Test retrieving a player."""
    service = PlayerService(store=artifact_store)
    created = await service.create_player(
        username="testuser",
        display_name="Test User",
    )

    retrieved = await service.get_player(created.metadata.id)
    assert retrieved.username == created.username
    assert retrieved.metadata.id == created.metadata.id


@pytest.mark.asyncio
async def test_username_uniqueness(artifact_store):
    """Test username uniqueness validation."""
    service = PlayerService(store=artifact_store)
    await service.create_player(username="testuser", display_name="Test User")

    # Attempt to create duplicate username
    with pytest.raises(ValueError, match="already exists"):
        await service.create_player(username="testuser", display_name="Another User")


@pytest.mark.asyncio
async def test_update_player(artifact_store):
    """Test updating a player."""
    service = PlayerService(store=artifact_store)
    player = await service.create_player(
        username="testuser",
        display_name="Test User",
    )

    player.display_name = "Updated Name"
    updated = await service.update_player(player)

    assert updated.display_name == "Updated Name"


@pytest.mark.asyncio
async def test_delete_player(artifact_store):
    """Test deleting a player."""
    service = PlayerService(store=artifact_store)
    player = await service.create_player(
        username="testuser",
        display_name="Test User",
    )

    await service.delete_player(player.metadata.id)

    with pytest.raises(FileNotFoundError):
        await service.get_player(player.metadata.id)


@pytest.mark.asyncio
async def test_list_players(artifact_store):
    """Test listing players."""
    service = PlayerService(store=artifact_store)
    await service.create_player(username="user1", display_name="User One")
    await service.create_player(username="user2", display_name="User Two")

    players = await service.list_players()
    assert len(players) == 2


@pytest.mark.asyncio
async def test_get_player_active_session_no_session(artifact_store):
    """Test getting active session when player has none."""
    service = PlayerService(store=artifact_store)
    player = await service.create_player(username="testuser", display_name="Test User")

    session = await service.get_player_active_session(player.metadata.id)
    assert session is None
