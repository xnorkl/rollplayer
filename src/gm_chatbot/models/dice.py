"""Dice rolling models."""

from datetime import datetime

from pydantic import BaseModel, Field

from ..lib.datetime import utc_now


class DiceResult(BaseModel):
    """Result of a dice roll."""

    expression: str  # Original expression (e.g., "2d6+3")
    total: int  # Final result
    rolls: list[int] = Field(default_factory=list)  # Individual die rolls
    modifier: int = Field(default=0)  # Applied modifier
    breakdown: str = ""  # Human-readable breakdown
    timestamp: datetime = Field(default_factory=utc_now)
    seed: str | None = None  # For reproducibility
