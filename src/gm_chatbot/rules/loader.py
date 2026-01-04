"""Rule loader for YAML rule files."""

import yaml
from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from ..models.rules import RuleSet


class RuleLoader:
    """Loads and validates game rules from YAML files."""

    def __init__(self, rules_dir: Path | str = "rules"):
        """
        Initialize rule loader.

        Args:
            rules_dir: Directory containing rule YAML files
        """
        self.rules_dir = Path(rules_dir)
        self._cache: dict[str, RuleSet] = {}

    def load_rules(self, system: str, version: Optional[str] = None) -> RuleSet:
        """
        Load rules for a game system.

        Args:
            system: Game system name (e.g., "shadowdark")
            version: Optional version string (defaults to latest)

        Returns:
            RuleSet instance

        Raises:
            FileNotFoundError: If rule file not found
            ValidationError: If rules are invalid
        """
        cache_key = f"{system}:{version or 'latest'}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        rule_file = self.rules_dir / system / "core.yaml"
        if not rule_file.exists():
            raise FileNotFoundError(f"Rule file not found: {rule_file}")

        try:
            with rule_file.open() as f:
                data = yaml.safe_load(f)
                if data is None:
                    raise ValueError(f"Rule file is empty: {rule_file}")

            ruleset = RuleSet.model_validate(data)
            self._cache[cache_key] = ruleset
            return ruleset
        except ValidationError as e:
            raise ValidationError(
                f"Invalid rules in {rule_file}: {e.errors()}",
                model=RuleSet,
            ) from e
        except yaml.YAMLError as e:
            raise ValueError(f"YAML parsing error in {rule_file}: {e}") from e

    def clear_cache(self) -> None:
        """Clear the rules cache."""
        self._cache.clear()
