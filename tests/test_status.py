def test_invalid_status_requires_authentication(client):
    response = client.put(
        "/issues/1/status",
        json={
            "status": "Invalid Status"
        }
    )

    assert response.status_code in [401, 403, 404]


def test_status_update_requires_authentication(client):
    response = client.put(
        "/issues/1/status",
        json={
            "status": "In Progress"
        }
    )

    assert response.status_code in [401, 403, 404]