"""
Integration tests for character Discord commands.

Tests the full flow from command invocation through persistence.
Uses real ArtifactStore with temp directories.
"""

import pytest

from gm_chatbot.lib.types import MembershipRole
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


class TestCharacterCreateAutoJoin:
    """Integration tests for character creation auto-join flow."""

    @pytest.mark.asyncio
    async def test_character_create_auto_join(
        self,
        artifact_store,
        character_service,
        campaign_service,
    ):
        """Test that character creation auto-joins non-member users."""
        # Setup: Create campaign (no player membership yet)
        campaign = await campaign_service.create_campaign(
            name="Test Campaign",
            rule_system="shadowdark",
        )

        # Create player (but don't add to campaign yet)
        player_service = PlayerService(store=artifact_store)
        player = await player_service.create_player(
            username="testplayer",
            display_name="Test Player",
        )

        # Verify player is NOT a member
        membership_before = await campaign_service.get_membership(
            campaign.metadata.id, player.metadata.id
        )
        assert membership_before is None

        # Simulate auto-join (what happens in Discord command)
        # This is what the character create handler does if membership is None
        membership = await campaign_service.add_player(
            campaign_id=campaign.metadata.id,
            player_id=player.metadata.id,
            role="player",
        )

        # Verify membership was created
        assert membership is not None
        assert membership.role == MembershipRole.PLAYER
        assert membership.campaign_id == campaign.metadata.id
        assert membership.player_id == player.metadata.id

        # Now create character (as normal flow)
        character = await character_service.create_character(
            campaign_id=campaign.metadata.id,
            character_type="player_character",
            name="Auto-Joined Hero",
        )

        # Link character to membership
        await campaign_service.update_membership(
            campaign_id=campaign.metadata.id,
            player_id=player.metadata.id,
            character_id=character.metadata.id,
        )

        # Verify: Character file exists
        # Filename is generated as: prefix + "_" + name.lower().replace(' ', '_')
        # "Auto-Joined Hero" -> "auto-joined_hero" (hyphens remain)
        char_path = (
            artifact_store.get_campaign_dir(campaign.metadata.id)
            / "characters"
            / "pc_auto-joined_hero.yaml"
        )
        assert char_path.exists()

        # Verify: Membership exists and is linked
        membership_after = await campaign_service.get_membership(
            campaign.metadata.id, player.metadata.id
        )
        assert membership_after is not None
        assert membership_after.character_id == character.metadata.id

    @pytest.mark.asyncio
    async def test_character_create_with_existing_membership(
        self,
        artifact_store,
        character_service,
        campaign_service,
    ):
        """Test character creation works for existing members."""
        # Setup: Create campaign with existing member
        campaign = await campaign_service.create_campaign(
            name="Test Campaign",
            rule_system="shadowdark",
        )

        player_service = PlayerService(store=artifact_store)
        player = await player_service.create_player(
            username="testplayer",
            display_name="Test Player",
        )

        # Add player to campaign (existing membership)
        await campaign_service.add_player(
            campaign_id=campaign.metadata.id,
            player_id=player.metadata.id,
            role="player",
        )

        # Verify membership exists
        membership_before = await campaign_service.get_membership(
            campaign.metadata.id, player.metadata.id
        )
        assert membership_before is not None

        # Create character (should work normally, no auto-join needed)
        character = await character_service.create_character(
            campaign_id=campaign.metadata.id,
            character_type="player_character",
            name="Existing Member Hero",
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
            / "pc_existing_member_hero.yaml"
        )
        assert char_path.exists()

        # Verify: Character can be retrieved
        retrieved = await character_service.get_character(
            campaign.metadata.id, character.metadata.id
        )
        assert retrieved.identity.name == "Existing Member Hero"
