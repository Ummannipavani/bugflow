def test_ai_analyze_requires_authentication(client):
    response = client.post(
        "/ai/analyze",
        json={
            "title": "Login failure",
            "description": "Users cannot login to the application."
        }
    )

    assert response.status_code in [401, 403, 422]


def test_similar_defects_requires_authentication(client):
    response = client.post(
        "/ai/similar-defects",
        json={
            "title": "Login failure",
            "description": "Users cannot login."
        }
    )

    assert response.status_code in [401, 403, 422]


def test_resolution_requires_authentication(client):
    response = client.post(
        "/ai/resolve",
        json={
            "title": "Login failure",
            "description": "Users cannot login."
        }
    )

    assert response.status_code in [401, 403, 422]