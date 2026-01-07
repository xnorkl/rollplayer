"""Session router."""

from fastapi import APIRouter, Body, Depends, status

from ...api.dependencies import get_session_service
from ...api.exceptions import APIError, ErrorCodes
from ...models.chat import APIResponse
from ...models.session import Session, SessionParticipant
from ...services.session_service import SessionService

router = APIRouter()


@router.get("/campaigns/{campaign_id}/sessions", response_model=APIResponse[list[Session]])
async def list_sessions(
    campaign_id: str,
    session_status: str | None = None,
    service: SessionService = Depends(get_session_service),
):
    """List sessions for a campaign."""
    try:
        sessions = await service.list_sessions(campaign_id, session_status)
        return APIResponse(success=True, data=sessions)
    except Exception as e:
        raise APIError(
            ErrorCodes.INTERNAL_ERROR,
            f"Failed to list sessions: {e!s}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e


@router.post(
    "/campaigns/{campaign_id}/sessions",
    response_model=APIResponse[Session],
    status_code=status.HTTP_201_CREATED,
)
async def create_session(
    campaign_id: str,
    started_by: str,
    name: str | None = None,
    notes: str | None = None,
    service: SessionService = Depends(get_session_service),
):
    """Start a new session."""
    try:
        session = await service.create_session(
            campaign_id=campaign_id,
            started_by=started_by,
            name=name,
            notes=notes,
        )
        return APIResponse(success=True, data=session)
    except ValueError as e:
        if "already has an active" in str(e):
            raise APIError(
                ErrorCodes.SESSION_ALREADY_ACTIVE,
                str(e),
                status_code=status.HTTP_409_CONFLICT,
            ) from e
        raise APIError(
            ErrorCodes.VALIDATION_ERROR,
            f"Failed to create session: {e!s}",
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from e
    except Exception as e:
        raise APIError(
            ErrorCodes.INTERNAL_ERROR,
            f"Failed to create session: {e!s}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e


@router.get("/campaigns/{campaign_id}/sessions/active", response_model=APIResponse[Session])
async def get_active_session(
    campaign_id: str,
    service: SessionService = Depends(get_session_service),
):
    """Get current active session for a campaign."""
    try:
        session = await service.get_active_session(campaign_id)
        if session is None:
            raise APIError(
                ErrorCodes.SESSION_NOT_FOUND,
                f"No active session found for campaign {campaign_id}",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return APIResponse(success=True, data=session)
    except APIError:
        raise
    except Exception as e:
        raise APIError(
            ErrorCodes.INTERNAL_ERROR,
            f"Failed to get active session: {e!s}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e


@router.get(
    "/campaigns/{campaign_id}/sessions/{session_id}",
    response_model=APIResponse[Session],
)
async def get_session(
    campaign_id: str,
    session_id: str,
    service: SessionService = Depends(get_session_service),
):
    """Get session details."""
    try:
        session = await service.get_session(campaign_id, session_id)
        return APIResponse(success=True, data=session)
    except FileNotFoundError:
        raise APIError(
            ErrorCodes.SESSION_NOT_FOUND,
            f"Session {session_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        raise APIError(
            ErrorCodes.INTERNAL_ERROR,
            f"Failed to get session: {e!s}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e


@router.put(
    "/campaigns/{campaign_id}/sessions/{session_id}",
    response_model=APIResponse[Session],
)
async def update_session(
    campaign_id: str,
    session_id: str,
    session: Session,
    service: SessionService = Depends(get_session_service),
):
    """Update a session (pause/resume, notes)."""
    try:
        # Ensure session ID matches
        session.metadata.id = session_id
        updated = await service.update_session(campaign_id, session)
        return APIResponse(success=True, data=updated)
    except FileNotFoundError:
        raise APIError(
            ErrorCodes.SESSION_NOT_FOUND,
            f"Session {session_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except ValueError as e:
        if "ended" in str(e).lower():
            raise APIError(
                ErrorCodes.SESSION_ENDED,
                str(e),
                status_code=status.HTTP_409_CONFLICT,
            ) from e
        raise APIError(
            ErrorCodes.VALIDATION_ERROR,
            f"Failed to update session: {e!s}",
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from e
    except Exception as e:
        raise APIError(
            ErrorCodes.INTERNAL_ERROR,
            f"Failed to update session: {e!s}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e


@router.delete(
    "/campaigns/{campaign_id}/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_session(
    campaign_id: str,
    session_id: str,
    service: SessionService = Depends(get_session_service),
):
    """Delete an ended session."""
    try:
        await service.delete_session(campaign_id, session_id)
    except FileNotFoundError:
        raise APIError(
            ErrorCodes.SESSION_NOT_FOUND,
            f"Session {session_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except ValueError as e:
        if "active" in str(e).lower() or "paused" in str(e).lower():
            raise APIError(
                ErrorCodes.SESSION_CANNOT_DELETE,
                str(e),
                status_code=status.HTTP_409_CONFLICT,
            ) from e
        raise APIError(
            ErrorCodes.VALIDATION_ERROR,
            f"Failed to delete session: {e!s}",
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from e
    except Exception as e:
        raise APIError(
            ErrorCodes.INTERNAL_ERROR,
            f"Failed to delete session: {e!s}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e


@router.post(
    "/campaigns/{campaign_id}/sessions/{session_id}/end",
    response_model=APIResponse[Session],
)
async def end_session(
    campaign_id: str,
    session_id: str,
    service: SessionService = Depends(get_session_service),
):
    """End a session."""
    try:
        session = await service.end_session(campaign_id, session_id)
        return APIResponse(success=True, data=session)
    except FileNotFoundError:
        raise APIError(
            ErrorCodes.SESSION_NOT_FOUND,
            f"Session {session_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        raise APIError(
            ErrorCodes.INTERNAL_ERROR,
            f"Failed to end session: {e!s}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e


@router.get(
    "/campaigns/{campaign_id}/sessions/{session_id}/participants",
    response_model=APIResponse[list[SessionParticipant]],
)
async def list_participants(
    campaign_id: str,
    session_id: str,
    service: SessionService = Depends(get_session_service),
):
    """List session participants."""
    try:
        participants = await service.get_participants(campaign_id, session_id)
        return APIResponse(success=True, data=participants)
    except FileNotFoundError:
        raise APIError(
            ErrorCodes.SESSION_NOT_FOUND,
            f"Session {session_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        raise APIError(
            ErrorCodes.INTERNAL_ERROR,
            f"Failed to list participants: {e!s}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e


@router.post(
    "/campaigns/{campaign_id}/sessions/{session_id}/participants",
    response_model=APIResponse[Session],
    status_code=status.HTTP_201_CREATED,
)
async def join_session(
    campaign_id: str,
    session_id: str,
    player_id: str = Body(...),
    character_id: str | None = Body(None),
    is_gm: bool = Body(False),
    service: SessionService = Depends(get_session_service),
):
    """Join a session."""
    try:
        session = await service.join_session(
            campaign_id=campaign_id,
            session_id=session_id,
            player_id=player_id,
            character_id=character_id,
            is_gm=is_gm,
        )
        return APIResponse(success=True, data=session)
    except FileNotFoundError:
        raise APIError(
            ErrorCodes.SESSION_NOT_FOUND,
            f"Session {session_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except ValueError as e:
        error_msg = str(e).lower()
        if "not active" in error_msg:
            raise APIError(
                ErrorCodes.SESSION_NOT_ACTIVE,
                str(e),
                status_code=status.HTTP_409_CONFLICT,
            ) from e
        if "already in active session" in error_msg:
            raise APIError(
                ErrorCodes.PLAYER_ALREADY_IN_SESSION,
                str(e),
                status_code=status.HTTP_409_CONFLICT,
            ) from e
        if "not a member" in error_msg:
            raise APIError(
                ErrorCodes.PLAYER_NOT_CAMPAIGN_MEMBER,
                str(e),
                status_code=status.HTTP_409_CONFLICT,
            ) from e
        if "not assigned" in error_msg or "has no default" in error_msg:
            raise APIError(
                ErrorCodes.CHARACTER_NOT_ASSIGNED,
                str(e),
                status_code=status.HTTP_409_CONFLICT,
            ) from e
        raise APIError(
            ErrorCodes.VALIDATION_ERROR,
            f"Failed to join session: {e!s}",
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from e
    except Exception as e:
        raise APIError(
            ErrorCodes.INTERNAL_ERROR,
            f"Failed to join session: {e!s}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e


@router.delete(
    "/campaigns/{campaign_id}/sessions/{session_id}/participants/{player_id}",
    response_model=APIResponse[Session],
)
async def leave_session(
    campaign_id: str,
    session_id: str,
    player_id: str,
    service: SessionService = Depends(get_session_service),
):
    """Leave a session."""
    try:
        session = await service.leave_session(campaign_id, session_id, player_id)
        return APIResponse(success=True, data=session)
    except FileNotFoundError:
        raise APIError(
            ErrorCodes.SESSION_NOT_FOUND,
            f"Session {session_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except ValueError as e:
        raise APIError(
            ErrorCodes.PARTICIPANT_NOT_FOUND,
            str(e),
            status_code=status.HTTP_404_NOT_FOUND,
        ) from e
    except Exception as e:
        raise APIError(
            ErrorCodes.INTERNAL_ERROR,
            f"Failed to leave session: {e!s}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e
