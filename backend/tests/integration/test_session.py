"""Testes de integracao da gestao de sessoes (F3)."""


def _auth_headers(client, username: str) -> dict[str, str]:
    creds = {"username": username, "password": "senha-forte-1"}
    client.post("/auth/register", json=creds)
    token = client.post("/auth/login", json=creds).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_request_session_creates_pending(client):
    alice = _auth_headers(client, "alicereq")
    _auth_headers(client, "bobreq")
    response = client.post(
        "/sessions/request",
        json={"bob_username": "bobreq", "mode": "RSA"},
        headers=alice,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["state"] == "pending"
    assert body["mode"] == "RSA"


def test_request_session_unknown_user(client):
    alice = _auth_headers(client, "aliceunk")
    response = client.post(
        "/sessions/request",
        json={"bob_username": "naoexiste", "mode": "RSA"},
        headers=alice,
    )
    assert response.status_code == 404


def test_accept_session_establishes_rsa_key(client):
    alice = _auth_headers(client, "aliceacc")
    bob = _auth_headers(client, "bobacc")
    session_id = client.post(
        "/sessions/request",
        json={"bob_username": "bobacc", "mode": "RSA"},
        headers=alice,
    ).json()["id"]

    accept = client.post(f"/sessions/{session_id}/accept", headers=bob)
    assert accept.status_code == 200
    assert accept.json()["state"] == "active"


def test_reject_session(client):
    alice = _auth_headers(client, "alicerej")
    bob = _auth_headers(client, "bobrej")
    session_id = client.post(
        "/sessions/request",
        json={"bob_username": "bobrej", "mode": "RSA"},
        headers=alice,
    ).json()["id"]

    reject = client.post(f"/sessions/{session_id}/reject", headers=bob)
    assert reject.status_code == 200
    assert reject.json()["state"] == "rejected"


def test_alice_cannot_accept_own_session(client):
    alice = _auth_headers(client, "aliceown")
    _auth_headers(client, "bobown")
    session_id = client.post(
        "/sessions/request",
        json={"bob_username": "bobown", "mode": "RSA"},
        headers=alice,
    ).json()["id"]

    response = client.post(f"/sessions/{session_id}/accept", headers=alice)
    assert response.status_code == 400


def test_close_session(client):
    alice = _auth_headers(client, "aliceclose")
    bob = _auth_headers(client, "bobclose")
    session_id = client.post(
        "/sessions/request",
        json={"bob_username": "bobclose", "mode": "RSA"},
        headers=alice,
    ).json()["id"]
    client.post(f"/sessions/{session_id}/accept", headers=bob)

    close = client.request("DELETE", f"/sessions/{session_id}", headers=alice)
    assert close.status_code == 200
    assert close.json()["state"] == "closed"


def test_get_session_key_after_establishment(client):
    alice = _auth_headers(client, "alicekey")
    bob = _auth_headers(client, "bobkey")
    session_id = client.post(
        "/sessions/request",
        json={"bob_username": "bobkey", "mode": "RSA"},
        headers=alice,
    ).json()["id"]
    client.post(f"/sessions/{session_id}/accept", headers=bob)

    response = client.get(f"/sessions/{session_id}/key", headers=alice)
    assert response.status_code == 200
    assert len(response.json()["key"]) > 0


def test_get_session_key_before_establishment_conflicts(client):
    alice = _auth_headers(client, "alicependkey")
    _auth_headers(client, "bobpendkey")
    session_id = client.post(
        "/sessions/request",
        json={"bob_username": "bobpendkey", "mode": "RSA"},
        headers=alice,
    ).json()["id"]

    response = client.get(f"/sessions/{session_id}/key", headers=alice)
    assert response.status_code == 409
