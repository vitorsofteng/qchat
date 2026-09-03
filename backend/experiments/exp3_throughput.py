"""Experimento 3 — throughput de mensagens cifradas (F17.3).

Com a chave ja estabelecida, mede a latencia de cifrar+decifrar mensagens de
tamanhos variados (ciclo AES-256-GCM).
Saida: results/exp3_throughput.csv com colunas msg_size, latency_ms, throughput_msgs_s.

Execucao: python -m experiments.exp3_throughput [--messages N]
"""

from __future__ import annotations

import argparse
import secrets
import time
from datetime import UTC, datetime

from app.crypto.message_cipher import MessageCipher
from experiments.common import write_csv

# (rotulo, tamanho em bytes)
_SIZES = [("100B", 100), ("1KB", 1024), ("10KB", 10240)]


def main() -> None:
    parser = argparse.ArgumentParser(description="Experimento 3 — throughput")
    parser.add_argument("--messages", type=int, default=1000, help="mensagens por tamanho")
    message_count = parser.parse_args().messages

    key = secrets.token_bytes(32)
    timestamp = datetime.now(UTC).isoformat()
    rows: list[dict] = []

    for label, size in _SIZES:
        plaintext = "x" * size
        sender = MessageCipher(key, "exp3")
        receiver = MessageCipher(key, "exp3")

        latencies_ms: list[float] = []
        batch_start = time.perf_counter()
        for _ in range(message_count):
            start = time.perf_counter()
            envelope = sender.encrypt(plaintext, timestamp)
            receiver.decrypt(envelope)
            latencies_ms.append((time.perf_counter() - start) * 1000)
        total_seconds = time.perf_counter() - batch_start

        throughput = message_count / total_seconds if total_seconds > 0 else 0.0
        for latency in latencies_ms:
            rows.append(
                {
                    "msg_size": label,
                    "latency_ms": round(latency, 5),
                    "throughput_msgs_s": round(throughput, 1),
                }
            )
        print(f"{label}: {message_count} mensagens, {throughput:.0f} msgs/s")

    path = write_csv("exp3_throughput.csv", ["msg_size", "latency_ms", "throughput_msgs_s"], rows)
    print(f"Resultados salvos em {path}")


if __name__ == "__main__":
    main()
