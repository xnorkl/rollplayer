"""Discord integration router."""

from typing import Optional

from fastapi import APIRouter, Depends, status

from ...api.dependencies import get_discord_binding_service, get_discord_linking_service
from ...api.exceptions import APIError, ErrorCodes
from ...models.chat import APIResponse
from ...models.discord_binding import DiscordBinding
from ...models.discord_link import DiscordLink
from ...services.discord_binding_service import DiscordBindingService
from ...services.discord_linking_service import DiscordLinkingService
from ...services.player_service import PlayerService

router = APIRouter()


@router.post("/discord/links", response_model=APIResponse[DiscordLink], status_code=status.HTTP_201_CREATED)
async def create_discord_link(
    discord_user_id: str,
    discord_username: str,
    player_id: Optional[str] = None,
    guild_id: Optional[str] = None,
    guild_name: Optional[str] = None,
    linking_service: DiscordLinkingService = Depends(get_discord_linking_service),
) -> APIResponse[DiscordLink]:
    """Create Discord link."""
    try:
        link = await linking_service.link_discord_user(
            discord_user_id=discord_user_id,
            discord_username=discord_username,
            player_id=player_id,
            guild_id=guild_id,
            guild_name=guild_name,
        )
        return APIResponse(success=True, data=link)
    except Exception as e:
        raise APIError(
            ErrorCodes.INTERNAL_ERROR,
            f"Failed to create Discord link: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e


@router.get("/discord/links/{discord_user_id}", response_model=APIResponse[dict])
async def get_player_by_discord_id(
    discord_user_id: str,
    linking_service: DiscordLinkingService = Depends(get_discord_linking_service),
) -> APIResponse[dict]:
    """Get player by Discord ID."""
    try:
        player = await linking_service.get_player_by_discord_id(discord_user_id)
        if not player:
            raise APIError(
                ErrorCodes.PLAYER_NOT_FOUND,
                f"Player not found for Discord user {discord_user_id}",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return APIResponse(success=True, data={"player_id": player.metadata.id, "player": player.model_dump()})
    except APIError:
        raise
    except Exception as e:
        raise APIError(
            ErrorCodes.INTERNAL_ERROR,
            f"Failed to get player: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e


@router.delete("/discord/links/{discord_user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unlink_discord_user(
    discord_user_id: str,
    linking_service: DiscordLinkingService = Depends(get_discord_linking_service),
) -> None:
    """Unlink Discord user."""
    try:
        await linking_service.unlink_discord_user(discord_user_id)
    except FileNotFoundError:
        raise APIError(
            ErrorCodes.PLAYER_NOT_FOUND,
            f"Discord link not found for user {discord_user_id}",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        raise APIError(
            ErrorCodes.INTERNAL_ERROR,
            f"Failed to unlink Discord user: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e


@router.get(
    "/campaigns/{campaign_id}/discord-binding",
    response_model=APIResponse[DiscordBinding],
)
async def get_discord_binding(
    campaign_id: str,
    binding_service: DiscordBindingService = Depends(get_discord_binding_service),
) -> APIResponse[DiscordBinding]:
    """Get Discord binding for campaign."""
    try:
        binding = await binding_service.get_binding(campaign_id)
        if not binding:
            raise APIError(
                ErrorCodes.CAMPAIGN_NOT_FOUND,
                f"Discord binding not found for campaign {campaign_id}",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return APIResponse(success=True, data=binding)
    except APIError:
        raise
    except Exception as e:
        raise APIError(
            ErrorCodes.INTERNAL_ERROR,
            f"Failed to get Discord binding: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e


@router.put(
    "/campaigns/{campaign_id}/discord-binding",
    response_model=APIResponse[DiscordBinding],
)
async def create_or_update_discord_binding(
    campaign_id: str,
    guild_id: str,
    channel_id: str,
    channel_name: str,
    bound_by: str,
    settings: Optional[dict] = None,
    binding_service: DiscordBindingService = Depends(get_discord_binding_service),
) -> APIResponse[DiscordBinding]:
    """Create or update Discord binding."""
    try:
        binding = await binding_service.bind_campaign_to_channel(
            campaign_id=campaign_id,
            guild_id=guild_id,
            channel_id=channel_id,
            channel_name=channel_name,
            bound_by=bound_by,
            settings=settings,
        )
        return APIResponse(success=True, data=binding)
    except ValueError as e:
        raise APIError(
            ErrorCodes.VALIDATION_ERROR,
            str(e),
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from e
    except Exception as e:
        raise APIError(
            ErrorCodes.INTERNAL_ERROR,
            f"Failed to create/update Discord binding: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e


@router.delete(
    "/campaigns/{campaign_id}/discord-binding",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_discord_binding(
    campaign_id: str,
    binding_service: DiscordBindingService = Depends(get_discord_binding_service),
) -> None:
    """Remove Discord binding."""
    try:
        await binding_service.unbind_campaign(campaign_id)
    except FileNotFoundError:
        raise APIError(
            ErrorCodes.CAMPAIGN_NOT_FOUND,
            f"Discord binding not found for campaign {campaign_id}",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        raise APIError(
            ErrorCodes.INTERNAL_ERROR,
            f"Failed to delete Discord binding: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e


@router.get(
    "/discord/guilds/{guild_id}/campaigns",
    response_model=APIResponse[list[DiscordBinding]],
)
async def list_campaigns_in_guild(
    guild_id: str,
    binding_service: DiscordBindingService = Depends(get_discord_binding_service),
) -> APIResponse[list[DiscordBinding]]:
    """List campaigns in a Discord guild."""
    try:
        bindings = await binding_service.list_campaigns_in_guild(guild_id)
        return APIResponse(success=True, data=bindings)
    except Exception as e:
        raise APIError(
            ErrorCodes.INTERNAL_ERROR,
            f"Failed to list campaigns: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e
