"""Shadowdark RPG rule definitions and constants."""
from typing import Dict, List

# Ability score to modifier mapping (standard D&D/Shadowdark)
ABILITY_MODIFIERS: Dict[int, int] = {
    1: -5, 2: -4, 3: -4, 4: -3, 5: -3, 6: -2, 7: -2, 8: -1, 9: -1,
    10: 0, 11: 0, 12: 1, 13: 1, 14: 2, 15: 2, 16: 3, 17: 3, 18: 4,
    19: 4, 20: 5
}

# Ability names
ABILITY_NAMES: List[str] = [
    "strength", "str", "dexterity", "dex", "constitution", "con",
    "intelligence", "int", "wisdom", "wis", "charisma", "cha"
]

# Difficulty Classes
DC_EASY: int = 5
DC_NORMAL: int = 10
DC_HARD: int = 15
DC_VERY_HARD: int = 20

# Conditions
CONDITIONS: List[str] = [
    "blinded", "charmed", "deafened", "frightened", "grappled",
    "incapacitated", "invisible", "paralyzed", "petrified", "poisoned",
    "prone", "restrained", "stunned", "unconscious"
]

# Spell levels
MAX_SPELL_LEVEL: int = 9

# Default spell slots by level (example - varies by class)
DEFAULT_SPELL_SLOTS: Dict[int, int] = {
    1: 2, 2: 3, 3: 3, 4: 4, 5: 4, 6: 4, 7: 4, 8: 4, 9: 4
}


def get_ability_modifier(ability_score: int) -> int:
    """Get ability modifier from ability score."""
    return ABILITY_MODIFIERS.get(ability_score, 0)


def normalize_ability_name(name: str) -> str:
    """Normalize ability name to full form."""
    name_lower = name.lower()
    if name_lower in ["str", "strength"]:
        return "strength"
    elif name_lower in ["dex", "dexterity"]:
        return "dexterity"
    elif name_lower in ["con", "constitution"]:
        return "constitution"
    elif name_lower in ["int", "intelligence"]:
        return "intelligence"
    elif name_lower in ["wis", "wisdom"]:
        return "wisdom"
    elif name_lower in ["cha", "charisma"]:
        return "charisma"
    return name_lower

