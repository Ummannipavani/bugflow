def test_get_nonexistent_issue(client):
    response = client.get("/issues/999999")

    assert response.status_code in [401, 403, 404]


def test_create_issue_requires_authentication(client):
    response = client.post(
        "/issues",
        data={
            "title": "Test Bug",
            "project": "Test Project",
            "priority": "P2",
            "severity": "Medium",
            "category": "Backend",
            "module": "API",
            "defect_type": "Functional",
            "description": "This is a test defect.",
            "due_date": "2026-12-31",
        }
    )

    assert response.status_code in [401, 403]


def test_issue_details_requires_authentication(client):
    response = client.get(
        "/issues/1/details"
    )

    assert response.status_code in [401, 403, 404]