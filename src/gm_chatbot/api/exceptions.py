"""API exception classes."""

from fastapi import HTTPException, status


class APIError(HTTPException):
    """Custom API error exception."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: dict | None = None,
    ):
        """
        Initialize API error.

        Args:
            code: Error code
            message: Error message
            status_code: HTTP status code
            details: Optional error details
        """
        super().__init__(
            status_code=status_code,
            detail={
                "code": code,
                "message": message,
                "details": details,
            },
        )


class ErrorCodes:
    """Standard error codes."""

    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    ARTIFACT_INVALID = "ARTIFACT_INVALID"
    CAMPAIGN_NOT_FOUND = "CAMPAIGN_NOT_FOUND"
    CHARACTER_NOT_FOUND = "CHARACTER_NOT_FOUND"
    DICE_EXPRESSION_INVALID = "DICE_EXPRESSION_INVALID"
    LLM_ERROR = "LLM_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    # Player errors
    PLAYER_NOT_FOUND = "PLAYER_NOT_FOUND"
    PLAYER_ALREADY_IN_SESSION = "PLAYER_ALREADY_IN_SESSION"
    PLAYER_IN_ACTIVE_SESSION = "PLAYER_IN_ACTIVE_SESSION"
    PLAYER_NOT_CAMPAIGN_MEMBER = "PLAYER_NOT_CAMPAIGN_MEMBER"
    PLAYER_ALREADY_IN_CAMPAIGN = "PLAYER_ALREADY_IN_CAMPAIGN"
    USERNAME_ALREADY_EXISTS = "USERNAME_ALREADY_EXISTS"
    # Session errors
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    SESSION_ALREADY_ACTIVE = "SESSION_ALREADY_ACTIVE"
    SESSION_NOT_ACTIVE = "SESSION_NOT_ACTIVE"
    SESSION_CANNOT_DELETE = "SESSION_CANNOT_DELETE"
    SESSION_ENDED = "SESSION_ENDED"
    PARTICIPANT_NOT_FOUND = "PARTICIPANT_NOT_FOUND"
    # Character assignment errors
    CHARACTER_NOT_ASSIGNED = "CHARACTER_NOT_ASSIGNED"
