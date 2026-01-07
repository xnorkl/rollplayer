"""CLI-based dice tool implementation."""

import asyncio
import re

from ...models.dice import DiceResult


class CLIDiceTool:
    """Dice tool using CLI subprocess (e.g., dice-cli)."""

    DICE_PATTERN = re.compile(r"(\d*)d(\d+)([+-]\d+)?")

    def __init__(self, command: str = "dice"):
        """
        Initialize CLI dice tool.

        Args:
            command: CLI command to execute (default: "dice")
        """
        self.command = command

    async def roll(self, expression: str) -> DiceResult:
        """
        Roll dice using CLI tool or fallback to local calculation.

        Args:
            expression: Dice expression (e.g., "2d6+3")

        Returns:
            DiceResult with breakdown
        """
        expression = expression.strip().lower().replace(" ", "")

        # Try CLI tool first
        try:
            result = await self._roll_with_cli(expression)
            if result:
                return result
        except Exception:
            pass

        # Fallback to local calculation
        return await self._roll_local(expression)

    async def _roll_with_cli(self, expression: str) -> DiceResult | None:
        """Roll using CLI tool."""
        try:
            process = await asyncio.create_subprocess_exec(
                self.command,
                expression,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _stderr = await process.communicate()
            if process.returncode == 0:
                # Parse CLI output (format may vary)
                total = int(stdout.decode().strip())
                return DiceResult(
                    expression=expression,
                    total=total,
                    rolls=[],
                    modifier=0,
                    breakdown=f"{expression} = {total}",
                )
        except Exception:
            pass
        return None

    async def _roll_local(self, expression: str) -> DiceResult:
        """Roll using local calculation (fallback)."""
        import random

        match = self.DICE_PATTERN.match(expression)
        if not match:
            raise ValueError(f"Invalid dice expression: {expression}")

        num_dice = int(match.group(1)) if match.group(1) else 1
        die_size = int(match.group(2))
        modifier = int(match.group(3)) if match.group(3) else 0

        if num_dice < 1 or num_dice > 100:
            raise ValueError("Number of dice must be between 1 and 100")
        if die_size < 1 or die_size > 1000:
            raise ValueError("Die size must be between 1 and 1000")

        # Roll dice
        rolls = [random.randint(1, die_size) for _ in range(num_dice)]
        total = sum(rolls) + modifier

        # Build breakdown
        rolls_str = ", ".join(str(r) for r in rolls)
        breakdown = f"{num_dice}d{die_size}"
        if modifier != 0:
            breakdown += f"{modifier:+d}"
        breakdown += f" = [{rolls_str}]"
        if modifier != 0:
            breakdown += f" {modifier:+d} = {total}"
        else:
            breakdown += f" = {total}"

        return DiceResult(
            expression=expression,
            total=total,
            rolls=rolls,
            modifier=modifier,
            breakdown=breakdown,
        )

    async def evaluate(self, expression: str, context: dict[str, int | str]) -> int:
        """
        Evaluate mathematical expression with context.

        Args:
            expression: Expression to evaluate
            context: Variable context

        Returns:
            Evaluated integer result
        """
        # Simple substitution and evaluation
        # For production, use a proper expression evaluator
        try:
            # Replace context variables
            for key, value in context.items():
                expression = expression.replace(f"{{{key}}}", str(value))

            # Evaluate (simple approach - use ast.literal_eval for safety)
            return int(eval(expression))
        except Exception as e:
            raise ValueError(f"Failed to evaluate expression '{expression}': {e}") from e
