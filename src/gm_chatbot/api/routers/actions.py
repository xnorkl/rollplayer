"""Actions router."""

from fastapi import APIRouter, Depends, status

from ...api.dependencies import get_game_state_service
from ...api.exceptions import APIError, ErrorCodes
from ...models.action import GameAction
from ...models.chat import APIResponse
from ...services.game_state_service import GameStateService

router = APIRouter()


@router.get("/campaigns/{campaign_id}/actions", response_model=APIResponse[list[GameAction]])
async def list_actions(
    campaign_id: str,
    limit: int | None = None,
    service: GameStateService = Depends(get_game_state_service),
):
    """List action history for a campaign."""
    try:
        actions = await service.get_action_history(campaign_id, limit)
        return APIResponse(success=True, data=actions)
    except Exception as e:
        raise APIError(
            ErrorCodes.INTERNAL_ERROR,
            f"Failed to list actions: {e!s}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e


@router.post(
    "/campaigns/{campaign_id}/actions",
    response_model=APIResponse[GameAction],
    status_code=status.HTTP_201_CREATED,
)
async def submit_action(
    campaign_id: str,
    action: GameAction,
    service: GameStateService = Depends(get_game_state_service),
):
    """Submit a new game action."""
    try:
        applied = await service.apply_action(campaign_id, action)
        return APIResponse(success=True, data=applied)
    except Exception as e:
        raise APIError(
            ErrorCodes.VALIDATION_ERROR,
            f"Failed to apply action: {e!s}",
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from e


@router.get("/campaigns/{campaign_id}/state")
async def get_game_state(
    campaign_id: str,
    service: GameStateService = Depends(get_game_state_service),
):
    """Get current game state."""
    try:
        state = await service.get_current_state(campaign_id)
        return APIResponse(
            success=True,
            data={
                "campaign_id": state.campaign_id,
                "in_combat": state.in_combat,
                "initiative_order": state.initiative_order,
                "current_turn": state.current_turn,
            },
        )
    except Exception as e:
        raise APIError(
            ErrorCodes.INTERNAL_ERROR,
            f"Failed to get game state: {e!s}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e


@router.post("/campaigns/{campaign_id}/rollback/{action_id}")
async def rollback_action(
    campaign_id: str,
    action_id: str,
    service: GameStateService = Depends(get_game_state_service),
):
    """Rollback to state before specified action."""
    try:
        state = await service.rollback_action(campaign_id, action_id)
        return APIResponse(
            success=True,
            data={
                "campaign_id": state.campaign_id,
                "in_combat": state.in_combat,
                "initiative_order": state.initiative_order,
                "current_turn": state.current_turn,
            },
        )
    except ValueError:
        raise APIError(
            ErrorCodes.NOT_FOUND,
            f"Action {action_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        raise APIError(
            ErrorCodes.INTERNAL_ERROR,
            f"Failed to rollback action: {e!s}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e
