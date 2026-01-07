"""Rules engine for querying game rules."""

import os
from pathlib import Path

from ..models.rules import AbilityDefinition, RuleSet
from .loader import RuleLoader


class RulesEngine:
    """Engine for loading and querying game rules."""

    def __init__(self, rules_dir: Path | str | None = None):
        """
        Initialize rules engine.

        Args:
            rules_dir: Directory containing rule YAML files (defaults to RULES_DIR env var or /data/rules)
        """
        if rules_dir is None:
            rules_dir = os.getenv("RULES_DIR", "/data/rules")
        self.loader = RuleLoader(rules_dir)
        self._current_ruleset: RuleSet | None = None

    def load_system(self, system: str, version: str | None = None) -> RuleSet:
        """
        Load a game system's rules.

        Args:
            system: Game system name
            version: Optional version string

        Returns:
            Loaded RuleSet
        """
        self._current_ruleset = self.loader.load_rules(system, version)
        return self._current_ruleset

    def get_ability_definition(self, ability_name: str) -> AbilityDefinition | None:
        """
        Get ability definition by name.

        Args:
            ability_name: Name or abbreviation of ability

        Returns:
            AbilityDefinition or None if not found
        """
        if not self._current_ruleset:
            return None

        ability_lower = ability_name.lower()
        for ability in self._current_ruleset.abilities:
            if (
                ability.name.lower() == ability_lower
                or ability.abbreviation.lower() == ability_lower
            ):
                return ability
        return None

    def get_ability_modifier(self, ability_score: int) -> int:
        """
        Get ability modifier for a given score.

        Args:
            ability_score: Ability score value

        Returns:
            Modifier value
        """
        if not self._current_ruleset:
            return 0

        for mapping in self._current_ruleset.ability_modifiers.range_mapping:
            score_range = mapping.range
            if score_range[0] <= ability_score <= score_range[1]:
                return mapping.modifier
        return 0

    def get_difficulty_class(self, difficulty: str) -> int | None:
        """
        Get difficulty class value.

        Args:
            difficulty: Difficulty name (e.g., "easy", "normal")

        Returns:
            DC value or None if not found
        """
        if not self._current_ruleset:
            return None
        return self._current_ruleset.difficulty_classes.get(difficulty.lower())

    def get_dice_expression(self, expression_name: str) -> str | None:
        """
        Get dice expression template.

        Args:
            expression_name: Name of expression (e.g., "ability_check")

        Returns:
            Expression template or None if not found
        """
        if not self._current_ruleset:
            return None
        return self._current_ruleset.dice_expressions.get(expression_name)
