"""Testes de integracao das rotas de autenticacao (F2)."""

CREDENTIALS = {"username": "alice123", "password": "senha-forte-1"}


def test_register_login_and_me(client):
    register = client.post("/auth/register", json=CREDENTIALS)
    assert register.status_code == 201
    assert register.json()["username"] == "alice123"

    login = client.post("/auth/login", json=CREDENTIALS)
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["username"] == "alice123"


def test_duplicate_username_rejected(client):
    client.post("/auth/register", json=CREDENTIALS)
    duplicate = client.post("/auth/register", json=CREDENTIALS)
    assert duplicate.status_code == 409


def test_invalid_username_rejected(client):
    response = client.post("/auth/register", json={"username": "a!", "password": "senha1234"})
    assert response.status_code == 422


def test_short_password_rejected(client):
    response = client.post("/auth/register", json={"username": "validuser", "password": "1234"})
    assert response.status_code == 422


def test_login_with_wrong_password(client):
    client.post("/auth/register", json=CREDENTIALS)
    response = client.post("/auth/login", json={"username": "alice123", "password": "senha-errada"})
    assert response.status_code == 401


def test_me_without_token_is_unauthorized(client):
    response = client.get("/auth/me")
    assert response.status_code in (401, 403)
