"""Pytest fixtures for smoke tests."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture(scope="module")
def smoke_env() -> Generator[Path, None, None]:
    """Create isolated temp directory for smoke test module."""
    temp_dir = Path(tempfile.mkdtemp(prefix="pytest_smoke_"))
    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="module")
def smoke_store(smoke_env: Path):
    """Artifact store for smoke tests."""
    from gm_chatbot.artifacts.store import ArtifactStore
    return ArtifactStore(
        campaigns_dir=smoke_env / "campaigns",
        players_dir=smoke_env / "players",
    )


@pytest.fixture(scope="module")
def smoke_services(smoke_store):
    """All services for smoke tests."""
    from gm_chatbot.services.campaign_service import CampaignService
    from gm_chatbot.services.player_service import PlayerService
    from gm_chatbot.services.session_service import SessionService

    return {
        "store": smoke_store,
        "campaign": CampaignService(smoke_store),
        "player": PlayerService(smoke_store),
        "session": SessionService(smoke_store),
    }
