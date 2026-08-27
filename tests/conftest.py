import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def authenticated_client():
    client = TestClient(app)

    # Create a session by calling the ASGI application
    # through a custom session middleware-compatible approach.
    client.cookies.set(
        "session",
        ""
    )

    return client