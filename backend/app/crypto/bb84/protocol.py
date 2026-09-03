"""Pipeline BB84 completo (F6).

Etapas: geracao de bits/bases -> codificacao e transmissao dos qubits (Qiskit
Aer) -> medicao por Bob -> sifting -> estimativa de QBER -> reconciliacao Cascade
-> amplificacao de privacidade -> chave AES-256.

Como o canal quantico e simulado no servidor, ``BB84Protocol.initiate()`` executa
o pipeline inteiro; ``respond()`` apenas recebe a chave ja destilada.
"""

from __future__ import annotations

import base64
import hashlib
import secrets
import time
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any

from app.core.config import get_settings
from app.core.event_logging import log_eve_activity
from app.crypto.bb84.cascade import reconcile
from app.crypto.bb84.privacy_amp import privacy_amplify
from app.crypto.bb84.qber import estimate_qber
from app.crypto.bb84.sifting import sift
from app.crypto.eve_simulator import EveMode, EveSimulator, configured_eve
from app.crypto.key_protocol import (
    SESSION_KEY_BYTES,
    KeyEstablishmentProtocol,
    ProtocolMetrics,
    ProtocolMode,
)

if TYPE_CHECKING:
    from qiskit import QuantumCircuit


class QBERThresholdExceeded(Exception):
    """QBER acima do limiar — possivel espionagem; sessao abortada (F6.7)."""

    def __init__(self, qber: float, threshold: float) -> None:
        self.qber = qber
        self.threshold = threshold
        super().__init__(f"QBER {qber:.4f} acima do limiar {threshold:.4f} — possivel espionagem")


class InsufficientKeyMaterial(Exception):
    """Chave destilada com menos de 256 bits apos a amplificacao de privacidade."""


@dataclass
class BB84Result:
    qber: float
    n_qubits: int
    sifted_length: int
    reconciled_length: int
    amplified_length: int
    parity_bits_leaked: int


def _build_circuit(alice_bit: int, alice_basis: int, bob_basis: int, eve: EveSimulator):
    """Monta o circuito de um qubit: preparo (Alice) -> Eve -> medicao (Bob)."""
    from qiskit import QuantumCircuit

    clbits = 2 if eve.uses_eve_register else 1
    circuit = QuantumCircuit(1, clbits)

    # Alice prepara: bit na base Z (|0>,|1>) ou X (|+>,|->).
    if alice_bit == 1:
        circuit.x(0)
    if alice_basis == 1:
        circuit.h(0)

    # Eve intercepta o qubit em transito (clbit 1 reservado para a medicao dela).
    eve.intercept(circuit, qubit=0, eve_clbit=clbits - 1)

    # Bob mede na sua base aleatoria.
    if bob_basis == 1:
        circuit.h(0)
    circuit.measure(0, 0)
    return circuit


def _transmit_and_measure(
    alice_bits: list[int],
    alice_bases: list[int],
    bob_bases: list[int],
    eve: EveSimulator,
) -> list[int]:
    """Codifica, transmite e mede os qubits via Qiskit Aer (shots=1)."""
    from qiskit_aer import AerSimulator

    circuits: list[QuantumCircuit] = [
        _build_circuit(alice_bits[i], alice_bases[i], bob_bases[i], eve)
        for i in range(len(alice_bits))
    ]
    result = AerSimulator().run(circuits, shots=1).result()
    # clbit 0 e o bit de Bob; e o caractere mais a direita da string de contagem.
    return [int(next(iter(result.get_counts(i)))[-1]) for i in range(len(circuits))]


def _bits_to_bytes(bits: list[int]) -> bytes:
    out = bytearray()
    for start in range(0, len(bits), 8):
        byte = 0
        for bit in bits[start : start + 8]:
            byte = (byte << 1) | (bit & 1)
        out.append(byte)
    return bytes(out)


