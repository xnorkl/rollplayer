"""Rules router."""

import os

from fastapi import APIRouter, Depends, status

from ...api.exceptions import APIError, ErrorCodes
from ...models.chat import APIResponse
from ...models.rules import RuleSet
from ...rules.engine import RulesEngine

router = APIRouter()

# Global rules engine instance
_rules_engine: RulesEngine | None = None


def get_rules_engine() -> RulesEngine:
    """Get rules engine instance."""
    global _rules_engine
    if _rules_engine is None:
        rules_dir = os.getenv("RULES_DIR", "/data/rules")
        _rules_engine = RulesEngine(rules_dir=rules_dir)
    return _rules_engine


@router.get("/rules/{system}", response_model=APIResponse[RuleSet])
async def get_rules(
    system: str,
    version: str | None = None,
    engine: RulesEngine = Depends(get_rules_engine),
):
    """Get rule definitions for a game system."""
    try:
        ruleset = engine.load_system(system, version)
        return APIResponse(success=True, data=ruleset)
    except FileNotFoundError:
        raise APIError(
            ErrorCodes.NOT_FOUND,
            f"Rules for system '{system}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        raise APIError(
            ErrorCodes.INTERNAL_ERROR,
            f"Failed to load rules: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e
