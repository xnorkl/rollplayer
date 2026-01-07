"""Tests for type definitions."""

from datetime import UTC

import pytest
from pydantic import BaseModel, ValidationError

from gm_chatbot.lib.types import (
    UTC_DATETIME,
    CampaignStatus,
    CharacterType,
    EntityId,
    NonEmptyStr,
    PlayerStatus,
    PositiveInt,
    SessionStatus,
    SlugStr,
)


class TestUTC_DATETIME:
    """Tests for UTC_DATETIME type."""

    class Model(BaseModel):
        timestamp: UTC_DATETIME

    def test_naive_datetime_assumes_utc(self):
        """Naive datetime should be assumed UTC."""
        from datetime import datetime

        naive_dt = datetime(2024, 1, 1, 12, 0, 0)
        model = self.Model(timestamp=naive_dt)

        assert model.timestamp.tzinfo is not None

    def test_utc_datetime_unchanged(self):
        """UTC datetime should remain unchanged."""
        from datetime import datetime

        utc_dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        model = self.Model(timestamp=utc_dt)

        assert model.timestamp == utc_dt
        assert model.timestamp.tzinfo == UTC

    def test_other_timezone_converts_to_utc(self):
        """Datetime in other timezone should convert to UTC."""
        from datetime import datetime, timedelta, timezone

        est = timezone(timedelta(hours=-5))
        est_dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=est)
        model = self.Model(timestamp=est_dt)

        assert model.timestamp.tzinfo == UTC
        assert model.timestamp.hour == 17  # 12 + 5 hours


class TestNonEmptyStr:
    """Tests for NonEmptyStr type."""

    class Model(BaseModel):
        value: NonEmptyStr

    def test_valid_string(self):
        """NonEmptyStr should accept valid non-empty strings."""
        model = self.Model(value="hello")
        assert model.value == "hello"

    def test_strips_whitespace(self):
        """NonEmptyStr should strip whitespace."""
        model = self.Model(value="  hello  ")
        assert model.value == "hello"

    def test_empty_string_raises_error(self):
        """NonEmptyStr should reject empty strings."""
        with pytest.raises(ValidationError):
            self.Model(value="")

    def test_whitespace_only_raises_error(self):
        """NonEmptyStr should reject whitespace-only strings."""
        with pytest.raises(ValidationError):
            self.Model(value="   ")


class TestEntityId:
    """Tests for EntityId type."""

    class Model(BaseModel):
        id: EntityId

    def test_valid_id(self):
        """EntityId should accept valid IDs."""
        model = self.Model(id="player_123")
        assert model.id == "player_123"

    def test_id_with_hyphen(self):
        """EntityId should accept hyphens."""
        model = self.Model(id="player-123")
        assert model.id == "player-123"

    def test_id_with_underscore(self):
        """EntityId should accept underscores."""
        model = self.Model(id="player_123")
        assert model.id == "player_123"

    def test_empty_id_raises_error(self):
        """EntityId should reject empty strings."""
        with pytest.raises(ValidationError):
            self.Model(id="")

    def test_too_long_id_raises_error(self):
        """EntityId should reject IDs longer than 64 characters."""
        long_id = "a" * 65
        with pytest.raises(ValidationError):
            self.Model(id=long_id)

    def test_invalid_characters_raises_error(self):
        """EntityId should reject invalid characters."""
        with pytest.raises(ValidationError):
            self.Model(id="player@123")

    def test_id_with_spaces_raises_error(self):
        """EntityId should reject spaces."""
        with pytest.raises(ValidationError):
            self.Model(id="player 123")


class TestSlugStr:
    """Tests for SlugStr type."""

    class Model(BaseModel):
        slug: SlugStr

    def test_valid_slug(self):
        """SlugStr should accept valid slugs."""
        model = self.Model(slug="hello-world")
        assert model.slug == "hello-world"

    def test_converts_to_lowercase(self):
        """SlugStr should convert to lowercase."""
        model = self.Model(slug="Hello-World")
        assert model.slug == "hello-world"

    def test_replaces_spaces_with_hyphens(self):
        """SlugStr should replace spaces with hyphens."""
        model = self.Model(slug="hello world")
        assert model.slug == "hello-world"

    def test_removes_special_characters(self):
        """SlugStr should remove special characters."""
        model = self.Model(slug="hello@world!")
        assert "hello" in model.slug
        assert "@" not in model.slug
        assert "!" not in model.slug

    def test_empty_slug_raises_error(self):
        """SlugStr should reject empty slugs."""
        with pytest.raises(ValidationError):
            self.Model(slug="")


class TestPositiveInt:
    """Tests for PositiveInt type."""

    class Model(BaseModel):
        value: PositiveInt

    def test_valid_positive_int(self):
        """PositiveInt should accept positive integers."""
        model = self.Model(value=1)
        assert model.value == 1

        model = self.Model(value=100)
        assert model.value == 100

    def test_zero_raises_error(self):
        """PositiveInt should reject zero."""
        with pytest.raises(ValidationError):
            self.Model(value=0)

    def test_negative_raises_error(self):
        """PositiveInt should reject negative integers."""
        with pytest.raises(ValidationError):
            self.Model(value=-1)


class TestCampaignStatus:
    """Tests for CampaignStatus enum."""

    def test_enum_values(self):
        """CampaignStatus should have correct values."""
        assert CampaignStatus.DRAFT == "draft"
        assert CampaignStatus.ACTIVE == "active"
        assert CampaignStatus.COMPLETED == "completed"
        assert CampaignStatus.ARCHIVED == "archived"

    def test_enum_string_representation(self):
        """CampaignStatus should work as string."""
        assert str(CampaignStatus.DRAFT) == "draft"
        assert CampaignStatus.DRAFT == "draft"


class TestPlayerStatus:
    """Tests for PlayerStatus enum."""

    def test_enum_values(self):
        """PlayerStatus should have correct values."""
        assert PlayerStatus.ONLINE == "online"
        assert PlayerStatus.OFFLINE == "offline"
        assert PlayerStatus.AWAY == "away"

    def test_enum_string_representation(self):
        """PlayerStatus should work as string."""
        assert str(PlayerStatus.ONLINE) == "online"
        assert PlayerStatus.ONLINE == "online"


class TestSessionStatus:
    """Tests for SessionStatus enum."""

    def test_enum_values(self):
        """SessionStatus should have correct values."""
        assert SessionStatus.ACTIVE == "active"
        assert SessionStatus.PAUSED == "paused"
        assert SessionStatus.ENDED == "ended"

    def test_enum_string_representation(self):
        """SessionStatus should work as string."""
        assert str(SessionStatus.ACTIVE) == "active"
        assert SessionStatus.ACTIVE == "active"


class TestCharacterType:
    """Tests for CharacterType enum."""

    def test_enum_values(self):
        """CharacterType should have correct values."""
        assert CharacterType.PLAYER_CHARACTER == "player_character"
        assert CharacterType.NON_PLAYER_CHARACTER == "non_player_character"

    def test_enum_string_representation(self):
        """CharacterType should work as string."""
        assert str(CharacterType.PLAYER_CHARACTER) == "player_character"
        assert CharacterType.PLAYER_CHARACTER == "player_character"
