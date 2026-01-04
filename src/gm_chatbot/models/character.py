"""Character sheet model."""

from typing import Literal, Optional

from pydantic import BaseModel, Field

from .base import BaseArtifact


class CharacterIdentity(BaseModel):
    """Character identity information."""

    name: str = Field(..., min_length=1)
    player_name: Optional[str] = None  # None for NPCs
    ancestry: Optional[str] = None
    class_name: Optional[str] = Field(None, alias="class")
    level: int = Field(default=1, ge=1, le=20)
    alignment: Optional[str] = None


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


class CharacterSheet(BaseArtifact):
    """Character sheet artifact (PC or NPC)."""

    character_type: Literal["player_character", "non_player_character"] = Field(
        ..., alias="type"
    )
    identity: CharacterIdentity
    abilities: dict[str, int] = Field(default_factory=dict)  # e.g., {"strength": 16}
    combat: CombatStats = Field(default_factory=CombatStats)
    inventory: list[InventoryItem] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)
    notes: Optional[str] = None

    model_config = BaseArtifact.model_config.copy()
    model_config["populate_by_name"] = True
