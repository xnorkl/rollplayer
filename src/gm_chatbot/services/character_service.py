"""Character service for character sheet management."""

from pathlib import Path
from typing import Optional
from uuid import uuid4

from ..artifacts.store import ArtifactStore
from ..artifacts.validator import ArtifactValidator
from ..models.character import CharacterSheet


class CharacterService:
    """Service for managing character sheets."""

    def __init__(self, store: Optional[ArtifactStore] = None):
        """
        Initialize character service.

        Args:
            store: Optional artifact store (creates default if not provided)
        """
        self.store = store or ArtifactStore()
        self.validator = ArtifactValidator()

    async def create_character(
        self,
        campaign_id: str,
        character_type: str,
        name: str,
        **kwargs,
    ) -> CharacterSheet:
        """
        Create a new character.

        Args:
            campaign_id: Campaign identifier
            character_type: "player_character" or "non_player_character"
            name: Character name
            **kwargs: Additional character fields

        Returns:
            Created character sheet
        """
        from ..models.character import CharacterIdentity

        character_id = str(uuid4())
        identity_data = kwargs.get("identity", {}).copy()
        # Remove 'name' from identity_data if present, since we're passing it explicitly
        identity_data.pop("name", None)
        identity = CharacterIdentity(name=name, **identity_data)

        character = CharacterSheet(
            character_type=character_type,
            identity=identity,
            **{k: v for k, v in kwargs.items() if k != "identity"},
        )
        character.metadata.id = character_id

        # Validate before saving
        self.validator.validate_character(character.model_dump())

        # Generate filename
        prefix = "pc" if character_type == "player_character" else "npc"
        filename = f"{prefix}_{name.lower().replace(' ', '_')}.yaml"

        # Save character in characters subdirectory
        self.store.save_artifact(
            character, campaign_id, "character", f"characters/{filename}"
        )

        return character

    async def get_character(
        self,
        campaign_id: str,
        character_id: str,
    ) -> CharacterSheet:
        """
        Get a character by ID.

        Args:
            campaign_id: Campaign identifier
            character_id: Character identifier

        Returns:
            Character sheet instance

        Raises:
            FileNotFoundError: If character not found
        """
        # Find character file by ID
        characters_dir = self.store.get_campaign_dir(campaign_id) / "characters"
        if not characters_dir.exists():
            raise FileNotFoundError(
                f"Characters directory not found for campaign {campaign_id}"
            )

        for char_file in characters_dir.glob("*.yaml"):
            try:
                char = self.store.load_artifact(
                    CharacterSheet, campaign_id, f"characters/{char_file.name}"
                )
                if char.metadata.id == character_id:
                    return char
            except Exception:
                continue

        raise FileNotFoundError(
            f"Character {character_id} not found in campaign {campaign_id}"
        )

    async def get_character_by_filename(
        self,
        campaign_id: str,
        filename: str,
    ) -> CharacterSheet:
        """
        Get a character by filename.

        Args:
            campaign_id: Campaign identifier
            filename: Character filename

        Returns:
            Character sheet instance
        """
        return self.store.load_artifact(
            CharacterSheet,
            campaign_id,
            f"characters/{filename}",
        )

    async def update_character(
        self, campaign_id: str, character: CharacterSheet
    ) -> CharacterSheet:
        """
        Update a character.

        Args:
            campaign_id: Campaign identifier
            character: Updated character instance

        Returns:
            Updated character
        """
        # Validate before saving
        self.validator.validate_character(character.model_dump())

        # Update timestamp
        from datetime import datetime

        character.metadata.updated_at = datetime.utcnow()

        # Find existing file to preserve filename
        characters_dir = self.store.get_campaign_dir(campaign_id) / "characters"
        for char_file in characters_dir.glob("*.yaml"):
            try:
                existing = self.store.load_artifact(
                    CharacterSheet,
                    campaign_id,
                    f"characters/{char_file.name}",
                )
                if existing.metadata.id == character.metadata.id:
                    self.store.save_artifact(
                        character,
                        campaign_id,
                        "character",
                        f"characters/{char_file.name}",
                    )
                    return character
            except Exception:
                continue

        raise FileNotFoundError(f"Character {character.metadata.id} not found")

    async def list_characters(
        self,
        campaign_id: str,
        character_type: Optional[str] = None,
    ) -> list[CharacterSheet]:
        """
        List characters in a campaign.

        Args:
            campaign_id: Campaign identifier
            character_type: Optional filter by type ("player_character" or "non_player_character")

        Returns:
            List of character sheets
        """
        characters = []
        characters_dir = self.store.get_campaign_dir(campaign_id) / "characters"
        if not characters_dir.exists():
            return characters

        for char_file in characters_dir.glob("*.yaml"):
            try:
                char = self.store.load_artifact(
                    CharacterSheet,
                    campaign_id,
                    f"characters/{char_file.name}",
                )
                if character_type is None or char.character_type == character_type:
                    characters.append(char)
            except Exception:
                continue

        return characters

    async def delete_character(
        self,
        campaign_id: str,
        character_id: str,
    ) -> None:
        """
        Delete a character.

        Args:
            campaign_id: Campaign identifier
            character_id: Character identifier
        """
        # Find and delete character file
        characters_dir = self.store.get_campaign_dir(campaign_id) / "characters"
        for char_file in characters_dir.glob("*.yaml"):
            try:
                char = self.store.load_artifact(
                    CharacterSheet,
                    campaign_id,
                    f"characters/{char_file.name}",
                )
                if char.metadata.id == character_id:
                    char_file.unlink()
                    return
            except Exception:
                continue

        raise FileNotFoundError(f"Character {character_id} not found")

    async def import_character(
        self,
        campaign_id: str,
        character: CharacterSheet,
    ) -> CharacterSheet:
        """
        Import a character from YAML.

        Args:
            campaign_id: Campaign identifier
            character: Character sheet to import

        Returns:
            Imported character sheet
        """
        # Validate before saving
        self.validator.validate_character(character.model_dump())

        # Generate new ID if not provided
        if not character.metadata.id:
            from uuid import uuid4

            character.metadata.id = str(uuid4())

        # Generate filename
        prefix = "pc" if character.character_type == "player_character" else "npc"
        filename = f"{prefix}_{character.identity.name.lower().replace(' ', '_')}.yaml"

        # Save character
        self.store.save_artifact(
            character, campaign_id, "character", f"characters/{filename}"
        )

        return character