def run_bb84(
    *,
    n_qubits: int,
    qber_threshold: float,
    eve: EveSimulator | None = None,
    cascade_passes: int = 4,
    sample_fraction: float = 0.25,
) -> tuple[bytes, BB84Result]:
    """Executa o pipeline BB84 completo e retorna ``(chave_256_bits, metricas)``."""
    eve = eve or EveSimulator(EveMode.PASSIVE)
    rng = secrets.SystemRandom()

    alice_bits = [secrets.randbits(1) for _ in range(n_qubits)]
    alice_bases = [secrets.randbits(1) for _ in range(n_qubits)]
    bob_bases = [secrets.randbits(1) for _ in range(n_qubits)]

    bob_bits = _transmit_and_measure(alice_bits, alice_bases, bob_bases, eve)

    sifted_alice, sifted_bob = sift(alice_bases, bob_bases, alice_bits, bob_bits)
    qber, reconciled_alice, reconciled_bob = estimate_qber(
        sifted_alice, sifted_bob, sample_fraction, rng
    )

    if qber > qber_threshold:
        raise QBERThresholdExceeded(qber, qber_threshold)

    corrected, leaked = reconcile(
        reconciled_alice, reconciled_bob, qber=qber, passes=cascade_passes, rng=rng
    )
    amplified = privacy_amplify(corrected, qber, rng)

    required_bits = SESSION_KEY_BYTES * 8
    if len(amplified) < required_bits:
        raise InsufficientKeyMaterial(
            f"Chave destilada com {len(amplified)} bits; necessario {required_bits}"
        )

    key = hashlib.sha256(_bits_to_bytes(amplified)).digest()
    result = BB84Result(
        qber=qber,
        n_qubits=n_qubits,
        sifted_length=len(sifted_alice),
        reconciled_length=len(reconciled_alice),
        amplified_length=len(amplified),
        parity_bits_leaked=leaked,
    )
    return key, result


class BB84Protocol(KeyEstablishmentProtocol):
    mode = ProtocolMode.BB84

    def __init__(
        self,
        *,
        n_qubits: int | None = None,
        qber_threshold: float | None = None,
        cascade_passes: int | None = None,
        eve: EveSimulator | None = None,
    ) -> None:
        settings = get_settings()
        self._n_qubits = n_qubits if n_qubits is not None else settings.bb84_qubits
        self._qber_threshold = (
            qber_threshold if qber_threshold is not None else settings.qber_threshold
        )
        self._cascade_passes = (
            cascade_passes if cascade_passes is not None else settings.cascade_passes
        )
        # Sem eve explicita, usa a configurada pelo ambiente (PASSIVE em producao).
        self._eve = eve if eve is not None else configured_eve()
        self._key: bytes | None = None
        self._result: BB84Result | None = None
        self._elapsed_ms = 0.0

    def initiate(self) -> dict[str, Any]:
        start = time.perf_counter()
        try:
            self._key, self._result = run_bb84(
                n_qubits=self._n_qubits,
                qber_threshold=self._qber_threshold,
                eve=self._eve,
                cascade_passes=self._cascade_passes,
            )
        except QBERThresholdExceeded as exc:
            log_eve_activity(
                mode=self._eve.mode.value,
                intercepted=self._eve.intercepted_count,
                qber=exc.qber,
                aborted=True,
                n_qubits=self._n_qubits,
            )
            raise
        self._elapsed_ms = (time.perf_counter() - start) * 1000
        log_eve_activity(
            mode=self._eve.mode.value,
            intercepted=self._eve.intercepted_count,
            qber=self._result.qber,
            aborted=False,
            n_qubits=self._n_qubits,
        )
        return {
            "key": base64.b64encode(self._key).decode("ascii"),
            "result": asdict(self._result),
        }

    def respond(self, initiation_data: dict[str, Any]) -> dict[str, Any]:
        self._key = base64.b64decode(initiation_data["key"])
        self._result = BB84Result(**initiation_data["result"])
        return {}

    def get_key(self) -> bytes:
        if self._key is None:
            raise RuntimeError("Chave de sessao ainda nao estabelecida")
        return self._key

    def get_metrics(self) -> ProtocolMetrics:
        if self._result is None:
            raise RuntimeError("Protocolo BB84 ainda nao executado")
        return ProtocolMetrics(
            mode=self.mode,
            elapsed_ms=self._elapsed_ms,
            qber=self._result.qber,
            bytes_exchanged=(2 * self._result.n_qubits + self._result.parity_bits_leaked) // 8,
            key_size_bits=len(self._key) * 8 if self._key else 0,
            extra={
                "n_qubits": self._result.n_qubits,
                "sifted_length": self._result.sifted_length,
                "reconciled_length": self._result.reconciled_length,
                "amplified_length": self._result.amplified_length,
                "parity_bits_leaked": self._result.parity_bits_leaked,
            },
        )
