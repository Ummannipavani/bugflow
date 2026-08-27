import os

# Tell the application that we are running tests
os.environ["TESTING"] = "1"

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def authenticated_client():
    client = TestClient(app)

    client.cookies.set(
        "session",
        ""
    )

    return client