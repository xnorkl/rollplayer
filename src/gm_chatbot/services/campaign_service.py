"""Campaign service for CRUD operations."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4

from ..artifacts.store import ArtifactStore
from ..artifacts.validator import ArtifactValidator
from ..models.campaign import Campaign
from ..models.membership import CampaignMembership


class CampaignService:
    """Service for managing campaigns."""

    def __init__(self, store: Optional[ArtifactStore] = None):
        """
        Initialize campaign service.

        Args:
            store: Optional artifact store (creates default if not provided)
        """
        self.store = store or ArtifactStore()
        self.validator = ArtifactValidator()

    async def create_campaign(
        self,
        name: str,
        rule_system: str,
        description: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> Campaign:
        """
        Create a new campaign.

        Args:
            name: Campaign name
            rule_system: Game system (e.g., "shadowdark")
            description: Optional description
            created_by: Optional creator identifier

        Returns:
            Created campaign
        """
        campaign_id = str(uuid4())
        campaign = Campaign(
            name=name,
            rule_system=rule_system,
            description=description,
            created_by=created_by,
            status="draft",
        )
        campaign.metadata.id = campaign_id

        # Validate before saving
        self.validator.validate_campaign(campaign.model_dump())

        # Create campaign directory structure
        campaign_dir = self.store.get_campaign_dir(campaign_id)
        campaign_dir.mkdir(parents=True, exist_ok=True)
        (campaign_dir / "characters").mkdir(exist_ok=True)
        (campaign_dir / "modules").mkdir(exist_ok=True)
        (campaign_dir / "state").mkdir(exist_ok=True)
        (campaign_dir / "memberships").mkdir(exist_ok=True)
        (campaign_dir / "sessions").mkdir(exist_ok=True)

        # Save campaign.yaml
        self.store.save_artifact(campaign, campaign_id, "campaign", "campaign.yaml")

        return campaign

    async def get_campaign(self, campaign_id: str) -> Campaign:
        """
        Get a campaign by ID.

        Args:
            campaign_id: Campaign identifier

        Returns:
            Campaign instance

        Raises:
            FileNotFoundError: If campaign not found
        """
        return self.store.load_artifact(Campaign, campaign_id, "campaign.yaml")

    async def update_campaign(self, campaign: Campaign) -> Campaign:
        """
        Update a campaign.

        Args:
            campaign: Updated campaign instance

        Returns:
            Updated campaign
        """
        # Validate before saving
        self.validator.validate_campaign(campaign.model_dump())

        # Update timestamp
        campaign.metadata.updated_at = datetime.now(timezone.utc)

        # Save
        self.store.save_artifact(
            campaign, campaign.metadata.id, "campaign", "campaign.yaml"
        )

        return campaign

    async def list_campaigns(self) -> list[Campaign]:
        """
        List all campaigns.

        Returns:
            List of campaigns
        """
        campaigns = []
        if not self.store.campaigns_dir.exists():
            return campaigns

        for campaign_dir in self.store.campaigns_dir.iterdir():
            if campaign_dir.is_dir():
                try:
                    campaign = await self.get_campaign(campaign_dir.name)
                    campaigns.append(campaign)
                except FileNotFoundError:
                    # Skip if campaign.yaml doesn't exist
                    continue

        return campaigns

    async def delete_campaign(self, campaign_id: str) -> None:
        """
        Delete a campaign and all its artifacts.

        Args:
            campaign_id: Campaign identifier
        """
        campaign_dir = self.store.get_campaign_dir(campaign_id)
        if campaign_dir.exists():
            import shutil

            shutil.rmtree(campaign_dir)

    async def add_player(
        self,
        campaign_id: str,
        player_id: str,
        role: str = "player",
        character_id: Optional[str] = None,
    ) -> CampaignMembership:
        """
        Add a player to a campaign.

        Args:
            campaign_id: Campaign identifier
            player_id: Player identifier
            role: Membership role (player, gm, spectator)
            character_id: Optional default character ID

        Returns:
            Created membership

        Raises:
            ValueError: If player is already a member
        """
        # Check if already a member
        existing = await self.get_membership(campaign_id, player_id)
        if existing is not None:
            raise ValueError(
                f"Player {player_id} is already a member of campaign {campaign_id}"
            )

        membership = CampaignMembership(
            player_id=player_id,
            campaign_id=campaign_id,
            role=role,
            character_id=character_id,
        )
        membership.metadata.id = str(uuid4())

        # Ensure memberships directory exists
        memberships_dir = self.store.get_memberships_dir(campaign_id)
        memberships_dir.mkdir(parents=True, exist_ok=True)

        # Save membership
        self.store.save_artifact(
            membership, campaign_id, "membership", f"memberships/{player_id}.yaml"
        )

        return membership

    async def remove_player(self, campaign_id: str, player_id: str) -> None:
        """
        Remove a player from a campaign.

        Args:
            campaign_id: Campaign identifier
            player_id: Player identifier

        Raises:
            ValueError: If player is in an active session
        """
        # Check if player is in active session
        from ..services.session_service import SessionService

        session_service = SessionService(self.store)
        active_session = await session_service.get_active_session(campaign_id)
        if active_session:
            for participant in active_session.participants:
                if participant.player_id == player_id and participant.left_at is None:
                    raise ValueError(
                        f"Cannot remove player {player_id}: player is in active session {active_session.metadata.id}"
                    )

        # Delete membership file
        memberships_dir = self.store.get_memberships_dir(campaign_id)
        membership_file = memberships_dir / f"{player_id}.yaml"
        if membership_file.exists():
            membership_file.unlink()
        else:
            raise FileNotFoundError(
                f"Membership not found for player {player_id} in campaign {campaign_id}"
            )

    async def update_membership(
        self,
        campaign_id: str,
        player_id: str,
        role: Optional[str] = None,
        character_id: Optional[str] = None,
    ) -> CampaignMembership:
        """
        Update a campaign membership.

        Args:
            campaign_id: Campaign identifier
            player_id: Player identifier
            role: Optional new role
            character_id: Optional new character ID

        Returns:
            Updated membership
        """
        membership = await self.get_membership(campaign_id, player_id)
        if membership is None:
            raise FileNotFoundError(
                f"Membership not found for player {player_id} in campaign {campaign_id}"
            )

        if role is not None:
            membership.role = role
        if character_id is not None:
            membership.character_id = character_id

        membership.metadata.updated_at = datetime.utcnow()

        # Save
        self.store.save_artifact(
            membership, campaign_id, "membership", f"memberships/{player_id}.yaml"
        )

        return membership

    async def list_members(
        self, campaign_id: str, include_character_details: bool = False
    ) -> list[dict]:
        """
        List campaign members.

        Args:
            campaign_id: Campaign identifier
            include_character_details: Whether to include character details

        Returns:
            List of membership dictionaries
        """
        memberships = []
        memberships_dir = self.store.get_memberships_dir(campaign_id)
        if not memberships_dir.exists():
            return memberships

        for membership_file in memberships_dir.glob("*.yaml"):
            try:
                membership = self.store.load_artifact(
                    CampaignMembership,
                    campaign_id,
                    f"memberships/{membership_file.name}",
                )
                member_data = {
                    "player_id": membership.player_id,
                    "role": membership.role,
                    "character_id": membership.character_id,
                    "joined_at": membership.joined_at,
                }

                if include_character_details and membership.character_id:
                    from ..services.character_service import CharacterService

                    char_service = CharacterService(self.store)
                    try:
                        character = await char_service.get_character(
                            campaign_id, membership.character_id
                        )
                        member_data["character"] = {
                            "id": character.metadata.id,
                            "name": character.identity.name,
                            "type": character.character_type,
                        }
                    except Exception:
                        pass

                memberships.append(member_data)
            except Exception:
                continue

        return memberships

    async def get_membership(
        self, campaign_id: str, player_id: str
    ) -> Optional[CampaignMembership]:
        """
        Get a specific membership record.

        Args:
            campaign_id: Campaign identifier
            player_id: Player identifier

        Returns:
            Membership instance or None if not found
        """
        memberships_dir = self.store.get_memberships_dir(campaign_id)
        membership_file = memberships_dir / f"{player_id}.yaml"
        if membership_file.exists():
            try:
                return self.store.load_artifact(
                    CampaignMembership, campaign_id, f"memberships/{player_id}.yaml"
                )
            except Exception:
                return None
        return None
