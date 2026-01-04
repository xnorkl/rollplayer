"""OpenAI LLM provider."""

import os
from typing import Optional

from openai import AsyncOpenAI

from .interface import LLMProvider


class OpenAIProvider:
    """OpenAI LLM provider implementation."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
    ):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model name to use
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.client: Optional[AsyncOpenAI] = None
        if self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key)

    async def chat(
        self,
        messages: list[dict[str, str]],
        tools: list[dict] | None = None,
        temperature: float = 0.3,
    ) -> str:
        """
        Send chat messages to OpenAI.

        Args:
            messages: List of message dicts
            tools: Optional tool definitions
            temperature: Sampling temperature

        Returns:
            Response text
        """
        if not self.client:
            raise ValueError("OpenAI client not initialized (missing API key)")

        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools

        response = await self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""

    async def is_available(self) -> bool:
        """Check if OpenAI is available."""
        return self.client is not None

