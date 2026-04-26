def create_user_and_login(client):
    register_payload = {
        "email": "user@example.com",
        "password": "password123",
        "password_confirmation": "password123",
    }
    register_response = client.post("/api/auth/register", json=register_payload)
    assert register_response.status_code == 201
    activation_key = register_response.json()["activation_key"]

    login_response = client.post(
        "/api/auth/login",
        json={"email": "user@example.com", "password": "password123"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return activation_key, token


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_register_login_refresh_key_and_change_password(client):
    _, token = create_user_and_login(client)

    profile_response = client.get("/api/profile", headers=auth_headers(token))
    assert profile_response.status_code == 200
    old_key = profile_response.json()["activation_key"]

    refresh_response = client.post("/api/profile/refresh-key", headers=auth_headers(token))
    assert refresh_response.status_code == 200
    assert refresh_response.json()["activation_key"] != old_key

    change_password_response = client.post(
        "/api/profile/change-password",
        headers=auth_headers(token),
        json={
            "current_password": "password123",
            "new_password": "newpassword123",
            "new_password_confirmation": "newpassword123",
        },
    )
    assert change_password_response.status_code == 204

    login_response = client.post(
        "/api/auth/login",
        json={"email": "user@example.com", "password": "newpassword123"},
    )
    assert login_response.status_code == 200


def test_activate_key_allocates_vm_and_consumes_key(client):
    activation_key, token = create_user_and_login(client)

    create_vm_response = client.post(
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
    assert create_vm_response.status_code == 201

    activation_response = client.post("/api/proxy/activate-key", json={"activation_key": activation_key})
    assert activation_response.status_code == 200
    body = activation_response.json()
    assert body["status"] == "connected"
    assert body["vm"]["name"] == "proxy-1"
    assert body["ws_token"]

    profile_response = client.get("/api/profile", headers=auth_headers(token))
    assert profile_response.status_code == 200
    assert profile_response.json()["activation_key"] is None


def test_activate_key_returns_503_when_no_free_vm(client):
    activation_key, _ = create_user_and_login(client)

    activation_response = client.post("/api/proxy/activate-key", json={"activation_key": activation_key})
    assert activation_response.status_code == 503
    assert activation_response.json()["detail"] == "Все прокси-серверы заняты"
