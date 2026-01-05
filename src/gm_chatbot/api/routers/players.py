"""Player router."""

from typing import Optional

from fastapi import APIRouter, Depends, status
from fastapi.responses import Response

from ...api.dependencies import get_player_service
from ...api.exceptions import APIError, ErrorCodes
from ...models.player import Player
from ...models.chat import APIResponse
from ...services.player_service import PlayerService

router = APIRouter()


@router.get("/players", response_model=APIResponse[list[Player]])
async def list_players(
    service: PlayerService = Depends(get_player_service),
):
    """List all players."""
    try:
        players = await service.list_players()
        # Exclude email from list response for privacy
        for player in players:
            player.email = None
        return APIResponse(success=True, data=players)
    except Exception as e:
        raise APIError(
            ErrorCodes.INTERNAL_ERROR,
            f"Failed to list players: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e


@router.post(
    "/players", response_model=APIResponse[Player], status_code=status.HTTP_201_CREATED
)
async def create_player(
    username: str,
    display_name: str,
    email: Optional[str] = None,
    avatar_url: Optional[str] = None,
    player_status: str = "offline",
    service: PlayerService = Depends(get_player_service),
):
    """Register a new player."""
    try:
        player = await service.create_player(
            username=username,
            display_name=display_name,
            email=email,
            avatar_url=avatar_url,
            status=player_status,
        )
        return APIResponse(success=True, data=player)
    except ValueError as e:
        if "already exists" in str(e):
            raise APIError(
                ErrorCodes.USERNAME_ALREADY_EXISTS,
                str(e),
                status_code=status.HTTP_409_CONFLICT,
            ) from e
        raise APIError(
            ErrorCodes.VALIDATION_ERROR,
            f"Failed to create player: {str(e)}",
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from e
    except Exception as e:
        raise APIError(
            ErrorCodes.INTERNAL_ERROR,
            f"Failed to create player: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e


@router.get("/players/{player_id}", response_model=APIResponse[Player])
async def get_player(
    player_id: str,
    service: PlayerService = Depends(get_player_service),
):
    """Get player details."""
    try:
        player = await service.get_player(player_id)
        return APIResponse(success=True, data=player)
    except FileNotFoundError:
        raise APIError(
            ErrorCodes.PLAYER_NOT_FOUND,
            f"Player {player_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        raise APIError(
            ErrorCodes.INTERNAL_ERROR,
            f"Failed to get player: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e


@router.put("/players/{player_id}", response_model=APIResponse[Player])
async def update_player(
    player_id: str,
    player: Player,
    service: PlayerService = Depends(get_player_service),
):
    """Update a player profile."""
    try:
        # Ensure player ID matches
        player.metadata.id = player_id
        updated = await service.update_player(player)
        return APIResponse(success=True, data=updated)
    except FileNotFoundError:
        raise APIError(
            ErrorCodes.PLAYER_NOT_FOUND,
            f"Player {player_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except ValueError as e:
        if "already exists" in str(e):
            raise APIError(
                ErrorCodes.USERNAME_ALREADY_EXISTS,
                str(e),
                status_code=status.HTTP_409_CONFLICT,
            ) from e
        raise APIError(
            ErrorCodes.VALIDATION_ERROR,
            f"Failed to update player: {str(e)}",
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from e
    except Exception as e:
        raise APIError(
            ErrorCodes.INTERNAL_ERROR,
            f"Failed to update player: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e


@router.delete("/players/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_player(
    player_id: str,
    service: PlayerService = Depends(get_player_service),
):
    """Delete a player account."""
    try:
        await service.delete_player(player_id)
    except FileNotFoundError:
        raise APIError(
            ErrorCodes.PLAYER_NOT_FOUND,
            f"Player {player_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except ValueError as e:
        if "active session" in str(e).lower():
            raise APIError(
                ErrorCodes.PLAYER_IN_ACTIVE_SESSION,
                str(e),
                status_code=status.HTTP_409_CONFLICT,
            ) from e
        raise APIError(
            ErrorCodes.VALIDATION_ERROR,
            f"Failed to delete player: {str(e)}",
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from e
    except Exception as e:
        raise APIError(
            ErrorCodes.INTERNAL_ERROR,
            f"Failed to delete player: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e


@router.get("/players/{player_id}/campaigns", response_model=APIResponse[list[dict]])
async def get_player_campaigns(
    player_id: str,
    service: PlayerService = Depends(get_player_service),
):
    """List player's campaign memberships."""
    try:
        campaigns = await service.get_player_campaigns(player_id)
        return APIResponse(success=True, data=campaigns)
    except FileNotFoundError:
        raise APIError(
            ErrorCodes.PLAYER_NOT_FOUND,
            f"Player {player_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        raise APIError(
            ErrorCodes.INTERNAL_ERROR,
            f"Failed to get player campaigns: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e


@router.get("/players/{player_id}/active-session", response_model=APIResponse[dict])
async def get_player_active_session(
    player_id: str,
    service: PlayerService = Depends(get_player_service),
):
    """Get player's current active session (if any)."""
    try:
        session = await service.get_player_active_session(player_id)
        if session is None:
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        return APIResponse(
            success=True,
            data={
                "session_id": session.metadata.id,
                "campaign_id": session.campaign_id,
                "session_number": session.session_number,
                "name": session.name,
                "status": session.status,
            },
        )
    except FileNotFoundError:
        raise APIError(
            ErrorCodes.PLAYER_NOT_FOUND,
            f"Player {player_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        raise APIError(
            ErrorCodes.INTERNAL_ERROR,
            f"Failed to get player active session: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e
