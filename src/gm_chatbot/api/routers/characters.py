"""Character router."""

from fastapi import APIRouter, Body, Depends, status
from fastapi.responses import Response

from ...api.dependencies import get_character_service
from ...api.exceptions import APIError, ErrorCodes
from ...models.character import CharacterSheet
from ...models.chat import APIResponse
from ...services.character_service import CharacterService

router = APIRouter()


@router.get("/campaigns/{campaign_id}/characters", response_model=APIResponse[list[CharacterSheet]])
async def list_characters(
    campaign_id: str,
    character_type: str | None = None,
    service: CharacterService = Depends(get_character_service),
):
    """List characters in a campaign."""
    try:
        characters = await service.list_characters(campaign_id, character_type)
        return APIResponse(success=True, data=characters)
    except Exception as e:
        raise APIError(
            ErrorCodes.INTERNAL_ERROR,
            f"Failed to list characters: {e!s}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e


@router.post(
    "/campaigns/{campaign_id}/characters",
    response_model=APIResponse[CharacterSheet],
    status_code=status.HTTP_201_CREATED,
)
async def create_character(
    campaign_id: str,
    character: CharacterSheet,
    service: CharacterService = Depends(get_character_service),
):
    """Create a new character."""
    try:
        created = await service.create_character(
            campaign_id=campaign_id,
            character_type=character.character_type,
            name=character.identity.name,
            identity=character.identity.model_dump(),
            abilities=character.abilities,
            combat=character.combat.model_dump(),
            inventory=[item.model_dump() for item in character.inventory],
            conditions=character.conditions,
            notes=character.notes,
        )
        return APIResponse(success=True, data=created)
    except Exception as e:
        raise APIError(
            ErrorCodes.VALIDATION_ERROR,
            f"Failed to create character: {e!s}",
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from e


@router.get(
    "/campaigns/{campaign_id}/characters/{character_id}",
    response_model=APIResponse[CharacterSheet],
)
async def get_character(
    campaign_id: str,
    character_id: str,
    service: CharacterService = Depends(get_character_service),
):
    """Get character details."""
    try:
        character = await service.get_character(campaign_id, character_id)
        return APIResponse(success=True, data=character)
    except FileNotFoundError:
        raise APIError(
            ErrorCodes.CHARACTER_NOT_FOUND,
            f"Character {character_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        raise APIError(
            ErrorCodes.INTERNAL_ERROR,
            f"Failed to get character: {e!s}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e


@router.put(
    "/campaigns/{campaign_id}/characters/{character_id}",
    response_model=APIResponse[CharacterSheet],
)
async def update_character(
    campaign_id: str,
    character_id: str,
    character: CharacterSheet,
    service: CharacterService = Depends(get_character_service),
):
    """Update a character."""
    try:
        character.metadata.id = character_id
        updated = await service.update_character(campaign_id, character)
        return APIResponse(success=True, data=updated)
    except FileNotFoundError:
        raise APIError(
            ErrorCodes.CHARACTER_NOT_FOUND,
            f"Character {character_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        raise APIError(
            ErrorCodes.VALIDATION_ERROR,
            f"Failed to update character: {e!s}",
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from e


@router.delete(
    "/campaigns/{campaign_id}/characters/{character_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_character(
    campaign_id: str,
    character_id: str,
    service: CharacterService = Depends(get_character_service),
):
    """Delete a character."""
    try:
        await service.delete_character(campaign_id, character_id)
    except FileNotFoundError:
        raise APIError(
            ErrorCodes.CHARACTER_NOT_FOUND,
            f"Character {character_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        raise APIError(
            ErrorCodes.INTERNAL_ERROR,
            f"Failed to delete character: {e!s}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e


@router.get(
    "/campaigns/{campaign_id}/characters/{character_id}/export",
    response_class=Response,
)
async def export_character(
    campaign_id: str,
    character_id: str,
    service: CharacterService = Depends(get_character_service),
):
    """Export character sheet as YAML."""
    try:
        character = await service.get_character(campaign_id, character_id)
        yaml_content = character.to_yaml()
        filename = f"{character.identity.name.replace(' ', '_')}.yaml"
        return Response(
            content=yaml_content,
            media_type="application/x-yaml",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except FileNotFoundError:
        raise APIError(
            ErrorCodes.CHARACTER_NOT_FOUND,
            f"Character {character_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        raise APIError(
            ErrorCodes.INTERNAL_ERROR,
            f"Failed to export character: {e!s}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e


@router.post(
    "/campaigns/{campaign_id}/characters/import",
    response_model=APIResponse[CharacterSheet],
    status_code=status.HTTP_201_CREATED,
)
async def import_character(
    campaign_id: str,
    yaml_content: str = Body(..., media_type="application/x-yaml"),
    service: CharacterService = Depends(get_character_service),
):
    """Import character sheet from YAML."""
    try:
        character = CharacterSheet.from_yaml(yaml_content)
        imported = await service.import_character(campaign_id, character)
        return APIResponse(success=True, data=imported)
    except Exception as e:
        raise APIError(
            ErrorCodes.VALIDATION_ERROR,
            f"Failed to import character: {e!s}",
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from e
