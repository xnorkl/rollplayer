"""Campaign router."""

from typing import Optional

from fastapi import APIRouter, Depends, status

from ...api.dependencies import get_campaign_service
from ...api.exceptions import APIError, ErrorCodes
from ...models.campaign import Campaign
from ...models.chat import APIResponse
from ...services.campaign_service import CampaignService

router = APIRouter()


@router.get("/campaigns", response_model=APIResponse[list[Campaign]])
async def list_campaigns(
    service: CampaignService = Depends(get_campaign_service),
):
    """List all campaigns."""
    try:
        campaigns = await service.list_campaigns()
        return APIResponse(success=True, data=campaigns)
    except Exception as e:
        raise APIError(
            ErrorCodes.INTERNAL_ERROR,
            f"Failed to list campaigns: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e


@router.post("/campaigns", response_model=APIResponse[Campaign], status_code=status.HTTP_201_CREATED)
async def create_campaign(
    name: str,
    rule_system: str,
    description: Optional[str] = None,
    created_by: Optional[str] = None,
    service: CampaignService = Depends(get_campaign_service),
):
    """Create a new campaign."""
    try:
        campaign = await service.create_campaign(
            name=name,
            rule_system=rule_system,
            description=description,
            created_by=created_by,
        )
        return APIResponse(success=True, data=campaign)
    except Exception as e:
        raise APIError(
            ErrorCodes.VALIDATION_ERROR,
            f"Failed to create campaign: {str(e)}",
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from e


@router.get("/campaigns/{campaign_id}", response_model=APIResponse[Campaign])
async def get_campaign(
    campaign_id: str,
    service: CampaignService = Depends(get_campaign_service),
):
    """Get campaign details."""
    try:
        campaign = await service.get_campaign(campaign_id)
        return APIResponse(success=True, data=campaign)
    except FileNotFoundError:
        raise APIError(
            ErrorCodes.CAMPAIGN_NOT_FOUND,
            f"Campaign {campaign_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        raise APIError(
            ErrorCodes.INTERNAL_ERROR,
            f"Failed to get campaign: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e


@router.put("/campaigns/{campaign_id}", response_model=APIResponse[Campaign])
async def update_campaign(
    campaign_id: str,
    campaign: Campaign,
    service: CampaignService = Depends(get_campaign_service),
):
    """Update a campaign."""
    try:
        # Ensure campaign ID matches
        campaign.metadata.id = campaign_id
        updated = await service.update_campaign(campaign)
        return APIResponse(success=True, data=updated)
    except FileNotFoundError:
        raise APIError(
            ErrorCodes.CAMPAIGN_NOT_FOUND,
            f"Campaign {campaign_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        raise APIError(
            ErrorCodes.VALIDATION_ERROR,
            f"Failed to update campaign: {str(e)}",
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from e


@router.delete("/campaigns/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    campaign_id: str,
    service: CampaignService = Depends(get_campaign_service),
):
    """Delete a campaign."""
    try:
        await service.delete_campaign(campaign_id)
    except Exception as e:
        raise APIError(
            ErrorCodes.INTERNAL_ERROR,
            f"Failed to delete campaign: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e


@router.post("/campaigns/{campaign_id}/activate-module")
async def activate_module(
    campaign_id: str,
    module_id: str,
    service: CampaignService = Depends(get_campaign_service),
):
    """Set active module for a campaign."""
    try:
        campaign = await service.get_campaign(campaign_id)
        campaign.active_module_id = module_id
        updated = await service.update_campaign(campaign)
        return APIResponse(success=True, data=updated)
    except FileNotFoundError:
        raise APIError(
            ErrorCodes.CAMPAIGN_NOT_FOUND,
            f"Campaign {campaign_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        raise APIError(
            ErrorCodes.INTERNAL_ERROR,
            f"Failed to activate module: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e
