"""Chat and API response models."""

from datetime import datetime
from typing import Generic, TypeVar
from uuid import uuid4

from pydantic import BaseModel, Field

from ..lib.datetime import utc_now

T = TypeVar("T")


class ChatMessage(BaseModel):
    """Chat message model."""

    message: str
    sender_id: str | None = None
    sender_type: str | None = None  # "player", "gm", etc.
    campaign_id: str


class ErrorDetail(BaseModel):
    """Error detail for API responses."""

    code: str
    message: str
    details: dict | None = None


class ResponseMeta(BaseModel):
    """Metadata for API responses."""

    request_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=utc_now)
    processing_time_ms: float = 0.0


class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""

    success: bool
    data: T | None = None
    error: ErrorDetail | None = None
    meta: ResponseMeta | None = None
