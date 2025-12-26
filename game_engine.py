"""Core game engine for Shadowdark RPG mechanics."""

import random
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum

from shadowdark_rules import (
    get_ability_modifier,
    normalize_ability_name,
    DC_EASY,
    DC_NORMAL,
    DC_HARD,
    DC_VERY_HARD,
    CONDITIONS,
)


class DiceRoller:
    """Parses and executes dice expressions."""

    # Pattern to match dice expressions like "2d6+3", "1d20", "d4-1"
    DICE_PATTERN = re.compile(r"(\d*)d(\d+)([+-]\d+)?")

    @staticmethod
    def roll(expression: str) -> Tuple[int, str]:
        """
        Roll dice based on expression.

        Args:
            expression: Dice expression (e.g., "2d6+3", "1d20", "d4")

        Returns:
            Tuple of (result, breakdown_string)
        """
        expression = expression.strip().lower().replace(" ", "")

        # Match dice pattern
        match = DiceRoller.DICE_PATTERN.match(expression)
        if not match:
            raise ValueError(f"Invalid dice expression: {expression}")

        num_dice = int(match.group(1)) if match.group(1) else 1
        die_size = int(match.group(2))
        modifier = int(match.group(3)) if match.group(3) else 0

        if num_dice < 1 or num_dice > 100:
            raise ValueError(f"Number of dice must be between 1 and 100")
        if die_size < 1 or die_size > 1000:
            raise ValueError(f"Die size must be between 1 and 1000")

        # Roll dice
        rolls = [random.randint(1, die_size) for _ in range(num_dice)]
        total = sum(rolls) + modifier

        # Build breakdown string
        rolls_str = ", ".join(str(r) for r in rolls)
        breakdown = f"{num_dice}d{die_size}"
        if modifier != 0:
            breakdown += f"{modifier:+d}"
        breakdown += f" = [{rolls_str}]"
        if modifier != 0:
            breakdown += f" {modifier:+d} = {total}"
        else:
            breakdown += f" = {total}"

        return total, breakdown

    @staticmethod
    def roll_d20() -> int:
        """Roll a d20."""
        return random.randint(1, 20)


@dataclass
class CombatParticipant:
    """Represents a participant in combat."""

    name: str
    initiative: int = 0
    hp: int = 0
    max_hp: int = 0
    ac: int = 10
    conditions: List[str] = field(default_factory=list)
    dex_modifier: int = 0


