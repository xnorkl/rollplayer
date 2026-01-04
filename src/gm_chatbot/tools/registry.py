"""Tool registry for managing external tools."""

from typing import Optional

from .dice.interface import DiceToolInterface
from .dice.cli_tool import CLIDiceTool


class ToolRegistry:
    """Registry for managing external tools."""

    def __init__(self):
        """Initialize tool registry."""
        self._dice_tools: dict[str, DiceToolInterface] = {}
        self._default_dice_tool: Optional[str] = None

    def register_dice_tool(self, name: str, tool: DiceToolInterface, default: bool = False) -> None:
        """
        Register a dice tool.

        Args:
            name: Tool name
            tool: Tool implementation
            default: Whether this is the default tool
        """
        self._dice_tools[name] = tool
        if default or self._default_dice_tool is None:
            self._default_dice_tool = name

    def get_dice_tool(self, name: Optional[str] = None) -> DiceToolInterface:
        """
        Get a dice tool by name.

        Args:
            name: Tool name (uses default if not provided)

        Returns:
            Dice tool instance

        Raises:
            ValueError: If tool not found
        """
        tool_name = name or self._default_dice_tool
        if tool_name is None:
            raise ValueError("No dice tool registered")
        if tool_name not in self._dice_tools:
            raise ValueError(f"Dice tool '{tool_name}' not found")
        return self._dice_tools[tool_name]


class DiceToolRegistry(ToolRegistry):
    """Specialized registry for dice tools."""

    def __init__(self):
        """Initialize dice tool registry with default CLI tool."""
        super().__init__()
        # Register default CLI tool
        self.register_dice_tool("cli", CLIDiceTool(), default=True)
