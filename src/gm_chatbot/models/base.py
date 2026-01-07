"""Base models for all artifacts."""

from typing import TYPE_CHECKING, Any, TypeVar
from uuid import uuid4

import yaml
from pydantic import BaseModel, ConfigDict, Field

from ..lib.datetime import parse_datetime, utc_now
from ..lib.types import UTC_DATETIME

if TYPE_CHECKING:
    T = TypeVar("T", bound="BaseArtifact")
else:
    T = TypeVar("T")


class ArtifactMetadata(BaseModel):
    """Metadata for all artifacts."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: UTC_DATETIME = Field(default_factory=utc_now)
    updated_at: UTC_DATETIME = Field(default_factory=utc_now)
    version: int = Field(default=1, ge=1)
    schema_version: str = Field(default="1.0")


class BaseArtifact(BaseModel):
    """Base class for all YAML artifacts with strict validation."""

    model_config = ConfigDict(
        strict=True,
        validate_assignment=True,
        extra="forbid",
    )

    metadata: ArtifactMetadata = Field(default_factory=ArtifactMetadata)

    def to_yaml(self) -> str:
        """Serialize to YAML string."""
        return yaml.safe_dump(
            self.model_dump(mode="json"),
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

    @classmethod
    def from_yaml(cls: type[T], content: str) -> T:
        """Deserialize from YAML string."""
        data = yaml.safe_load(content)
        if data is None:
            raise ValueError("YAML content is empty")
        # Convert datetime strings back to datetime objects for Pydantic v2 strict mode
        data = cls._parse_datetime_strings(data)
        return cls.model_validate(data)

    @staticmethod
    def _parse_datetime_strings(obj: Any) -> Any:
        """Recursively parse datetime strings in dict/list structures."""
        if isinstance(obj, dict):
            return {k: BaseArtifact._parse_datetime_strings(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [BaseArtifact._parse_datetime_strings(item) for item in obj]
        elif isinstance(obj, str) and "T" in obj and len(obj) > 10:
            # Try to parse ISO format datetime strings
            # Look for ISO datetime pattern: YYYY-MM-DDTHH:MM:SS...
            try:
                return parse_datetime(obj)
            except (ValueError, TypeError):
                # Not a datetime string, return as-is
                pass
        return obj
