import uuid


def register_and_login(client, role):
    email = f"permission_{uuid.uuid4().hex[:8]}@example.com"
    password = "Test@12345"

    client.post(
        "/register",
        json={
            "name": f"Permission {role}",
            "email": email,
            "password": password,
            "role": role
        }
    )

    response = client.post(
        "/login",
        json={
            "email": email,
            "password": password
        }
    )

    assert response.status_code == 200

    return email


def create_issue(client):
    response = client.post(
        "/issues",
        data={
            "title": "Permission Test Issue",
            "project": "Permission Test Project",
            "priority": "P2",
            "severity": "Medium",
            "category": "Backend",
            "module": "API",
            "defect_type": "Functional",
            "description": "Testing permissions.",
            "due_date": "2026-12-31"
        }
    )

    assert response.status_code == 200

    return response.json()["issue_id"]


def test_reporter_cannot_delete_issue(client):
    register_and_login(client, "Reporter")

    issue_id = create_issue(client)

    response = client.delete(
        f"/issues/{issue_id}"
    )

    assert response.status_code in [401, 403]


def test_reporter_cannot_update_status(client):
    register_and_login(client, "Reporter")

    issue_id = create_issue(client)

    response = client.put(
        f"/issues/{issue_id}/status",
        json={
            "status": "In Progress"
        }
    )

    assert response.status_code in [401, 403]


def test_reporter_cannot_assign_issue(client):
    register_and_login(client, "Reporter")

    issue_id = create_issue(client)

    response = client.put(
        f"/issues/{issue_id}/assignee",
        json={
            "assigned_to": 1
        }
    )

    assert response.status_code in [401, 403]