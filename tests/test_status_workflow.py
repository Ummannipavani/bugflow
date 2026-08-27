import uuid


def register_and_login(client, role):
    email = f"status_{uuid.uuid4().hex[:8]}@example.com"
    password = "Test@12345"

    register_response = client.post(
        "/register",
        json={
            "name": f"Test {role}",
            "email": email,
            "password": password,
            "role": role
        }
    )

    assert register_response.status_code == 200

    login_response = client.post(
        "/login",
        json={
            "email": email,
            "password": password
        }
    )

    assert login_response.status_code == 200

    return email


def create_issue(client):
    response = client.post(
        "/issues",
        data={
            "title": "Status Workflow Test",
            "project": "Status Test Project",
            "priority": "P2",
            "severity": "Medium",
            "category": "Backend",
            "module": "API",
            "defect_type": "Functional",
            "description": "Testing status transitions.",
            "due_date": "2026-12-31"
        }
    )

    assert response.status_code == 200

    return response.json()["issue_id"]


def test_open_to_in_progress(client):
    register_and_login(client, "Project Manager")

    issue_id = create_issue(client)

    response = client.put(
        f"/issues/{issue_id}/status",
        json={
            "status": "In Progress"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "In Progress"


def test_invalid_status(client):
    register_and_login(client, "Project Manager")

    issue_id = create_issue(client)

    response = client.put(
        f"/issues/{issue_id}/status",
        json={
            "status": "Something Invalid"
        }
    )

    assert response.status_code == 400