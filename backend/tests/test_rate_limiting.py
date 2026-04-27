import pytest


@pytest.mark.skip(reason="Rate limiting doesn't work with TestClient - requires real HTTP requests")
def test_rate_limiting_on_login(client):
    """Test that rate limiting works on login endpoint"""
    # Try to login 6 times (limit is 5/minute)
    for i in range(6):
        response = client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )
        if i < 5:
            # First 5 should work (even if credentials are wrong)
            assert response.status_code in [401, 422]  # Unauthorized or validation error
        else:
            # 6th should be rate limited
            assert response.status_code == 429


@pytest.mark.skip(reason="Rate limiting doesn't work with TestClient - requires real HTTP requests")
def test_rate_limiting_on_register(client):
    """Test that rate limiting works on register endpoint"""
    # Try to register 6 times (limit is 5/minute)
    for i in range(6):
        response = client.post(
            "/api/auth/register",
            json={
                "email": f"test{i}@example.com",
                "password": "password123",
                "password_confirmation": "password123",
            },
        )
        if i < 5:
            # First 5 should work
            assert response.status_code == 201
        else:
            # 6th should be rate limited
            assert response.status_code == 429


@pytest.mark.skip(reason="Rate limiting doesn't work with TestClient - requires real HTTP requests")
def test_rate_limiting_on_activate_key(client):
    """Test that rate limiting works on activate-key endpoint"""
    # Try to activate 11 times (limit is 10/minute)
    for i in range(11):
        response = client.post(
            "/api/proxy/activate-key",
            json={"activation_key": "invalid_key"},
        )
        if i < 10:
            # First 10 should work (even if key is invalid)
            assert response.status_code in [404, 503]
        else:
            # 11th should be rate limited
            assert response.status_code == 429
