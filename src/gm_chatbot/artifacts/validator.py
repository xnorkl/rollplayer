"""Artifact validation system."""

from typing import Any

from pydantic import ValidationError

from ..models.action import GameAction
from ..models.base import BaseArtifact
from ..models.campaign import Campaign
from ..models.character import CharacterSheet


class ArtifactValidator:
    """Validates artifacts before use and after generation."""

    def validate_character(self, data: dict[str, Any]) -> CharacterSheet:
        """
        Validate character sheet data.

        Raises:
            ValidationError: If character data is invalid
        """
        try:
            return CharacterSheet.model_validate(data)
        except ValidationError as e:
            raise ValidationError(f"Invalid character sheet: {e.errors()}") from e

    def validate_campaign(self, data: dict[str, Any]) -> Campaign:
        """
        Validate campaign data.

        Raises:
            ValidationError: If campaign data is invalid
        """
        try:
            return Campaign.model_validate(data)
        except ValidationError as e:
            raise ValidationError(f"Invalid campaign: {e.errors()}") from e

    def validate_action(self, data: dict[str, Any]) -> GameAction:
        """
        Validate game action data.

        Raises:
            ValidationError: If action data is invalid
        """
        try:
            return GameAction.model_validate(data)
        except ValidationError as e:
            raise ValidationError(f"Invalid game action: {e.errors()}") from e

    def validate_artifact(self, artifact: BaseArtifact) -> bool:
        """
        Validate an artifact instance.

        Returns:
            True if valid

        Raises:
            ValidationError: If artifact is invalid
        """
        try:
            artifact.model_validate(artifact.model_dump())
            return True
        except ValidationError as e:
            raise ValidationError(f"Invalid artifact: {e.errors()}") from e
