"""Game rules models."""

from pydantic import BaseModel, Field


class RuleMetadata(BaseModel):
    """Metadata for a rule set."""

    system_name: str
    version: str
    author: str | None = None


class AbilityDefinition(BaseModel):
    """Definition of an ability score."""

    name: str = Field(..., min_length=1)
    abbreviation: str = Field(..., pattern=r"^[A-Z]{2,3}$")
    description: str = ""


class AbilityModifierRange(BaseModel):
    """Ability modifier range mapping."""

    range: list[int] = Field(..., min_length=2, max_length=2)  # [min, max]
    modifier: int


class AbilityModifierConfig(BaseModel):
    """Configuration for ability modifiers."""

    range_mapping: list[AbilityModifierRange] = Field(default_factory=list)


class RuleSet(BaseModel):
    """Complete rule set definition."""

    metadata: RuleMetadata
    abilities: list[AbilityDefinition] = Field(default_factory=list)
    ability_modifiers: AbilityModifierConfig = Field(
        default_factory=AbilityModifierConfig
    )
    difficulty_classes: dict[str, int] = Field(default_factory=dict)
    dice_expressions: dict[str, str] = Field(default_factory=dict)
    conditions: list[dict[str, list[str]]] = Field(default_factory=list)
