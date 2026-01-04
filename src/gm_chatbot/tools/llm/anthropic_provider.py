"""Anthropic LLM provider."""

import os
from typing import Optional

from anthropic import AsyncAnthropic

from .interface import LLMProvider


class AnthropicProvider:
    """Anthropic LLM provider implementation."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-haiku-20240307",
    ):
        """
        Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Model name to use
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        self.client: Optional[AsyncAnthropic] = None
        if self.api_key:
            self.client = AsyncAnthropic(api_key=self.api_key)

    async def chat(
        self,
        messages: list[dict[str, str]],
        tools: list[dict] | None = None,
        temperature: float = 0.3,
    ) -> str:
        """
        Send chat messages to Anthropic.

        Args:
            messages: List of message dicts
            tools: Optional tool definitions
            temperature: Sampling temperature

        Returns:
            Response text
        """
        if not self.client:
            raise ValueError("Anthropic client not initialized (missing API key)")

        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools

        response = await self.client.messages.create(**kwargs)
        return response.content[0].text

    async def is_available(self) -> bool:
        """Check if Anthropic is available."""
        return self.client is not None

