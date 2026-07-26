TEST_PASSWORD = "StrongTestPassword123!"


def test_a1_register_new_user(client):
    response = client.post(
        "/api/v1/users/register",
        json={
            "email": "new-user@example.com",
            "name": "新用户",
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code in (200, 201)
    assert response.json()["email"] == "new-user@example.com"


def test_a2_duplicate_email_rejected(client, user_a):
    response = client.post(
        "/api/v1/users/register",
        json={
            "email": user_a.email,
            "name": "重复用户",
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 400


def test_a3_login_returns_access_token(client, user_a):
    response = client.post(
        "/api/v1/users/login",
        data={"username": user_a.email, "password": TEST_PASSWORD},
    )

    assert response.status_code == 200
    assert response.json()["access_token"]


def test_a4_wrong_password_is_unauthorized(client, user_a):
    response = client.post(
        "/api/v1/users/login",
        data={"username": user_a.email, "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_a5_glucose_requires_token(client):
    response = client.get("/api/v1/glucose")

    assert response.status_code == 401
    assert response.json()["code"] == "http_error"