class CombatTracker:
    """Manages combat state including initiative, HP, AC, and conditions."""

    def __init__(self):
        self._in_combat: bool = False
        self._participants: Dict[str, CombatParticipant] = {}
        self._turn_order: List[str] = []
        self._current_turn: int = 0

    def start_combat(self) -> str:
        """Start a new combat encounter."""
        self._in_combat = True
        self._participants.clear()
        self._turn_order.clear()
        self._current_turn = 0
        return "Combat started! Use !initiative to add participants."

    def end_combat(self) -> str:
        """End the current combat encounter."""
        self._in_combat = False
        count = len(self._participants)
        self._participants.clear()
        self._turn_order.clear()
        self._current_turn = 0
        return f"Combat ended. {count} participant(s) removed."

    def add_initiative(self, name: str, roll: int, dex_modifier: int = 0) -> str:
        """Add or update a participant's initiative."""
        total = roll + dex_modifier
        if name not in self._participants:
            self._participants[name] = CombatParticipant(
                name=name, dex_modifier=dex_modifier
            )

        participant = self._participants[name]
        participant.initiative = total
        participant.dex_modifier = dex_modifier

        # Rebuild turn order
        self._turn_order = sorted(
            self._participants.keys(),
            key=lambda n: (self._participants[n].initiative, n),
            reverse=True,
        )
        self._current_turn = 0

        return f"{name}: Initiative {total} (d20: {roll}, Dex mod: {dex_modifier:+d})"

    def set_hp(self, name: str, hp: int, max_hp: Optional[int] = None) -> str:
        """Set HP for a participant."""
        if name not in self._participants:
            self._participants[name] = CombatParticipant(name=name)

        participant = self._participants[name]
        participant.hp = hp
        if max_hp is not None:
            participant.max_hp = max_hp
        elif participant.max_hp == 0:
            participant.max_hp = hp

        return f"{name}: HP {hp}/{participant.max_hp}"

    def apply_damage(self, name: str, damage: int) -> str:
        """Apply damage to a participant."""
        if name not in self._participants:
            return f"Error: {name} not found in combat."

        participant = self._participants[name]
        participant.hp = max(0, participant.hp - damage)

        status = (
            "DEAD" if participant.hp == 0 else f"{participant.hp}/{participant.max_hp}"
        )
        return f"{name} takes {damage} damage. HP: {status}"

    def set_ac(self, name: str, ac: int) -> str:
        """Set AC for a participant."""
        if name not in self._participants:
            self._participants[name] = CombatParticipant(name=name)

        participant = self._participants[name]
        participant.ac = ac
        return f"{name}: AC {ac}"

    def get_ac(self, name: str) -> Optional[int]:
        """Get AC for a participant."""
        if name in self._participants:
            return self._participants[name].ac
        return None

    def add_condition(self, name: str, condition: str) -> str:
        """Add a condition to a participant."""
        if name not in self._participants:
            self._participants[name] = CombatParticipant(name=name)

        participant = self._participants[name]
        condition_lower = condition.lower()
        if condition_lower not in participant.conditions:
            participant.conditions.append(condition_lower)
            return f"{name} is now {condition_lower}."
        return f"{name} is already {condition_lower}."

    def remove_condition(self, name: str, condition: str) -> str:
        """Remove a condition from a participant."""
        if name not in self._participants:
            return f"Error: {name} not found in combat."

        participant = self._participants[name]
        condition_lower = condition.lower()
        if condition_lower in participant.conditions:
            participant.conditions.remove(condition_lower)
            return f"{name} is no longer {condition_lower}."
        return f"{name} is not {condition_lower}."

    def get_status(self) -> str:
        """Get current combat status."""
        if not self._in_combat:
            return "No active combat."

        if not self._participants:
            return "Combat started but no participants yet."

        lines = ["=== Combat Status ==="]
        for name in self._turn_order:
            p = self._participants[name]
            hp_str = f"{p.hp}/{p.max_hp}" if p.max_hp > 0 else str(p.hp)
            cond_str = f" [{', '.join(p.conditions)}]" if p.conditions else ""
            lines.append(
                f"{name}: Initiative {p.initiative}, HP {hp_str}, AC {p.ac}{cond_str}"
            )

        if self._turn_order:
            current = self._turn_order[self._current_turn % len(self._turn_order)]
            lines.append(f"\nCurrent turn: {current}")

        return "\n".join(lines)

    def next_turn(self) -> str:
        """Advance to next turn."""
        if not self._in_combat or not self._turn_order:
            return "No active combat."

        self._current_turn = (self._current_turn + 1) % len(self._turn_order)
        current = self._turn_order[self._current_turn]
        return f"Turn: {current}"

    def is_in_combat(self) -> bool:
        """Check if combat is active."""
        return self._in_combat


@dataclass
class Spell:
    """Represents a spell."""

    name: str
    level: int
    casting_time: str = "1 action"
    duration: str = "Instantaneous"
    requires_concentration: bool = False


