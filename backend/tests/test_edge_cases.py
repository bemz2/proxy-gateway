import threading
import time


def create_user_and_login(client, email):
    """Helper function to create user and get token"""
    register_response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "password123",
            "password_confirmation": "password123",
        },
    )
    activation_key = register_response.json()["activation_key"]

    login_response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "password123"},
    )
    token = login_response.json()["access_token"]
    return activation_key, token


def test_concurrent_vm_allocation(client):
    """Test that two users cannot get the same VM"""
    # Create one VM
    activation_key1, token1 = create_user_and_login(client, "user1@example.com")
    
    client.post(
        "/api/vms",
        headers={"Authorization": f"Bearer {token1}"},
        json={
            "name": "single-vm",
            "host": "127.0.0.1",
            "port": 1080,
            "protocol": "socks5",
            "is_active": True,
        },
    )

    # Create second user
    activation_key2, _ = create_user_and_login(client, "user2@example.com")

    # First user activates successfully
    response1 = client.post("/api/proxy/activate-key", json={"activation_key": activation_key1})
    assert response1.status_code == 200

    # Second user should fail (no free VMs)
    response2 = client.post("/api/proxy/activate-key", json={"activation_key": activation_key2})
    assert response2.status_code == 503
    assert "заняты" in response2.json()["detail"].lower()


def test_vm_pagination(client):
    """Test VM list pagination"""
    activation_key, token = create_user_and_login(client, "admin@example.com")

    # Create 5 VMs
    for i in range(5):
        client.post(
            "/api/vms",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": f"vm-{i}",
                "host": "127.0.0.1",
                "port": 1080 + i,
                "protocol": "socks5",
                "is_active": True,
            },
        )

    # Get first 2
    response1 = client.get("/api/vms?skip=0&limit=2", headers={"Authorization": f"Bearer {token}"})
    assert response1.status_code == 200
    assert len(response1.json()) == 2

    # Get next 2
    response2 = client.get("/api/vms?skip=2&limit=2", headers={"Authorization": f"Bearer {token}"})
    assert response2.status_code == 200
    assert len(response2.json()) == 2

    # Get last 1
    response3 = client.get("/api/vms?skip=4&limit=2", headers={"Authorization": f"Bearer {token}"})
    assert response3.status_code == 200
    assert len(response3.json()) == 1


def test_vm_protocol_validation(client):
    """Test that only valid protocols are accepted"""
    activation_key, token = create_user_and_login(client, "admin@example.com")

    # Valid protocol
    response1 = client.post(
        "/api/vms",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "valid-vm",
            "host": "127.0.0.1",
            "port": 1080,
            "protocol": "socks5",
            "is_active": True,
        },
    )
    assert response1.status_code == 201

    # Invalid protocol
    response2 = client.post(
        "/api/vms",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "invalid-vm",
            "host": "127.0.0.1",
            "port": 1081,
            "protocol": "invalid_protocol",
            "is_active": True,
        },
    )
    assert response2.status_code == 422


def test_vm_port_validation(client):
    """Test that port validation works"""
    activation_key, token = create_user_and_login(client, "admin@example.com")

    # Invalid port (too high)
    response1 = client.post(
        "/api/vms",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "invalid-port-vm",
            "host": "127.0.0.1",
            "port": 99999,
            "protocol": "socks5",
            "is_active": True,
        },
    )
    assert response1.status_code == 422

    # Invalid port (too low)
    response2 = client.post(
        "/api/vms",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "invalid-port-vm2",
            "host": "127.0.0.1",
            "port": 0,
            "protocol": "socks5",
            "is_active": True,
        },
    )
    assert response2.status_code == 422
