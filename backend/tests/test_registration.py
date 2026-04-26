import pytest


def test_register_success(client):
    """Test successful user registration"""
    response = client.post(
        "/api/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "password123",
            "password_confirmation": "password123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "activation_key" in data
    assert len(data["activation_key"]) == 32


def test_register_duplicate_email(client):
    """Test registration with duplicate email"""
    payload = {
        "email": "duplicate@example.com",
        "password": "password123",
        "password_confirmation": "password123",
    }
    response1 = client.post("/api/auth/register", json=payload)
    assert response1.status_code == 201

    response2 = client.post("/api/auth/register", json=payload)
    assert response2.status_code == 400
    assert "already registered" in response2.json()["detail"].lower()


def test_register_password_mismatch(client):
    """Test registration with mismatched passwords"""
    response = client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "password": "password123",
            "password_confirmation": "different123",
        },
    )
    assert response.status_code == 400
    assert "do not match" in response.json()["detail"].lower()


def test_register_short_password(client):
    """Test registration with short password"""
    response = client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "password": "short",
            "password_confirmation": "short",
        },
    )
    assert response.status_code == 422  # Pydantic validation error


def test_register_invalid_email(client):
    """Test registration with invalid email format"""
    response = client.post(
        "/api/auth/register",
        json={
            "email": "invalid-email",
            "password": "password123",
            "password_confirmation": "password123",
        },
    )
    assert response.status_code == 422


def test_register_missing_fields(client):
    """Test registration with missing required fields"""
    response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com"},
    )
    assert response.status_code == 422