class SpellManager:
    """Manages spell casting, slots, and effects."""

    def __init__(self):
        self._spells: Dict[str, Spell] = {}
        self._active_spells: Dict[str, List[Tuple[str, Spell]]] = (
            {}
        )  # character -> [(target, spell)]
        self._spell_slots: Dict[str, Dict[int, int]] = (
            {}
        )  # character -> {level: remaining_slots}

    def register_spell(self, spell: Spell) -> None:
        """Register a spell definition."""
        self._spells[spell.name.lower()] = spell

    def cast_spell(
        self, caster: str, spell_name: str, target: Optional[str] = None
    ) -> str:
        """Cast a spell."""
        spell_name_lower = spell_name.lower()
        if spell_name_lower not in self._spells:
            return f"Error: Spell '{spell_name}' not found."

        spell = self._spells[spell_name_lower]

        # Check spell slots
        if caster not in self._spell_slots:
            self._spell_slots[caster] = {}

        slots = self._spell_slots[caster]
        if spell.level not in slots or slots[spell.level] <= 0:
            return f"Error: {caster} has no level {spell.level} spell slots remaining."

        # Use spell slot
        slots[spell.level] -= 1

        # Track active spell if it has duration
        if spell.duration != "Instantaneous":
            if caster not in self._active_spells:
                self._active_spells[caster] = []
            self._active_spells[caster].append((target or "self", spell))

        target_str = f" on {target}" if target else ""
        return f"{caster} casts {spell.name}{target_str}. (Used level {spell.level} slot, {slots[spell.level]} remaining)"

    def set_spell_slots(self, character: str, level: int, slots: int) -> str:
        """Set spell slots for a character."""
        if character not in self._spell_slots:
            self._spell_slots[character] = {}
        self._spell_slots[character][level] = slots
        return f"{character}: {slots} level {level} spell slot(s)."

    def get_spell_slots(self, character: str) -> str:
        """Get remaining spell slots for a character."""
        if character not in self._spell_slots or not self._spell_slots[character]:
            return f"{character} has no spell slots tracked."

        slots = self._spell_slots[character]
        lines = [f"{character}'s Spell Slots:"]
        for level in sorted(slots.keys()):
            lines.append(f"  Level {level}: {slots[level]}")
        return "\n".join(lines)


    @staticmethod
    def parse_roll20_roll_data(roll_data: dict) -> Tuple[list, int]:
        """
        Parse Roll20 roll data to extract dice values and modifier.
        
        Args:
            roll_data: Roll20 rollresult data structure
            
        Returns:
            Tuple of (dice_values_list, modifier)
        """
        dice = roll_data.get("dice", [])
        modifier = roll_data.get("modifier", 0)
        return dice, modifier
    
    @staticmethod
    def calculate_total_from_roll20(dice: list, modifier: int) -> int:
        """
        Calculate total from Roll20 dice values and modifier.
        
        Args:
            dice: List of dice values
            modifier: Modifier to add
            
        Returns:
            Total value
        """
        return sum(dice) + modifier


class ShadowdarkRules:
    """Shadowdark RPG rule calculations and checks."""

    @staticmethod
    def ability_check(roll: int, ability_modifier: int, dc: int) -> Tuple[bool, str]:
        """
        Perform an ability check.

        Args:
            roll: d20 roll result
            ability_modifier: Ability modifier
            dc: Difficulty class

        Returns:
            Tuple of (success, description)
        """
        total = roll + ability_modifier
        success = total >= dc
        result = "Success" if success else "Failure"
        return (
            success,
            f"{result}: {total} (d20: {roll}, mod: {ability_modifier:+d}) vs DC {dc}",
        )

    @staticmethod
    def attack_roll(
        roll: int, attack_modifier: int, target_ac: int
    ) -> Tuple[bool, str]:
        """
        Perform an attack roll.

        Args:
            roll: d20 roll result
            attack_modifier: Attack modifier
            target_ac: Target's Armor Class

        Returns:
            Tuple of (hit, description)
        """
        total = roll + attack_modifier
        hit = total >= target_ac
        result = "HIT" if hit else "MISS"
        return (
            hit,
            f"{result}: {total} (d20: {roll}, mod: {attack_modifier:+d}) vs AC {target_ac}",
        )

    @staticmethod
    def saving_throw(roll: int, save_modifier: int, dc: int) -> Tuple[bool, str]:
        """
        Perform a saving throw.

        Args:
            roll: d20 roll result
            save_modifier: Save modifier
            dc: Difficulty class

        Returns:
            Tuple of (success, description)
        """
        total = roll + save_modifier
        success = total >= dc
        result = "Success" if success else "Failure"
        return (
            success,
            f"{result}: {total} (d20: {roll}, mod: {save_modifier:+d}) vs DC {dc}",
        )


# Global game state
_combat_tracker = CombatTracker()
_spell_manager = SpellManager()
