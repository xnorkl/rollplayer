"""Integration tests for campaigns."""

import pytest


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
