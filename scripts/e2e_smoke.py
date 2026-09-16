#!/usr/bin/env python3
"""Verificacao ponta a ponta do QChat: HTTP, WebSocket e cifragem de mensagens.

Cria dois usuarios, conecta ambos por WebSocket e, para cada um dos quatro modos
de estabelecimento de chave, executa o fluxo completo: pedido de sessao, aceite,
recuperacao da chave pelos dois lados, troca de mensagens cifradas com
AES-256-GCM e encerramento. A cifragem espelha o MessageCryptoService do
frontend (nonce de 96 bits, tag de 128 bits, AAD session_id|sequencia|timestamp),
entao uma mensagem que passa aqui e' exatamente a que o navegador produziria.

Uso:
    QCHAT_API=http://localhost:8000 python scripts/e2e_smoke.py
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import secrets
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone

import websockets
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

API = os.environ.get("QCHAT_API", "http://localhost:8000").rstrip("/")
WS_BASE = API.replace("https://", "wss://").replace("http://", "ws://")
PASSWORD = "Senha!Forte123"
MODES = ("RSA", "MLKEM", "BB84", "HYBRID")
TIMEOUT = 180

_OK = "\033[32mOK\033[0m"
_FAIL = "\033[31mFALHOU\033[0m"
_failures: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> bool:
    print(f"  [{_OK if condition else _FAIL}] {label}{(' — ' + detail) if detail else ''}")
    if not condition:
        _failures.append(label)
    return condition


def http(method: str, path: str, body=None, token: str | None = None):
    req = urllib.request.Request(
        API + path,
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
    )
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            raw = resp.read()
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode()[:300]


def b64(data: bytes) -> str:
    return base64.b64encode(data).decode()


def unb64(value: str) -> bytes:
    return base64.b64decode(value)


def encrypt(key: bytes, plaintext: str, session_id: str, seq: int) -> dict:
    """Espelha MessageCryptoService.encrypt do frontend."""
    timestamp = datetime.now(timezone.utc).isoformat()
    nonce = secrets.token_bytes(12)
    aad = f"{session_id}|{seq}|{timestamp}".encode()
    out = AESGCM(key).encrypt(nonce, plaintext.encode(), aad)
    return {
        "nonce": b64(nonce),
        "ciphertext": b64(out[:-16]),
        "tag": b64(out[-16:]),
        "sequence_number": seq,
        "timestamp": timestamp,
    }


def decrypt(key: bytes, env: dict, session_id: str) -> str:
    aad = f"{session_id}|{env['sequence_number']}|{env['timestamp']}".encode()
    payload = unb64(env["ciphertext"]) + unb64(env["tag"])
    return AESGCM(key).decrypt(unb64(env["nonce"]), payload, aad).decode()


class Peer:
    """Cliente WebSocket de um usuario, com fila de mensagens recebidas."""

    def __init__(self, username: str) -> None:
        self.username = username
        self.token: str = ""
        self.ws = None
        self._queue: asyncio.Queue = asyncio.Queue()
        self._reader: asyncio.Task | None = None
        self.pings = 0

    def authenticate(self) -> None:
        http("POST", "/auth/register", {"username": self.username, "password": PASSWORD})
        status, body = http(
            "POST", "/auth/login", {"username": self.username, "password": PASSWORD}
        )
        if status != 200:
            raise SystemExit(f"login de {self.username} falhou: {status} {body}")
        self.token = body["access_token"]

    async def connect(self) -> None:
        self.ws = await websockets.connect(f"{WS_BASE}/ws/{self.token}", open_timeout=30)
        self._reader = asyncio.create_task(self._read_loop())

    async def _read_loop(self) -> None:
        try:
            async for raw in self.ws:
                message = json.loads(raw)
                if message.get("type") == "ping":
                    self.pings += 1
                    await self.send({"type": "pong", "payload": {}})
                    continue
                await self._queue.put(message)
        except websockets.exceptions.ConnectionClosed:
            pass

    async def send(self, message: dict) -> None:
        await self.ws.send(json.dumps(message))

    async def expect(self, msg_type: str, timeout: float = TIMEOUT) -> dict | None:
        """Aguarda uma mensagem do tipo pedido, descartando as demais."""
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None
            try:
                message = await asyncio.wait_for(self._queue.get(), timeout=remaining)
            except asyncio.TimeoutError:
                return None
            if message.get("type") == msg_type:
                return message

    async def close(self) -> None:
        if self._reader:
            self._reader.cancel()
        if self.ws:
            await self.ws.close()


async def run_mode(mode: str, alice: Peer, bob: Peer) -> None:
    print(f"\n--- modo {mode} ---")
    started = time.monotonic()

    status, body = http(
        "POST", "/sessions/request", {"bob_username": bob.username, "mode": mode}, alice.token
    )
    if not check("alice cria a sessao", status == 201, f"HTTP {status}"):
        return
    session_id = body.get("id") or body.get("session_id")

    check("bob recebe session_request no WS", await bob.expect("session_request") is not None)

    status, _ = http("POST", f"/sessions/{session_id}/accept", None, bob.token)
    check("bob aceita a sessao", status == 200, f"HTTP {status}")
    check("alice recebe session_accepted no WS", await alice.expect("session_accepted") is not None)

    status_a, key_a = http("GET", f"/sessions/{session_id}/key", None, alice.token)
    status_b, key_b = http("GET", f"/sessions/{session_id}/key", None, bob.token)
    if not check("ambos recuperam a chave", status_a == 200 and status_b == 200):
        return

    raw_key = unb64(key_a["key"])
    elapsed = time.monotonic() - started
    check("chave de 256 bits", len(raw_key) == 32, f"{len(raw_key) * 8} bits")
    check("alice e bob derivam a mesma chave", key_a["key"] == key_b["key"])
    qber = key_a.get("qber")
    if qber is not None:
        check("QBER abaixo do limiar", qber < 0.15, f"QBER = {qber:.4f}")

    # alice -> bob
    text_ab = f"mensagem {mode} de ida {uuid.uuid4().hex[:8]}"
    await alice.send(
        {
            "type": "chat_message",
            "session_id": session_id,
            "payload": encrypt(raw_key, text_ab, session_id, 1),
        }
    )
    received = await bob.expect("chat_message")
    if check("bob recebe a mensagem cifrada", received is not None):
        check(
            "bob decifra o texto original",
            decrypt(raw_key, received["payload"], session_id) == text_ab,
        )

    # bob -> alice
    text_ba = f"resposta {mode} {uuid.uuid4().hex[:8]}"
    await bob.send(
        {
            "type": "chat_message",
            "session_id": session_id,
            "payload": encrypt(raw_key, text_ba, session_id, 2),
        }
    )
    received = await alice.expect("chat_message")
    if check("alice recebe a resposta", received is not None):
        check(
            "alice decifra o texto original",
            decrypt(raw_key, received["payload"], session_id) == text_ba,
        )

    await alice.send({"type": "typing", "session_id": session_id, "payload": {}})
    check("indicador de digitacao chega em bob", await bob.expect("typing", 15) is not None)

    status, _ = http("DELETE", f"/sessions/{session_id}", None, alice.token)
    check("sessao encerrada", status in (200, 204), f"HTTP {status}")
    check("bob recebe session_closed", await bob.expect("session_closed", 15) is not None)
    print(f"  tempo total do modo: {elapsed:.2f}s")


async def run_tamper_test(alice: Peer, bob: Peer) -> None:
    """Uma mensagem adulterada deve falhar na verificacao da tag GCM."""
    print("\n--- integridade (AES-GCM) ---")
    status, body = http(
        "POST", "/sessions/request", {"bob_username": bob.username, "mode": "RSA"}, alice.token
    )
    session_id = body.get("id") or body.get("session_id")
    await bob.expect("session_request")
    http("POST", f"/sessions/{session_id}/accept", None, bob.token)
    await alice.expect("session_accepted")
    _, key = http("GET", f"/sessions/{session_id}/key", None, alice.token)
    raw_key = unb64(key["key"])

    envelope = encrypt(raw_key, "texto integro", session_id, 1)
    corrupted = bytearray(unb64(envelope["ciphertext"]))
    corrupted[0] ^= 0x01
    envelope["ciphertext"] = b64(bytes(corrupted))
    try:
        decrypt(raw_key, envelope, session_id)
        check("ciphertext adulterado e' rejeitado", False, "decifrou indevidamente")
    except InvalidTag:
        check("ciphertext adulterado e' rejeitado", True, "InvalidTag, como esperado")

    http("DELETE", f"/sessions/{session_id}", None, alice.token)


async def main() -> int:
    print(f"QChat — verificacao ponta a ponta contra {API}\n")

    print("--- infraestrutura ---")
    status, body = http("GET", "/health")
    check("backend responde /health", status == 200, json.dumps(body) if body else "")

    tag = uuid.uuid4().hex[:6]
    alice, bob = Peer(f"alice{tag}"), Peer(f"bob{tag}")
    for peer in (alice, bob):
        peer.authenticate()
    check("dois usuarios registrados e autenticados", bool(alice.token and bob.token))

    await alice.connect()
    await bob.connect()
    check("ambos conectados por WebSocket", alice.ws.open and bob.ws.open)

    await asyncio.sleep(0.5)
    status, online = http("GET", "/users/online", None, alice.token)
    names = [u["username"] for u in online] if isinstance(online, list) else []
    check("bob aparece na lista de usuarios online", bob.username in names, ", ".join(names))

    await alice.send({"type": "ping", "payload": {}})
    check("servidor responde ao ping", await alice.expect("pong", 15) is not None)

    for mode in MODES:
        await run_mode(mode, alice, bob)

    await run_tamper_test(alice, bob)

    await alice.close()
    await bob.close()

    print("\n" + "=" * 60)
    if _failures:
        print(f"{len(_failures)} verificacao(oes) falharam:")
        for item in _failures:
            print(f"  - {item}")
        return 1
    print("Todas as verificacoes passaram.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
