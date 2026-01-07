"""Campaign model."""

from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, Field

from ..lib.types import CampaignStatus
from .base import BaseArtifact


def _validate_campaign_status(v: CampaignStatus | str) -> CampaignStatus:
    """Convert string to CampaignStatus enum."""
    if isinstance(v, str):
        return CampaignStatus(v)
    return v


class CampaignCreate(BaseModel):
    """Request model for creating a campaign."""

    name: str = Field(..., min_length=1)
    rule_system: str = Field(..., min_length=1)  # e.g., "shadowdark", "dnd5e"
    description: str | None = None
    created_by: str | None = None


class Campaign(BaseArtifact):
    """Campaign artifact representing a game world."""

    name: str = Field(..., min_length=1)
    rule_system: str = Field(..., min_length=1)  # e.g., "shadowdark", "dnd5e"
    status: Annotated[CampaignStatus, BeforeValidator(_validate_campaign_status)] = (
        Field(default=CampaignStatus.DRAFT)
    )
    description: str | None = None
    created_by: str | None = None
    active_module_id: str | None = None  # ID of currently active session module

    def model_post_init(self, __context: Any) -> None:
        """Update metadata after initialization."""
        # Metadata timestamps are handled by ArtifactMetadata defaults
        pass
