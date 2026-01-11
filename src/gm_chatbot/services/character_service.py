"""Character service for character sheet management."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

from ..artifacts.store import ArtifactStore
from ..artifacts.validator import ArtifactValidator
from ..models.character import CharacterSheet

if TYPE_CHECKING:
    from ..services.campaign_service import CampaignService


class CharacterService:
    """Service for managing character sheets."""

    def __init__(
        self,
        store: ArtifactStore | None = None,
        campaign_service: "CampaignService | None" = None,
    ):
        """
        Initialize character service.

        Args:
            store: Optional artifact store (creates default if not provided)
            campaign_service: Optional campaign service (creates default if not provided)
        """
        self.store = store or ArtifactStore()
        self.validator = ArtifactValidator()
        # Lazy import to avoid circular dependency
        if campaign_service is None:
            from ..services.campaign_service import CampaignService

            self.campaign_service = CampaignService(self.store)
        else:
            self.campaign_service = campaign_service

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
        from ..lib.types import CharacterType
        from ..models.character import CharacterIdentity

        character_id = str(uuid4())
        identity_data = kwargs.get("identity", {}).copy()
        # Remove 'name' from identity_data if present, since we're passing it explicitly
        identity_data.pop("name", None)
        identity = CharacterIdentity(name=name, **identity_data)

        # Convert string to enum if needed
        if isinstance(character_type, str):
            character_type_enum = CharacterType(character_type)
        else:
            character_type_enum = character_type

        character = CharacterSheet(
            type=character_type_enum,  # Use alias 'type' instead of 'character_type'
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
                )  # type: ignore[assignment]
                if char.metadata.id == character_id:
                    return char  # type: ignore[return-value]
            except Exception:
                continue

        raise FileNotFoundError(
            f"Character {character_id} not found in campaign {campaign_id}"
        )

    async def get_character_by_player(
        self,
        campaign_id: str,
        player_id: str,
    ) -> CharacterSheet | None:
        """
        Retrieve a player's character in a campaign.

        Looks up the player's membership to find their linked character_id,
        then loads and returns the character.

        Args:
            campaign_id: Campaign identifier
            player_id: Player identifier

        Returns:
            CharacterSheet if player has a character, None otherwise

        Raises:
            FileNotFoundError: If membership not found
        """
        # Get membership to find character_id
        membership = await self.campaign_service.get_membership(campaign_id, player_id)

        if not membership or not membership.character_id:
            return None

        return await self.get_character(campaign_id, membership.character_id)

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
        )  # type: ignore[return-value]

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
        from ..lib.datetime import utc_now

        character.metadata.updated_at = utc_now()

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
        character_type: str | None = None,
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
