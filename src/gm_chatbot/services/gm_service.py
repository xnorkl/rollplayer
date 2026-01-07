"""GM service for coordinating LLM, tools, and artifacts."""

from ..artifacts.validator import ArtifactValidator
from ..models.chat import ChatMessage
from ..tools.llm.interface import LLMProvider
from ..tools.registry import DiceToolRegistry


class GMService:
    """Service for GM chatbot functionality."""

    def __init__(
        self,
        llm_provider: LLMProvider | None = None,
        dice_registry: DiceToolRegistry | None = None,
        validator: ArtifactValidator | None = None,
    ):
        """
        Initialize GM service.

        Args:
            llm_provider: Optional LLM provider
            dice_registry: Optional dice tool registry
            validator: Optional artifact validator
        """
        self.llm_provider = llm_provider
        self.dice_registry = dice_registry or DiceToolRegistry()
        self.validator = validator or ArtifactValidator()

    async def handle_message(
        self,
        message: ChatMessage,
        campaign_id: str,
    ) -> str:
        """
        Handle a chat message and generate response.

        Args:
            message: Chat message
            campaign_id: Campaign identifier

        Returns:
            Response text
        """
        if not self.llm_provider or not await self.llm_provider.is_available():
            return "AI features are not available. Use !help for command reference."

        # Build tool definitions for LLM
        tools = [
            {
                "name": "roll_dice",
                "description": "Roll dice using standard notation (e.g., 2d6+3, 1d20)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Dice expression in standard notation",
                        },
                        "reason": {
                            "type": "string",
                            "description": "Why this roll is being made",
                        },
                    },
                    "required": ["expression"],
                },
            },
        ]

        # Prepare messages
        messages = [
            {
                "role": "system",
                "content": "You are a helpful Game Master assistant for tabletop RPGs. Use the roll_dice tool when you need to roll dice.",
            },
            {
                "role": "user",
                "content": message.message,
            },
        ]

        # Call LLM with tools
        response = await self.llm_provider.chat(messages, tools=tools)

        # TODO: Handle tool calls from LLM response
        # For now, just return the text response

        return response

    async def roll_dice(self, expression: str) -> str:
        """
        Roll dice using the dice tool.

        Args:
            expression: Dice expression

        Returns:
            Formatted dice result
        """
        tool = self.dice_registry.get_dice_tool()
        result = await tool.roll(expression)
        return f"{result.expression} = {result.total} ({result.breakdown})"
