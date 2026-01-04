"""Dice tool interface."""

from typing import Protocol

from ...models.dice import DiceResult


class DiceToolInterface(Protocol):
    """Protocol for dice rolling tools."""

    async def roll(self, expression: str) -> DiceResult:
        """
        Roll dice using standard notation.

        Args:
            expression: Dice expression (e.g., "2d6+3", "1d20")

        Returns:
            DiceResult with breakdown
        """

    async def evaluate(self, expression: str, context: dict[str, int | str]) -> int:
        """
        Evaluate mathematical expression with context variables.

        Args:
            expression: Expression to evaluate (e.g., "2d6 + {modifier}")
            context: Variable context for substitution

        Returns:
            Evaluated integer result
        """
