"""FastAPI application factory."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from scalar_fastapi import Layout, SearchHotKey, get_scalar_api_reference

from .exceptions import APIError


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI app
    """
    app = FastAPI(
        title="GM Chatbot API",
        version="2.0.0",
        openapi_version="3.1.0",
        description="Game Master Assistant API for tabletop RPGs",
        servers=[
            {"url": "http://localhost:8000", "description": "Development"},
            {"url": "https://gm-chatbot.fly.dev", "description": "Production"},
        ],
        docs_url=None,  # Disable default Swagger UI
        redoc_url=None,  # Disable default ReDoc
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,  # type: ignore[arg-type]
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handler for FastAPI validation errors
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request, exc: RequestValidationError
    ):
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors()},
        )

    # Custom exception handler for APIError to return {"error": {...}} format
    @app.exception_handler(APIError)
    async def api_error_handler(_request: Request, exc: APIError):
        """Handle APIError exceptions and return standardized error format."""
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail},
        )

    # Scalar API Reference
    @app.get("/docs", include_in_schema=False)
    async def scalar_docs():
        """Serve Scalar API Reference documentation."""
        return get_scalar_api_reference(
            openapi_url=app.openapi_url,
            title="GM Chatbot API",
            layout=Layout.MODERN,
            dark_mode=True,
            hide_dark_mode_toggle=False,
            show_sidebar=True,
            search_hot_key=SearchHotKey.K,
            default_open_all_tags=False,
            hide_download_button=False,
            persist_auth=True,
        )

    # Include routers
    from .routers import (
        actions,
        campaigns,
        characters,
        chat,
        health,
        players,
        rules,
        sessions,
        tools,
    )
    from .routers import (
        discord as discord_router,
    )

    app.include_router(health.router, tags=["Health"])
    app.include_router(campaigns.router, prefix="/api/v1", tags=["Campaigns"])
    app.include_router(characters.router, prefix="/api/v1", tags=["Characters"])
    app.include_router(actions.router, prefix="/api/v1", tags=["Actions"])
    app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
    app.include_router(tools.router, prefix="/api/v1", tags=["Tools"])
    app.include_router(rules.router, prefix="/api/v1", tags=["Rules"])
    app.include_router(players.router, prefix="/api/v1", tags=["Players"])
    app.include_router(sessions.router, prefix="/api/v1", tags=["Sessions"])
    app.include_router(discord_router.router, prefix="/api/v1", tags=["Discord"])

    return app


# Create app instance for uvicorn
app = create_app()
