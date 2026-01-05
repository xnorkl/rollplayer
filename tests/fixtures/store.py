"""Store fixtures for testing."""

import pytest
import shutil
import tempfile
from pathlib import Path

from gm_chatbot.artifacts.store import ArtifactStore


@pytest.fixture
def temp_campaigns_dir():
    """Create temporary campaigns directory."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def artifact_store(temp_campaigns_dir):
    """Create artifact store with temp directory."""
    return ArtifactStore(campaigns_dir=temp_campaigns_dir)
