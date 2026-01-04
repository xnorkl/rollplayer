"""Platform adapter interface."""

from typing import Awaitable, Callable, Protocol

from ..models.chat import ChatMessage


class PlatformConfig:
    """Configuration for platform adapters."""

    def __init__(self, **kwargs):
        """Initialize platform config."""
        self.__dict__.update(kwargs)


class PlatformAdapter(Protocol):
    """Protocol for VTT/chat platform integration."""

    async def connect(self, config: PlatformConfig) -> None:
        """Establish connection to platform."""

    async def disconnect(self) -> None:
        """Gracefully disconnect from platform."""

    async def send_message(self, message: ChatMessage) -> None:
        """Send message to platform chat."""

    async def on_message(
        self,
        callback: Callable[[ChatMessage], Awaitable[None]],
    ) -> None:
        """Register message handler."""

    @property
    def platform_name(self) -> str:
        """Return platform identifier."""
