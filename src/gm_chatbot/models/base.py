"""Base models for all artifacts."""

import yaml
from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class ArtifactMetadata(BaseModel):
    """Metadata for all artifacts."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
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
        return cls.model_validate(data)
