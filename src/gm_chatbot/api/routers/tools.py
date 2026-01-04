"""Tools router."""

from fastapi import APIRouter, Depends, status

from ...api.dependencies import get_dice_tool_registry
from ...api.exceptions import APIError, ErrorCodes
from ...models.chat import APIResponse
from ...models.dice import DiceResult
from ...tools.registry import DiceToolRegistry

router = APIRouter()


@router.post("/tools/dice/roll", response_model=APIResponse[DiceResult])
async def roll_dice(
    expression: str,
    reason: str = "",
    registry: DiceToolRegistry = Depends(get_dice_tool_registry),
):
    """Roll dice using standard notation."""
    try:
        tool = registry.get_dice_tool()
        result = await tool.roll(expression)
        return APIResponse(success=True, data=result)
    except ValueError as e:
        raise APIError(
            ErrorCodes.DICE_EXPRESSION_INVALID,
            f"Invalid dice expression: {str(e)}",
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from e
    except Exception as e:
        raise APIError(
            ErrorCodes.INTERNAL_ERROR,
            f"Failed to roll dice: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e


@router.post("/tools/dice/evaluate")
async def evaluate_expression(
    expression: str,
    context: dict[str, int | str],
    registry: DiceToolRegistry = Depends(get_dice_tool_registry),
):
    """Evaluate mathematical expression with context."""
    try:
        tool = registry.get_dice_tool()
        result = await tool.evaluate(expression, context)
        return APIResponse(success=True, data={"result": result})
    except ValueError as e:
        raise APIError(
            ErrorCodes.DICE_EXPRESSION_INVALID,
            f"Invalid expression: {str(e)}",
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from e
    except Exception as e:
        raise APIError(
            ErrorCodes.INTERNAL_ERROR,
            f"Failed to evaluate expression: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e
