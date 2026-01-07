"""Character sheet model."""

from typing import Annotated

from pydantic import BaseModel, BeforeValidator, Field

from ..lib.types import CharacterType
from .base import BaseArtifact


class CharacterIdentity(BaseModel):
    """Character identity information."""

    name: str = Field(..., min_length=1)
    player_name: str | None = None  # None for NPCs
    ancestry: str | None = None
    class_name: str | None = Field(None, alias="class")
    level: int = Field(default=1, ge=1, le=20)
    alignment: str | None = None


class HitPoints(BaseModel):
    """Hit points information."""

    current: int = Field(default=0, ge=0)
    maximum: int = Field(default=0, ge=0)


class CombatStats(BaseModel):
    """Combat statistics."""

    hit_points: HitPoints = Field(default_factory=HitPoints)
    armor_class: int = Field(default=10, ge=0)
    attack_bonus: int = Field(default=0)


class InventoryItem(BaseModel):
    """Inventory item."""

    item: str = Field(..., min_length=1)
    quantity: int = Field(default=1, ge=1)
    equipped: bool = Field(default=False)


def _validate_character_type(v: CharacterType | str) -> CharacterType:
    """Convert string to CharacterType enum."""
    if isinstance(v, str):
        return CharacterType(v)
    return v


class CharacterSheet(BaseArtifact):
    """Character sheet artifact (PC or NPC)."""

    character_type: Annotated[
        CharacterType, BeforeValidator(_validate_character_type)
    ] = Field(..., alias="type")
    identity: CharacterIdentity
    abilities: dict[str, int] = Field(default_factory=dict)  # e.g., {"strength": 16}
    combat: CombatStats = Field(default_factory=CombatStats)
    inventory: list[InventoryItem] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)
    notes: str | None = None

    model_config = BaseArtifact.model_config.copy()
    model_config["populate_by_name"] = True
