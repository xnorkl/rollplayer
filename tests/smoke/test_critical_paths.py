"""Pytest smoke tests for critical paths.

Run with: pytest -m smoke
"""

from __future__ import annotations

from datetime import timezone

import pytest

pytestmark = pytest.mark.smoke


class TestPlayerSmoke:
    """Player service smoke tests."""

    async def test_create_player(self, smoke_services):
        """Can create player with valid data."""
        svc = smoke_services["player"]
        player = await svc.create_player("pytest_smoke", "Pytest Smoke")

        assert player.metadata.id
        assert player.username == "pytest_smoke"

    async def test_player_roundtrip(self, smoke_services):
        """Player survives save/load."""
        svc = smoke_services["player"]
        created = await svc.create_player("roundtrip", "Roundtrip")

        loaded = await svc.get_player(created.metadata.id)

        assert loaded is not None
        assert loaded.metadata.id == created.metadata.id
        assert loaded.metadata.created_at.tzinfo == timezone.utc


class TestCampaignSmoke:
    """Campaign service smoke tests."""

    async def test_create_campaign(self, smoke_services):
        """Can create campaign."""
        svc = smoke_services["campaign"]
        campaign = await svc.create_campaign("Pytest Quest", "shadowdark")

        assert campaign.metadata.id
        assert campaign.status == "draft"

    async def test_add_player_to_campaign(self, smoke_services):
        """Can add player to campaign."""
        player = await smoke_services["player"].create_player("joiner", "Joiner")
        campaign = await smoke_services["campaign"].create_campaign(
            "Joinable", "shadowdark"
        )

        membership = await smoke_services["campaign"].add_player(
            campaign.metadata.id,
            player.metadata.id,
        )

        assert membership.player_id == player.metadata.id


class TestCharacterSmoke:
    """Character service smoke tests."""

    async def test_create_character(self, smoke_services):
        """Can create character."""
        character = await smoke_services["character"].create_character(
            "Test Character", "shadowdark"
        )

        assert character.metadata.id
        assert character.identity.name == "Test Character"
        assert character.character_type == "player_character"


class TestIntegrationSmoke:
    """Integration smoke tests."""

    async def test_full_workflow(self, smoke_services):
        """Complete game setup workflow."""
        # Setup
        gm = await smoke_services["player"].create_player("smoke_gm", "Smoke GM")
        player = await smoke_services["player"].create_player(
            "smoke_player", "Smoke Player"
        )
        campaign = await smoke_services["campaign"].create_campaign(
            "Smoke Campaign", "dnd5e"
        )

        # Add members
        await smoke_services["campaign"].add_player(
            campaign.metadata.id, gm.metadata.id, role="gm"
        )
        await smoke_services["campaign"].add_player(
            campaign.metadata.id, player.metadata.id
        )

        # Start session
        session = await smoke_services["session"].create_session(
            campaign.metadata.id, gm.metadata.id
        )

        assert session.status == "active"

        # End session
        ended = await smoke_services["session"].end_session(
            campaign.metadata.id, session.metadata.id
        )

        assert ended.status == "ended"
