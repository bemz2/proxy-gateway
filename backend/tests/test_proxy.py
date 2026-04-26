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


def test_activate_key_with_available_vm(client):
    """Test activating key when VM is available"""
    activation_key, token = create_user_and_login(client)

    # Create a VM
    client.post(
        "/api/vms",
        headers=auth_headers(token),
        json={
            "name": "proxy-1",
            "host": "127.0.0.1",
            "port": 1080,
            "protocol": "socks5",
            "is_active": True,
        },
    )

    # Activate key
    response = client.post("/api/proxy/activate-key", json={"activation_key": activation_key})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "connected"
    assert data["user_id"] is not None
    assert data["ws_token"] is not None
    assert data["vm"]["name"] == "proxy-1"


def test_activate_key_invalid(client):
    """Test activating with invalid key"""
    response = client.post("/api/proxy/activate-key", json={"activation_key": "invalid_key_12345"})
    assert response.status_code == 404


def test_activate_key_no_free_vm(client):
    """Test activating key when no VMs are available"""
    activation_key, _ = create_user_and_login(client)

    response = client.post("/api/proxy/activate-key", json={"activation_key": activation_key})
    assert response.status_code == 503
    assert "заняты" in response.json()["detail"].lower() or "busy" in response.json()["detail"].lower()


def test_activate_key_consumed_after_use(client):
    """Test that activation key is consumed after use"""
    activation_key, token = create_user_and_login(client)

    # Create a VM
    client.post(
        "/api/vms",
        headers=auth_headers(token),
        json={
            "name": "proxy-1",
            "host": "127.0.0.1",
            "port": 1080,
            "protocol": "socks5",
            "is_active": True,
        },
    )

    # Activate key
    response1 = client.post("/api/proxy/activate-key", json={"activation_key": activation_key})
    assert response1.status_code == 200

    # Try to use same key again
    response2 = client.post("/api/proxy/activate-key", json={"activation_key": activation_key})
    assert response2.status_code == 404


def test_disconnect_proxy_success(client):
    """Test disconnecting from proxy"""
    activation_key, token = create_user_and_login(client)

    # Create and activate VM
    client.post(
        "/api/vms",
        headers=auth_headers(token),
        json={
            "name": "proxy-1",
            "host": "127.0.0.1",
            "port": 1080,
            "protocol": "socks5",
            "is_active": True,
        },
    )

    activate_response = client.post("/api/proxy/activate-key", json={"activation_key": activation_key})
    user_id = activate_response.json()["user_id"]

    # Disconnect
    response = client.post("/api/proxy/disconnect", json={"user_id": user_id})
    assert response.status_code == 200


def test_disconnect_proxy_not_connected(client):
    """Test disconnecting when not connected"""
    response = client.post("/api/proxy/disconnect", json={"user_id": 99999})
    assert response.status_code == 404


def test_get_proxy_status(client):
    """Test getting proxy status"""
    activation_key, token = create_user_and_login(client)

    # Create and activate VM
    client.post(
        "/api/vms",
        headers=auth_headers(token),
        json={
            "name": "proxy-1",
            "host": "127.0.0.1",
            "port": 1080,
            "protocol": "socks5",
            "is_active": True,
        },
    )

    activate_response = client.post("/api/proxy/activate-key", json={"activation_key": activation_key})
    user_id = activate_response.json()["user_id"]
    ws_token = activate_response.json()["ws_token"]

    # Get status
    response = client.get(f"/api/proxy/status/{user_id}?token={ws_token}")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == user_id
    assert data["status"] == "connected"


def test_get_proxy_status_invalid_token(client):
    """Test getting status with invalid token"""
    response = client.get("/api/proxy/status/1?token=invalid_token")
    assert response.status_code == 401
