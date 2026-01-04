"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import get_scalar_api_reference, Layout, SearchHotKey


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
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
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
    from .routers import campaigns, characters, actions, chat, tools, rules, health

    app.include_router(health.router, tags=["Health"])
    app.include_router(campaigns.router, prefix="/api/v1", tags=["Campaigns"])
    app.include_router(characters.router, prefix="/api/v1", tags=["Characters"])
    app.include_router(actions.router, prefix="/api/v1", tags=["Actions"])
    app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
    app.include_router(tools.router, prefix="/api/v1", tags=["Tools"])
    app.include_router(rules.router, prefix="/api/v1", tags=["Rules"])

    return app
