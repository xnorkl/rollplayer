"""Data fixtures for testing."""

import pytest


@pytest.fixture
async def player(player_service):
    """Create a sample player."""
    return await player_service.create_player(
        username="testplayer",
        display_name="Test Player",
        email="test@example.com",
        status="online",
    )


@pytest.fixture
async def campaign(campaign_service):
    """Create a sample campaign."""
    return await campaign_service.create_campaign(
        name="Test Campaign",
        rule_system="shadowdark",
        description="A test campaign",
    )


@pytest.fixture
async def campaign_with_members(campaign_service, player_service):
    """Create a campaign with multiple members."""
    campaign = await campaign_service.create_campaign(
        name="Campaign with Members",
        rule_system="shadowdark",
    )

    # Create players
    player1 = await player_service.create_player(
        username="player1",
        display_name="Player One",
        status="online",
    )
    player2 = await player_service.create_player(
        username="player2",
        display_name="Player Two",
        status="online",
    )
    gm = await player_service.create_player(
        username="gm",
        display_name="Game Master",
        status="online",
    )

    # Add members
    await campaign_service.add_player(campaign.metadata.id, player1.metadata.id, role="player")
    await campaign_service.add_player(campaign.metadata.id, player2.metadata.id, role="player")
    await campaign_service.add_player(campaign.metadata.id, gm.metadata.id, role="gm")

    return {
        "campaign": campaign,
        "player1": player1,
        "player2": player2,
        "gm": gm,
    }


@pytest.fixture
async def character(campaign, character_service):
    """Create a sample character."""
    return await character_service.create_character(
        campaign_id=campaign.metadata.id,
        character_type="player_character",
        name="Test Character",
        identity={"name": "Test Character", "level": 1},
    )


@pytest.fixture
async def active_session(campaign_with_members, session_service):
    """Create an active session with participants."""
    campaign = campaign_with_members["campaign"]
    gm = campaign_with_members["gm"]

    session = await session_service.create_session(
        campaign_id=campaign.metadata.id,
        started_by=gm.metadata.id,
        name="Test Session",
    )

    # Add participants
    await session_service.join_session(
        campaign_id=campaign.metadata.id,
        session_id=session.metadata.id,
        player_id=campaign_with_members["player1"].metadata.id,
        is_gm=False,
    )
    await session_service.join_session(
        campaign_id=campaign.metadata.id,
        session_id=session.metadata.id,
        player_id=gm.metadata.id,
        is_gm=True,
    )

    # Reload session to get updated participants
    return await session_service.get_session(campaign.metadata.id, session.metadata.id)


@pytest.fixture
async def ended_session(active_session, session_service):
    """Create an ended session."""
    campaign_id = active_session.campaign_id
    session_id = active_session.metadata.id

    ended = await session_service.end_session(campaign_id, session_id)
    return ended
