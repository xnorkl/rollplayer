"""LLM provider interface."""

from typing import Protocol


class LLMProvider(Protocol):
    """Protocol for LLM providers."""

    async def chat(
        self,
        messages: list[dict[str, str]],
        tools: list[dict] | None = None,
        temperature: float = 0.3,
    ) -> str:
        """
        Send chat messages to LLM.

        Args:
            messages: List of message dicts with "role" and "content"
            tools: Optional list of tool definitions for function calling
            temperature: Sampling temperature

        Returns:
            LLM response text
        """

    async def is_available(self) -> bool:
        """
        Check if provider is available.

        Returns:
            True if available
        """
