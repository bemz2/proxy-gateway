def create_user_and_login(client):
    """Helper function to create user and get token"""
    register_response = client.post(
        "/api/auth/register",
        json={
            "email": "user@example.com",
            "password": "password123",
            "password_confirmation": "password123",
        },
    )
    activation_key = register_response.json()["activation_key"]

    login_response = client.post(
        "/api/auth/login",
        json={"email": "user@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]
    return activation_key, token


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_get_profile_success(client):
    """Test getting user profile"""
    _, token = create_user_and_login(client)

    response = client.get("/api/profile", headers=auth_headers(token))
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "user@example.com"
    assert "activation_key" in data


def test_get_profile_unauthorized(client):
    """Test getting profile without token"""
    response = client.get("/api/profile")
    assert response.status_code == 401


def test_get_profile_invalid_token(client):
    """Test getting profile with invalid token"""
    response = client.get("/api/profile", headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 401


def test_refresh_key_success(client):
    """Test refreshing activation key"""
    _, token = create_user_and_login(client)

    # Get old key
    profile_response = client.get("/api/profile", headers=auth_headers(token))
    old_key = profile_response.json()["activation_key"]

    # Refresh key
    response = client.post("/api/profile/refresh-key", headers=auth_headers(token))
    assert response.status_code == 200
    new_key = response.json()["activation_key"]
    assert new_key != old_key
    assert len(new_key) == 32


def test_refresh_key_unauthorized(client):
    """Test refreshing key without token"""
    response = client.post("/api/profile/refresh-key")
    assert response.status_code == 401


def test_change_password_success(client):
    """Test changing password"""
    _, token = create_user_and_login(client)

    response = client.post(
        "/api/profile/change-password",
        headers=auth_headers(token),
        json={
            "current_password": "password123",
            "new_password": "newpassword123",
            "new_password_confirmation": "newpassword123",
        },
    )
    assert response.status_code == 204

    # Try login with new password
    login_response = client.post(
        "/api/auth/login",
        json={"email": "user@example.com", "password": "newpassword123"},
    )
    assert login_response.status_code == 200


def test_change_password_wrong_current(client):
    """Test changing password with wrong current password"""
    _, token = create_user_and_login(client)

    response = client.post(
        "/api/profile/change-password",
        headers=auth_headers(token),
        json={
            "current_password": "wrongpassword",
            "new_password": "newpassword123",
            "new_password_confirmation": "newpassword123",
        },
    )
    assert response.status_code == 400


def test_change_password_mismatch(client):
    """Test changing password with mismatched new passwords"""
    _, token = create_user_and_login(client)

    response = client.post(
        "/api/profile/change-password",
        headers=auth_headers(token),
        json={
            "current_password": "password123",
            "new_password": "newpassword123",
            "new_password_confirmation": "different123",
        },
    )
    assert response.status_code == 400


def test_change_password_too_short(client):
    """Test changing password to a short password"""
    _, token = create_user_and_login(client)

    response = client.post(
        "/api/profile/change-password",
        headers=auth_headers(token),
        json={
            "current_password": "password123",
            "new_password": "short",
            "new_password_confirmation": "short",
        },
    )
    assert response.status_code in [400, 422]
