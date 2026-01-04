"""Game action models."""

from datetime import datetime
from typing import Literal
from uuid import uuid4

from pydantic import Field

from .base import BaseModel
from .dice import DiceResult


class StateChange(BaseModel):
    """Represents a change to game state."""

    target: str  # Entity ID (character, etc.)
    field: str  # Field path (e.g., "combat.hit_points.current")
    old_value: int | str | bool | None
    new_value: int | str | bool | None


class ActionOutcome(BaseModel):
    """Result of a game action."""

    success: bool
    description: str
    state_changes: list[StateChange] = Field(default_factory=list)
    narrative: str = ""  # Flavor text for the action


class GameAction(BaseModel):
    """A discrete game event that transitions game state."""

    action_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    actor_id: str  # Character or GM identifier
    actor_type: Literal["player", "gm"]
    action_type: str  # "attack", "move", "cast_spell", etc.
    target_ids: list[str] = Field(default_factory=list)
    parameters: dict = Field(default_factory=dict)  # Action-specific parameters
    dice_results: list[DiceResult] = Field(default_factory=list)
    outcome: ActionOutcome
