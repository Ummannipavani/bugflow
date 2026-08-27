import uuid


def test_login_page(client):
    response = client.get("/")

    assert response.status_code == 200


def test_register_page(client):
    response = client.get("/register")

    assert response.status_code == 200


def test_dashboard_requires_login(client):
    response = client.get(
        "/dashboard",
        follow_redirects=False
    )

    assert response.status_code in [302, 303]


def test_register_and_login(client):
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    password = "Test@12345"

    # -----------------------------
    # REGISTER
    # -----------------------------
    register_response = client.post(
        "/register",
        json={
            "name": "Test Developer",
            "email": email,
            "password": password,
            "role": "Developer"
        }
    )

    assert register_response.status_code == 200

    # -----------------------------
    # LOGIN
    # -----------------------------
    login_response = client.post(
        "/login",
        json={
            "email": email,
            "password": password
        }
    )

    assert login_response.status_code == 200

    data = login_response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_invalid_login(client):
    response = client.post(
        "/login",
        json={
            "email": "nonexistent_user@example.com",
            "password": "WrongPassword123"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Invalid email or password"