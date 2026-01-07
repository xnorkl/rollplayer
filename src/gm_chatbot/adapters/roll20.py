"""Roll20 WebSocket adapter."""

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import WebSocket

from ..adapters.interface import PlatformConfig
from ..models.chat import ChatMessage


class Roll20Adapter:
    """Roll20 WebSocket adapter."""

    def __init__(self):
        """Initialize Roll20 adapter."""
        self.websocket: WebSocket | None = None
        self.message_handler: Callable[[ChatMessage], Awaitable[None]] | None = None

    @property
    def platform_name(self) -> str:
        """Return platform identifier."""
        return "roll20"

    async def connect(self, config: PlatformConfig) -> None:
        """Establish WebSocket connection."""
        self.websocket = config.websocket  # type: ignore[assignment]
        if self.websocket:
            await self.websocket.accept()

    async def disconnect(self) -> None:
        """Gracefully disconnect from WebSocket."""
        if self.websocket:
            await self.websocket.close()

    async def send_message(self, message: ChatMessage) -> None:
        """Send message via WebSocket."""
        if self.websocket:
            await self.websocket.send_json(
                {
                    "type": "text",
                    "content": message.message,
                }
            )

    async def on_message(
        self,
        callback: Callable[[ChatMessage], Awaitable[None]],
    ) -> None:
        """Register message handler."""
        self.message_handler = callback
        # Message handling is done in the WebSocket endpoint
