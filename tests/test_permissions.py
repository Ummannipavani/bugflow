def test_delete_issue_requires_authentication(client):
    response = client.delete(
        "/issues/1"
    )

    assert response.status_code in [401, 403, 404]


def test_update_assignee_requires_authentication(client):
    response = client.put(
        "/issues/1/assignee",
        json={
            "assigned_to": 1
        }
    )

    assert response.status_code in [401, 403, 404]


def test_update_sprint_requires_authentication(client):
    response = client.put(
        "/issues/1/sprint",
        json={
            "sprint_id": 1
        }
    )

    assert response.status_code in [401, 403, 404]


def test_comments_require_authentication(client):
    response = client.post(
        "/issues/1/comments",
        data={
            "comment": "Test comment"
        }
    )

    assert response.status_code in [401, 403, 404]