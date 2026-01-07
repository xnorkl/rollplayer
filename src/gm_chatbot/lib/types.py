"""Reusable Pydantic type definitions for consistent validation.

This module provides common types used across models to ensure
consistent validation rules and reduce duplication.
"""

import re
from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BeforeValidator, Field

# ============================================================================
# Datetime Types
# ============================================================================


def _ensure_utc_validator(v: datetime | None) -> datetime | None:
    """Validator to ensure datetime is in UTC."""
    if v is None:
        return None
    if v.tzinfo is None:
        return v.replace(tzinfo=UTC)
    return v.astimezone(UTC)


UTC_DATETIME = Annotated[
    datetime,
    BeforeValidator(_ensure_utc_validator),
    Field(description="UTC timezone-aware datetime"),
]


# ============================================================================
# String Types
# ============================================================================


def _strip_and_validate_non_empty(v: str) -> str:
    """Strip whitespace and validate non-empty."""
    if not isinstance(v, str):
        raise ValueError("Expected string")
    stripped = v.strip()
    if not stripped:
        raise ValueError("String cannot be empty after stripping whitespace")
    return stripped


NonEmptyStr = Annotated[
    str,
    BeforeValidator(_strip_and_validate_non_empty),
    Field(description="Non-empty string (whitespace stripped)"),
]


def _validate_entity_id(v: str) -> str:
    """Validate entity ID format."""
    if not isinstance(v, str):
        raise ValueError("Expected string")
    if not v:
        raise ValueError("Entity ID cannot be empty")
    if len(v) > 64:
        raise ValueError("Entity ID cannot exceed 64 characters")
    # Alphanumeric, underscore, hyphen
    if not re.match(r"^[a-zA-Z0-9_-]+$", v):
        raise ValueError(
            "Entity ID can only contain alphanumeric characters, underscores, and hyphens"
        )
    return v


EntityId = Annotated[
    str,
    BeforeValidator(_validate_entity_id),
    Field(description="Entity identifier (1-64 chars, alphanumeric + _-)"),
]


def _validate_slug(v: str) -> str:
    """Validate and normalize slug format."""
    if not isinstance(v, str):
        raise ValueError("Expected string")
    # Convert to lowercase and replace spaces/spaces with hyphens
    slug = re.sub(r"[^\w\s-]", "", v.lower())
    slug = re.sub(r"[-\s]+", "-", slug)
    slug = slug.strip("-")
    if not slug:
        raise ValueError("Slug cannot be empty")
    return slug


SlugStr = Annotated[
    str,
    BeforeValidator(_validate_slug),
    Field(description="URL-safe slug (lowercase alphanumeric with hyphens)"),
]


# ============================================================================
# Numeric Types
# ============================================================================

PositiveInt = Annotated[
    int,
    Field(gt=0, description="Positive integer (greater than 0)"),
]


# ============================================================================
# Status Enums
# ============================================================================


class CampaignStatus(StrEnum):
    """Campaign status enumeration."""

    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class PlayerStatus(StrEnum):
    """Player status enumeration."""

    ONLINE = "online"
    OFFLINE = "offline"
    AWAY = "away"


class SessionStatus(StrEnum):
    """Session status enumeration."""

    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"


# ============================================================================
# Character Types and Roles
# ============================================================================


class CharacterType(StrEnum):
    """Character type enumeration."""

    PLAYER_CHARACTER = "player_character"
    NON_PLAYER_CHARACTER = "non_player_character"


class MembershipRole(StrEnum):
    """Campaign membership role enumeration."""

    PLAYER = "player"
    GM = "gm"
    SPECTATOR = "spectator"
