import uuid


def register_and_login(client, role="Developer"):
    email = f"workflow_{uuid.uuid4().hex[:8]}@example.com"
    password = "Test@12345"

    # Register
    register_response = client.post(
        "/register",
        json={
            "name": "Workflow Tester",
            "email": email,
            "password": password,
            "role": role
        }
    )

    assert register_response.status_code == 200

    # Login
    login_response = client.post(
        "/login",
        json={
            "email": email,
            "password": password
        }
    )

    assert login_response.status_code == 200

    return email


def test_authenticated_dashboard(client):
    register_and_login(client)

    response = client.get("/dashboard")

    assert response.status_code == 200


def test_authenticated_issue_access(client):
    register_and_login(client)

    response = client.get("/issues")

    assert response.status_code == 200


def test_create_issue(client):
    register_and_login(client)

    response = client.post(
        "/issues",
        data={
            "title": "Automated Test Bug",
            "project": "BugFlow Test Project",
            "priority": "P2",
            "severity": "Medium",
            "category": "Backend",
            "module": "API",
            "defect_type": "Functional",
            "description": "This defect was created during automated testing.",
            "due_date": "2026-12-31"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "issue_id" in data
    assert data["message"] == "Issue reported successfully!"
    assert data["status"] in [
        "Open",
        "In Progress"
    ]