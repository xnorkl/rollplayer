"""Base models for all artifacts."""

import yaml
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class ArtifactMetadata(BaseModel):
    """Metadata for all artifacts."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
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
    def from_yaml(cls, content: str) -> "BaseArtifact":
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
        elif isinstance(obj, str):
            # Try to parse ISO format datetime strings
            # Look for ISO datetime pattern: YYYY-MM-DDTHH:MM:SS...
            if "T" in obj and len(obj) > 10:
                try:
                    # Python 3.11+ fromisoformat can handle 'Z' directly
                    # For older Python, replace 'Z' with '+00:00'
                    if obj.endswith("Z"):
                        # Try with Z first (Python 3.11+)
                        try:
                            return datetime.fromisoformat(obj.replace("Z", "+00:00"))
                        except ValueError:
                            # Fallback: remove Z and parse as naive datetime
                            return datetime.fromisoformat(obj[:-1])
                    else:
                        # No Z suffix, try parsing as-is
                        return datetime.fromisoformat(obj)
                except (ValueError, AttributeError):
                    # Not a datetime string, return as-is
                    pass
        return obj
