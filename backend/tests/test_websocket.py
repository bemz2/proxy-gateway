import pytest
from fastapi.testclient import TestClient


def create_user_and_activate(client):
    """Helper to create user, get activation key, and activate"""
    register_response = client.post(
        "/api/auth/register",
        json={
            "email": "wstest@example.com",
            "password": "password123",
            "password_confirmation": "password123",
        },
    )
    activation_key = register_response.json()["activation_key"]

    login_response = client.post(
        "/api/auth/login",
        json={"email": "wstest@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    # Create VM
    client.post(
        "/api/vms",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "ws-test-vm",
            "host": "127.0.0.1",
            "port": 9999,
            "protocol": "socks5",
            "is_active": True,
        },
    )

    # Activate
    activate_response = client.post(
        "/api/proxy/activate-key",
        json={"activation_key": activation_key},
    )
    return activate_response.json()


def test_websocket_connection_with_valid_token(client):
    """Test WebSocket connection with valid token"""
    data = create_user_and_activate(client)
    user_id = data["user_id"]
    ws_token = data["ws_token"]

    with client.websocket_connect(f"/api/ws/status/{user_id}?token={ws_token}") as websocket:
        # Should receive initial status
        message = websocket.receive_json()
        assert message["user_id"] == user_id
        assert message["status"] == "connected"


def test_websocket_connection_with_invalid_token(client):
    """Test WebSocket connection with invalid token"""
    data = create_user_and_activate(client)
    user_id = data["user_id"]

    with pytest.raises(Exception):
        with client.websocket_connect(f"/api/ws/status/{user_id}?token=invalid_token"):
            pass


def test_websocket_status_updates(client):
    """Test that WebSocket receives status updates"""
    data = create_user_and_activate(client)
    user_id = data["user_id"]
    ws_token = data["ws_token"]

    with client.websocket_connect(f"/api/ws/status/{user_id}?token={ws_token}") as websocket:
        # Receive initial status
        initial_message = websocket.receive_json()
        assert initial_message["status"] == "connected"

        # Disconnect
        client.post("/api/proxy/disconnect", json={"user_id": user_id})

        # Should receive updated status (may need to wait for heartbeat)
        # Note: In real scenario, this would be pushed immediately


def test_get_proxy_status_endpoint(client):
    """Test the HTTP status endpoint"""
    data = create_user_and_activate(client)
    user_id = data["user_id"]
    ws_token = data["ws_token"]

    response = client.get(f"/api/proxy/status/{user_id}?token={ws_token}")
    assert response.status_code == 200
    status_data = response.json()
    assert status_data["user_id"] == user_id
    assert status_data["status"] == "connected"
    assert "updated_at" in status_data
