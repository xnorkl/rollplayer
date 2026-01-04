"""Campaign service for CRUD operations."""

from pathlib import Path
from typing import Optional
from uuid import uuid4

from ..artifacts.store import ArtifactStore
from ..artifacts.validator import ArtifactValidator
from ..models.campaign import Campaign


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
        from datetime import datetime

        campaign.metadata.updated_at = datetime.utcnow()

        # Save
        self.store.save_artifact(campaign, campaign.metadata.id, "campaign", "campaign.yaml")

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
