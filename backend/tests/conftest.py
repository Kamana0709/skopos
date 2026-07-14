"""Test fixtures."""

import pytest
from fastapi.testclient import TestClient
from skopos.backend.main import app


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)