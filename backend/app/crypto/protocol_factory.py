"""Factory de protocolos de estabelecimento de chave (F5.2).

Os imports dos modulos concretos sao tardios (lazy): assim os modos RSA
funcionam sem que os extras `quantum` (qiskit-aer, liboqs) estejam instalados.
"""

from app.crypto.key_protocol import KeyEstablishmentProtocol, ProtocolMode


class ProtocolFactory:
    @staticmethod
    def create(mode: ProtocolMode) -> KeyEstablishmentProtocol:
        if mode == ProtocolMode.RSA:
            from app.crypto.rsa.protocol import RSAProtocol

            return RSAProtocol()
        if mode == ProtocolMode.MLKEM:
            from app.crypto.mlkem.protocol import MLKEMProtocol

            return MLKEMProtocol()
        if mode == ProtocolMode.BB84:
            from app.crypto.bb84.protocol import BB84Protocol

            return BB84Protocol()
        if mode == ProtocolMode.HYBRID:
            from app.crypto.hybrid.protocol import HybridProtocol

            return HybridProtocol()
        raise ValueError(f"Modo de protocolo desconhecido: {mode}")
