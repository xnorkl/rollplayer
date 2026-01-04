"""Dice rolling models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DiceResult(BaseModel):
    """Result of a dice roll."""

    expression: str  # Original expression (e.g., "2d6+3")
    total: int  # Final result
    rolls: list[int] = Field(default_factory=list)  # Individual die rolls
    modifier: int = Field(default=0)  # Applied modifier
    breakdown: str = ""  # Human-readable breakdown
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    seed: Optional[str] = None  # For reproducibility
