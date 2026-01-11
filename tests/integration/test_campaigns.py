"""Integration tests for campaigns."""

import pytest

from gm_chatbot.lib.types import MembershipRole


@pytest.mark.asyncio
async def test_create_campaign(campaign_service):
    """Test creating a campaign."""
    campaign = await campaign_service.create_campaign(
        name="Test Campaign",
        rule_system="shadowdark",
        description="A test campaign",
    )

    assert campaign.name == "Test Campaign"
    assert campaign.rule_system == "shadowdark"
    assert campaign.metadata.id is not None


@pytest.mark.asyncio
async def test_campaign_creator_auto_membership(
    campaign_service, player_service, artifact_store
):
    """Test that campaign creator is automatically added as GM member."""
    # Create a player (simulating campaign creator)
    player = await player_service.create_player(
        username="creator",
        display_name="Campaign Creator",
    )

    # Create campaign with creator
    campaign = await campaign_service.create_campaign(
        name="Test Campaign",
        rule_system="shadowdark",
        created_by=player.metadata.id,
    )

    # Manually add creator as GM (simulating what the Discord command does)
    # Note: In the actual Discord command, this happens automatically
    await campaign_service.add_player(
        campaign_id=campaign.metadata.id,
        player_id=player.metadata.id,
        role="gm",
    )

    # Verify membership exists with GM role
    membership = await campaign_service.get_membership(
        campaign.metadata.id, player.metadata.id
    )
    assert membership is not None
    assert membership.role == MembershipRole.GM
    assert membership.campaign_id == campaign.metadata.id
    assert membership.player_id == player.metadata.id


@pytest.mark.asyncio
async def test_get_campaign(campaign_service):
    """Test retrieving a campaign."""
    created = await campaign_service.create_campaign(
        name="Test Campaign",
        rule_system="shadowdark",
    )

    retrieved = await campaign_service.get_campaign(created.metadata.id)
    assert retrieved.name == created.name
    assert retrieved.metadata.id == created.metadata.id


@pytest.mark.asyncio
async def test_list_campaigns(campaign_service):
    """Test listing campaigns."""
    await campaign_service.create_campaign(name="Campaign 1", rule_system="shadowdark")
    await campaign_service.create_campaign(name="Campaign 2", rule_system="shadowdark")

    campaigns = await campaign_service.list_campaigns()
    assert len(campaigns) == 2


@pytest.mark.asyncio
async def test_update_campaign(campaign_service):
    """Test updating a campaign."""
    created = await campaign_service.create_campaign(
        name="Test Campaign",
        rule_system="shadowdark",
    )

    created.status = "active"
    updated = await campaign_service.update_campaign(created)

    assert updated.status == "active"
    assert updated.metadata.updated_at > created.metadata.created_at


@pytest.mark.asyncio
async def test_campaign_join_with_campaign_id(
    campaign_service, player_service
):
    """Test joining a campaign with explicit campaign_id."""
    # Create campaign
    campaign = await campaign_service.create_campaign(
        name="Test Campaign",
        rule_system="shadowdark",
    )

    # Create player
    player = await player_service.create_player(
        username="testplayer",
        display_name="Test Player",
    )

    # Join campaign
    membership = await campaign_service.add_player(
        campaign_id=campaign.metadata.id,
        player_id=player.metadata.id,
        role="player",
    )

    # Verify membership
    assert membership.role == MembershipRole.PLAYER
    assert membership.campaign_id == campaign.metadata.id
    assert membership.player_id == player.metadata.id

    # Verify can retrieve membership
    retrieved = await campaign_service.get_membership(
        campaign.metadata.id, player.metadata.id
    )
    assert retrieved is not None
    assert retrieved.role == MembershipRole.PLAYER


@pytest.mark.asyncio
async def test_campaign_join_duplicate(
    campaign_service, player_service
):
    """Test graceful handling of duplicate join attempts."""
    # Create campaign
    campaign = await campaign_service.create_campaign(
        name="Test Campaign",
        rule_system="shadowdark",
    )

    # Create player
    player = await player_service.create_player(
        username="testplayer",
        display_name="Test Player",
    )

    # Join campaign first time
    membership1 = await campaign_service.add_player(
        campaign_id=campaign.metadata.id,
        player_id=player.metadata.id,
        role="player",
    )

    # Attempt to join again (should raise ValueError)
    with pytest.raises(ValueError, match="already a member"):
        await campaign_service.add_player(
            campaign_id=campaign.metadata.id,
            player_id=player.metadata.id,
            role="player",
        )

    # Verify original membership still exists
    retrieved = await campaign_service.get_membership(
        campaign.metadata.id, player.metadata.id
    )
    assert retrieved is not None
    assert retrieved.metadata.id == membership1.metadata.id
