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


def test_create_vm_success(client):
    """Test creating a virtual machine"""
    _, token = create_user_and_login(client)

    response = client.post(
        "/api/vms",
        headers=auth_headers(token),
        json={
            "name": "test-vm-1",
            "host": "192.168.1.1",
            "port": 8080,
            "protocol": "http",
            "is_active": True,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test-vm-1"
    assert data["host"] == "192.168.1.1"
    assert data["port"] == 8080
    assert data["protocol"] == "http"
    assert data["is_active"] is True


def test_create_vm_duplicate_name(client):
    """Test creating VM with duplicate name"""
    _, token = create_user_and_login(client)

    vm_data = {
        "name": "duplicate-vm",
        "host": "192.168.1.1",
        "port": 8080,
        "protocol": "http",
        "is_active": True,
    }

    response1 = client.post("/api/vms", headers=auth_headers(token), json=vm_data)
    assert response1.status_code == 201

    response2 = client.post("/api/vms", headers=auth_headers(token), json=vm_data)
    assert response2.status_code == 400


def test_create_vm_unauthorized(client):
    """Test creating VM without authentication"""
    response = client.post(
        "/api/vms",
        json={
            "name": "test-vm",
            "host": "192.168.1.1",
            "port": 8080,
            "protocol": "http",
            "is_active": True,
        },
    )
    assert response.status_code == 401


def test_list_vms(client):
    """Test listing virtual machines"""
    _, token = create_user_and_login(client)

    # Create some VMs
    for i in range(3):
        client.post(
            "/api/vms",
            headers=auth_headers(token),
            json={
                "name": f"vm-{i}",
                "host": f"192.168.1.{i}",
                "port": 8080 + i,
                "protocol": "http",
                "is_active": True,
            },
        )

    response = client.get("/api/vms", headers=auth_headers(token))
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3


def test_get_vm_by_id(client):
    """Test getting VM by ID"""
    _, token = create_user_and_login(client)

    # Create VM
    create_response = client.post(
        "/api/vms",
        headers=auth_headers(token),
        json={
            "name": "test-vm",
            "host": "192.168.1.1",
            "port": 8080,
            "protocol": "http",
            "is_active": True,
        },
    )
    vm_id = create_response.json()["id"]

    # Get VM
    response = client.get(f"/api/vms/{vm_id}", headers=auth_headers(token))
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == vm_id
    assert data["name"] == "test-vm"


def test_get_vm_not_found(client):
    """Test getting non-existent VM"""
    _, token = create_user_and_login(client)

    response = client.get("/api/vms/99999", headers=auth_headers(token))
    assert response.status_code == 404
