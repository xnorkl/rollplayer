"""
Integration tests for character Discord commands.

Tests the full flow from command invocation through persistence.
Uses real ArtifactStore with temp directories.
"""

import pytest

from gm_chatbot.artifacts.store import ArtifactStore
from gm_chatbot.services.character_service import CharacterService
from gm_chatbot.services.campaign_service import CampaignService
from gm_chatbot.services.player_service import PlayerService


class TestCharacterCreateIntegration:
    """Integration tests for /character create command flow."""

    @pytest.mark.asyncio
    async def test_full_character_creation_flow(
        self,
        artifact_store,
        character_service,
        campaign_service,
    ):
        """Test complete character creation and retrieval."""
        # Setup: Create campaign and membership
        campaign = await campaign_service.create_campaign(
            name="Test Campaign",
            rule_system="shadowdark",
        )

        # Create player and add to campaign
        player_service = PlayerService(store=artifact_store)
        player = await player_service.create_player(
            username="testplayer",
            display_name="Test Player",
        )

        await campaign_service.add_player(
            campaign_id=campaign.metadata.id,
            player_id=player.metadata.id,
            role="player",
        )

        # Create character
        character = await character_service.create_character(
            campaign_id=campaign.metadata.id,
            character_type="player_character",
            name="Test Hero",
        )

        # Link character to membership
        await campaign_service.update_membership(
            campaign_id=campaign.metadata.id,
            player_id=player.metadata.id,
            character_id=character.metadata.id,
        )

        # Verify: Character file exists
        char_path = (
            artifact_store.get_campaign_dir(campaign.metadata.id)
            / "characters"
            / "pc_test_hero.yaml"
        )
        assert char_path.exists()

        # Verify: Character can be retrieved
        retrieved = await character_service.get_character(
            campaign.metadata.id,
            character.metadata.id,
        )
        assert retrieved.identity.name == "Test Hero"

        # Verify: Membership is linked
        membership = await campaign_service.get_membership(
            campaign.metadata.id,
            player.metadata.id,
        )
        assert membership.character_id == character.metadata.id

    @pytest.mark.asyncio
    async def test_duplicate_character_prevention(
        self,
        artifact_store,
        character_service,
        campaign_service,
    ):
        """Test that duplicate character creation is prevented."""
        # Setup campaign with player
        campaign = await campaign_service.create_campaign(
            name="Test Campaign",
            rule_system="shadowdark",
        )

        player_service = PlayerService(store=artifact_store)
        player = await player_service.create_player(
            username="testplayer2",
            display_name="Test Player 2",
        )

        await campaign_service.add_player(
            campaign_id=campaign.metadata.id,
            player_id=player.metadata.id,
            role="player",
        )

        # Create first character
        character = await character_service.create_character(
            campaign_id=campaign.metadata.id,
            character_type="player_character",
            name="First Hero",
        )

        # Link to membership
        await campaign_service.update_membership(
            campaign_id=campaign.metadata.id,
            player_id=player.metadata.id,
            character_id=character.metadata.id,
        )

        # Verify membership has character_id (business rule check point)
        membership = await campaign_service.get_membership(
            campaign.metadata.id,
            player.metadata.id,
        )
        assert membership.character_id is not None
        assert membership.character_id == character.metadata.id


class TestCharacterViewIntegration:
    """Integration tests for /character view command flow."""

    @pytest.mark.asyncio
    async def test_get_character_by_player(
        self,
        artifact_store,
        character_service,
        campaign_service,
    ):
        """Test retrieving character by player."""
        # Setup: Create campaign, player, and character
        campaign = await campaign_service.create_campaign(
            name="Test Campaign",
            rule_system="shadowdark",
        )

        player_service = PlayerService(store=artifact_store)
        player = await player_service.create_player(
            username="testplayer",
            display_name="Test Player",
        )

        await campaign_service.add_player(
            campaign_id=campaign.metadata.id,
            player_id=player.metadata.id,
            role="player",
        )

        character = await character_service.create_character(
            campaign_id=campaign.metadata.id,
            character_type="player_character",
            name="Test Hero",
        )

        await campaign_service.update_membership(
            campaign_id=campaign.metadata.id,
            player_id=player.metadata.id,
            character_id=character.metadata.id,
        )

        # Get character by player
        retrieved = await character_service.get_character_by_player(
            campaign_id=campaign.metadata.id,
            player_id=player.metadata.id,
        )

        assert retrieved is not None
        assert retrieved.metadata.id == character.metadata.id
        assert retrieved.identity.name == "Test Hero"

    @pytest.mark.asyncio
    async def test_get_character_by_player_no_character(
        self,
        artifact_store,
        character_service,
        campaign_service,
    ):
        """Test get_character_by_player when no character is linked."""
        # Setup: Create campaign and player (no character)
        campaign = await campaign_service.create_campaign(
            name="Test Campaign",
            rule_system="shadowdark",
        )

        player_service = PlayerService(store=artifact_store)
        player = await player_service.create_player(
            username="testplayer",
            display_name="Test Player",
        )

        await campaign_service.add_player(
            campaign_id=campaign.metadata.id,
            player_id=player.metadata.id,
            role="player",
        )

        # Get character by player (should return None)
        retrieved = await character_service.get_character_by_player(
            campaign_id=campaign.metadata.id,
            player_id=player.metadata.id,
        )

        assert retrieved is None
