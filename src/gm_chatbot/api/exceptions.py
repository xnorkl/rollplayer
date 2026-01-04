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
