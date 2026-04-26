def test_login_success(client):
    """Test successful login"""
    # Register user first
    client.post(
        "/api/auth/register",
        json={
            "email": "user@example.com",
            "password": "password123",
            "password_confirmation": "password123",
        },
    )

    # Login
    response = client.post(
        "/api/auth/login",
        json={"email": "user@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    """Test login with wrong password"""
    # Register user first
    client.post(
        "/api/auth/register",
        json={
            "email": "user@example.com",
            "password": "password123",
            "password_confirmation": "password123",
        },
    )

    # Try login with wrong password
    response = client.post(
        "/api/auth/login",
        json={"email": "user@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_login_nonexistent_user(client):
    """Test login with non-existent user"""
    response = client.post(
        "/api/auth/login",
        json={"email": "nonexistent@example.com", "password": "password123"},
    )
    assert response.status_code == 401


def test_login_missing_fields(client):
    """Test login with missing fields"""
    response = client.post(
        "/api/auth/login",
        json={"email": "user@example.com"},
    )
    assert response.status_code == 422
