"""Store fixtures for testing."""

import os
import shutil
import tempfile
from pathlib import Path

import pytest

from gm_chatbot.artifacts.store import ArtifactStore


@pytest.fixture
def temp_campaigns_dir():
    """Create temporary campaigns directory."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def artifact_store():
    """Create artifact store using environment variables if set, otherwise temp directory."""
    # If environment variables are set (by setup_test_env), use them
    # Otherwise, create a temp directory
    if "CAMPAIGNS_DIR" in os.environ:
        store = ArtifactStore()
        yield store
    else:
        # Fallback for tests that don't use setup_test_env
        temp_dir = tempfile.mkdtemp()
        campaigns_dir = Path(temp_dir) / "campaigns"
        players_dir = Path(temp_dir) / "players"
        campaigns_dir.mkdir(parents=True, exist_ok=True)
        players_dir.mkdir(parents=True, exist_ok=True)
        store = ArtifactStore(campaigns_dir=str(campaigns_dir), players_dir=str(players_dir))
        yield store
        shutil.rmtree(temp_dir, ignore_errors=True)
