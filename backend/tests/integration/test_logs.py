"""Teste de integracao do endpoint de exportacao de logs (F13.5)."""


def _auth_headers(client, username: str) -> dict[str, str]:
    creds = {"username": username, "password": "senha-forte-1"}
    client.post("/auth/register", json=creds)
    token = client.post("/auth/login", json=creds).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_export_logs_requires_auth(client):
    response = client.get("/logs/export", params={"session_id": "x"})
    assert response.status_code in (401, 403)


def test_export_logs_returns_csv(client):
    headers = _auth_headers(client, "logsuser")
    response = client.get("/logs/export", params={"session_id": "any"}, headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
