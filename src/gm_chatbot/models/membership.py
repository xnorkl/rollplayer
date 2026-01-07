"""Campaign membership model."""

from typing import Annotated, Any

from pydantic import BeforeValidator, Field

from ..lib.datetime import utc_now
from ..lib.types import UTC_DATETIME, MembershipRole
from .base import BaseArtifact


def _validate_membership_role(v: MembershipRole | str) -> MembershipRole:
    """Convert string to MembershipRole enum."""
    if isinstance(v, str):
        return MembershipRole(v)
    return v


class CampaignMembership(BaseArtifact):
    """Campaign membership artifact representing a player's relationship to a campaign."""

    player_id: str = Field(..., min_length=1)
    campaign_id: str = Field(..., min_length=1)
    role: Annotated[MembershipRole, BeforeValidator(_validate_membership_role)] = Field(
        default=MembershipRole.PLAYER
    )
    character_id: str | None = None  # Default character this player controls
    joined_at: UTC_DATETIME = Field(default_factory=utc_now)

    def model_post_init(self, __context: Any) -> None:
        """Update metadata after initialization."""
        # Metadata timestamps are handled by ArtifactMetadata defaults
        pass
