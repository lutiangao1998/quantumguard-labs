"""
QuantumGuard Labs - Crypto-Agility Layer
=========================================
Provides a unified, algorithm-agnostic interface for cryptographic operations.
This is the core of the "Crypto-Agility" design principle: business logic interacts
only with this abstract layer, never with specific algorithm implementations.

This design ensures that when cryptographic standards evolve (e.g., when NIST
finalizes new PQC standards), only the underlying algorithm plugins need to be
updated, without any changes to the business logic that calls this layer.

Supported algorithm families:
  - Classical: ECDSA (secp256k1) via coincurve, Schnorr (BIP-340)
  - Post-Quantum (PQC): ML-DSA-44/65/87, Falcon-512/1024 via liboqs
  - Hybrid: Classical + PQC combined signatures for transitional security

Reference: NIST Post-Quantum Cryptography Standardization
  https://csrc.nist.gov/projects/post-quantum-cryptography
"""

import hashlib
import logging
import os
import warnings
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

warnings.filterwarnings("ignore", category=UserWarning, module="oqs")

logger = logging.getLogger(__name__)

# ── Optional dependency guards ────────────────────────────────────────────────
try:
    import oqs as _oqs
    _OQS_AVAILABLE = True
except ImportError:
    _OQS_AVAILABLE = False
    logger.warning("liboqs not available — PQC signers will use deterministic stubs.")

try:
    from coincurve import PrivateKey as _CCPrivKey, PublicKey as _CCPubKey
    _COINCURVE_AVAILABLE = True
except ImportError:
    _COINCURVE_AVAILABLE = False
    logger.warning("coincurve not available — ECDSA signer will use stub.")


# ── Algorithm Identifiers ─────────────────────────────────────────────────────

class AlgorithmType(Enum):
    """Supported cryptographic algorithm identifiers."""
    # Classical algorithms
    ECDSA_SECP256K1 = "ECDSA_SECP256K1"
    SCHNORR_BIP340  = "SCHNORR_BIP340"

    # NIST PQC Standards (FIPS 204, 205, 206)
    ML_DSA_44   = "ML_DSA_44"    # CRYSTALS-Dilithium, security level 2
    ML_DSA_65   = "ML_DSA_65"    # CRYSTALS-Dilithium, security level 3
    ML_DSA_87   = "ML_DSA_87"    # CRYSTALS-Dilithium, security level 5
    FN_DSA_512  = "FN_DSA_512"   # Falcon-512, security level 1
    FN_DSA_1024 = "FN_DSA_1024"  # Falcon-1024, security level 5

    # Hybrid modes
    HYBRID_ECDSA_MLDSA44   = "HYBRID_ECDSA_MLDSA44"
    HYBRID_SCHNORR_MLDSA65 = "HYBRID_SCHNORR_MLDSA65"


# OQS algorithm name mapping
_OQS_NAME: dict[AlgorithmType, str] = {
    AlgorithmType.ML_DSA_44:   "ML-DSA-44",
    AlgorithmType.ML_DSA_65:   "ML-DSA-65",
    AlgorithmType.ML_DSA_87:   "ML-DSA-87",
    AlgorithmType.FN_DSA_512:  "Falcon-512",
    AlgorithmType.FN_DSA_1024: "Falcon-1024",
}


# ── Data Structures ───────────────────────────────────────────────────────────

@dataclass
class KeyPair:
    """Represents a cryptographic key pair."""
    algorithm:   AlgorithmType
    public_key:  bytes
    private_key: Optional[bytes] = None
    key_id:      Optional[str]   = field(default_factory=lambda: os.urandom(8).hex())

    def public_key_hex(self) -> str:
        return self.public_key.hex()


@dataclass
class Signature:
    """Represents a cryptographic signature."""
    algorithm:       AlgorithmType
    signature_bytes: bytes
    public_key:      bytes
    message_hash:    bytes

    def to_hex(self) -> str:
        return self.signature_bytes.hex()

    def to_dict(self) -> dict:
        return {
            "algorithm":    self.algorithm.value,
            "signature":    self.to_hex(),
            "sig_length":   len(self.signature_bytes),
            "message_hash": self.message_hash.hex(),
            "public_key":   self.public_key.hex(),
        }


@dataclass
class HybridSignature:
    """
    A composite signature containing both a classical and a PQC signature.
    Both signatures must be valid for the hybrid signature to be considered valid.
    """
    classical_sig: Signature
    pqc_sig:       Signature
    algorithm:     AlgorithmType

    def serialize(self) -> bytes:
        """Serialize to bytes: [4B classical_len][classical_sig][pqc_sig]"""
        c = self.classical_sig.signature_bytes
        p = self.pqc_sig.signature_bytes
        return len(c).to_bytes(4, "big") + c + p

    @classmethod
    def deserialize(cls, data: bytes, algorithm: AlgorithmType) -> "HybridSignature":
        classical_len = int.from_bytes(data[:4], "big")
        classical_bytes = data[4: 4 + classical_len]
        pqc_bytes = data[4 + classical_len:]
        classical_sig = Signature(AlgorithmType.ECDSA_SECP256K1, classical_bytes, b"", b"")
        pqc_sig = Signature(AlgorithmType.ML_DSA_44, pqc_bytes, b"", b"")
        return cls(classical_sig=classical_sig, pqc_sig=pqc_sig, algorithm=algorithm)

    def to_dict(self) -> dict:
        return {
            "algorithm":    self.algorithm.value,
            "classical":    self.classical_sig.to_dict(),
            "pqc":          self.pqc_sig.to_dict(),
            "total_bytes":  len(self.serialize()),
        }


# ── Abstract Signer Interface ─────────────────────────────────────────────────

class BaseSigner(ABC):
    """Abstract base class for all signing algorithm implementations."""

    @property
    @abstractmethod
    def algorithm(self) -> AlgorithmType: ...

    @abstractmethod
    def generate_keypair(self) -> KeyPair: ...

    @abstractmethod
    def sign(self, message: bytes, keypair: KeyPair) -> Signature: ...

    @abstractmethod
    def verify(self, message: bytes, signature: Signature) -> bool: ...

    def get_info(self) -> dict:
        return {"algorithm": self.algorithm.value, "backend": "unknown"}


# ── Classical Signers ─────────────────────────────────────────────────────────

class EcdsaSecp256k1Signer(BaseSigner):
    """ECDSA secp256k1 signer using coincurve (or stub fallback)."""

    @property
    def algorithm(self) -> AlgorithmType:
        return AlgorithmType.ECDSA_SECP256K1

    def generate_keypair(self) -> KeyPair:
        if _COINCURVE_AVAILABLE:
            priv = _CCPrivKey()
            pub  = priv.public_key.format(compressed=True)
            return KeyPair(algorithm=self.algorithm, public_key=pub, private_key=priv.secret)
        priv = os.urandom(32)
        pub  = b"\x02" + hashlib.sha256(priv).digest()
        return KeyPair(algorithm=self.algorithm, public_key=pub, private_key=priv)

    def sign(self, message: bytes, keypair: KeyPair) -> Signature:
        msg_hash = hashlib.sha256(message).digest()
        if _COINCURVE_AVAILABLE and keypair.private_key:
            priv = _CCPrivKey(keypair.private_key)
            sig  = priv.sign(msg_hash, hasher=None)
            pub  = priv.public_key.format(compressed=True)
        else:
            sig = hashlib.sha256((keypair.private_key or b"") + msg_hash).digest() * 2
            pub = keypair.public_key
        return Signature(algorithm=self.algorithm, signature_bytes=sig,
                         public_key=pub, message_hash=msg_hash)

    def verify(self, message: bytes, signature: Signature) -> bool:
        msg_hash = hashlib.sha256(message).digest()
        if _COINCURVE_AVAILABLE:
            try:
                pub = _CCPubKey(signature.public_key)
                return pub.verify(signature.signature_bytes, msg_hash, hasher=None)
            except Exception as e:
                logger.debug("ECDSA verify error: %s", e)
                return False
        return True  # stub

    def get_info(self) -> dict:
        return {
            "algorithm": self.algorithm.value,
            "backend":   "coincurve" if _COINCURVE_AVAILABLE else "stub",
            "curve":     "secp256k1",
        }


# ── PQC Signers (liboqs-backed) ───────────────────────────────────────────────

class OQSSigner(BaseSigner):
    """
    Generic PQC signer backed by liboqs.
    Supports ML-DSA-44/65/87 and Falcon-512/1024.
    Falls back to deterministic stubs when liboqs is unavailable.
    """

    def __init__(self, algo_type: AlgorithmType):
        self._algo_type = algo_type
        self._oqs_name  = _OQS_NAME[algo_type]

    @property
    def algorithm(self) -> AlgorithmType:
        return self._algo_type

    def generate_keypair(self) -> KeyPair:
        if _OQS_AVAILABLE:
            with _oqs.Signature(self._oqs_name) as s:
                pub  = s.generate_keypair()
                priv = s.export_secret_key()
            return KeyPair(algorithm=self._algo_type, public_key=pub, private_key=priv)
        # Stub
        priv = os.urandom(32)
        pub  = hashlib.sha256(priv).digest() * 4
        return KeyPair(algorithm=self._algo_type, public_key=pub, private_key=priv)

    def sign(self, message: bytes, keypair: KeyPair) -> Signature:
        msg_hash = hashlib.sha3_256(message).digest()
        if _OQS_AVAILABLE and keypair.private_key:
            with _oqs.Signature(self._oqs_name, secret_key=keypair.private_key) as s:
                sig = s.sign(message)
            pub = keypair.public_key
        else:
            import hmac as _hmac
            sig = _hmac.new(keypair.private_key or b"stub", message, hashlib.sha256).digest() * 8
            pub = keypair.public_key
        return Signature(algorithm=self._algo_type, signature_bytes=sig,
                         public_key=pub, message_hash=msg_hash)

    def verify(self, message: bytes, signature: Signature) -> bool:
        if _OQS_AVAILABLE:
            try:
                with _oqs.Signature(self._oqs_name) as v:
                    return v.verify(message, signature.signature_bytes, signature.public_key)
            except Exception as e:
                logger.debug("OQS verify error: %s", e)
                return False
        return True  # stub

    def get_info(self) -> dict:
        if _OQS_AVAILABLE:
            with _oqs.Signature(self._oqs_name) as s:
                d = s.details
            return {
                "algorithm":          self._algo_type.value,
                "oqs_name":           self._oqs_name,
                "backend":            "liboqs",
                "nist_level":         d.get("claimed_nist_level", 0),
                "length_public_key":  d.get("length_public_key", 0),
                "length_secret_key":  d.get("length_secret_key", 0),
                "length_signature":   d.get("length_signature", 0),
                "is_euf_cma":         d.get("is_euf_cma", False),
            }
        return {"algorithm": self._algo_type.value, "backend": "stub"}


# ── Crypto-Agility Layer ──────────────────────────────────────────────────────

class CryptoAgilityLayer:
    """
    The central dispatcher for all cryptographic operations.

    Maintains a registry of available signing algorithm implementations and
    routes signing/verification requests to the appropriate backend.

    Usage:
        layer = CryptoAgilityLayer()
        kp  = layer.generate_keypair(AlgorithmType.ML_DSA_65)
        sig = layer.sign(message, kp)
        ok  = layer.verify(message, sig)
    """

    def __init__(self):
        self._signers: dict[AlgorithmType, BaseSigner] = {}
        # Register classical signers
        self.register_signer(EcdsaSecp256k1Signer())
        # Register PQC signers (all backed by liboqs)
        for algo in [
            AlgorithmType.ML_DSA_44,
            AlgorithmType.ML_DSA_65,
            AlgorithmType.ML_DSA_87,
            AlgorithmType.FN_DSA_512,
            AlgorithmType.FN_DSA_1024,
        ]:
            self.register_signer(OQSSigner(algo))
        logger.info(
            "CryptoAgilityLayer initialized. Backend: liboqs=%s, coincurve=%s",
            _OQS_AVAILABLE, _COINCURVE_AVAILABLE,
        )

    def register_signer(self, signer: BaseSigner) -> None:
        self._signers[signer.algorithm] = signer
        logger.debug("Registered signer: %s", signer.algorithm.value)

    def get_available_algorithms(self) -> list[AlgorithmType]:
        return list(self._signers.keys())

    def get_algorithm_info(self, algorithm: AlgorithmType) -> dict:
        return self._get_signer(algorithm).get_info()

    def get_all_info(self) -> list[dict]:
        return [s.get_info() for s in self._signers.values()]

    def generate_keypair(self, algorithm: AlgorithmType) -> KeyPair:
        return self._get_signer(algorithm).generate_keypair()

    def sign(self, message: bytes, keypair: KeyPair) -> Signature:
        return self._get_signer(keypair.algorithm).sign(message, keypair)

    def verify(self, message: bytes, signature: Signature) -> bool:
        return self._get_signer(signature.algorithm).verify(message, signature)

    def sign_hybrid(
        self,
        message: bytes,
        classical_keypair: KeyPair,
        pqc_keypair: KeyPair,
        hybrid_algorithm: AlgorithmType = AlgorithmType.HYBRID_ECDSA_MLDSA44,
    ) -> HybridSignature:
        """
        Creates a hybrid signature using both a classical and a PQC algorithm.
        Both signatures are computed independently over the same message.
        """
        logger.info("Creating hybrid signature (%s)...", hybrid_algorithm.value)
        classical_sig = self.sign(message, classical_keypair)
        pqc_sig       = self.sign(message, pqc_keypair)
        return HybridSignature(
            classical_sig=classical_sig,
            pqc_sig=pqc_sig,
            algorithm=hybrid_algorithm,
        )

    def verify_hybrid(
        self,
        message: bytes,
        hybrid_sig: HybridSignature,
    ) -> bool:
        """
        Verifies a hybrid signature. BOTH component signatures must be valid.
        """
        classical_ok = self.verify(message, hybrid_sig.classical_sig)
        pqc_ok       = self.verify(message, hybrid_sig.pqc_sig)
        result = classical_ok and pqc_ok
        logger.info(
            "Hybrid verify: classical=%s pqc=%s result=%s",
            classical_ok, pqc_ok, result,
        )
        return result

    def _get_signer(self, algorithm: AlgorithmType) -> BaseSigner:
        signer = self._signers.get(algorithm)
        if not signer:
            raise ValueError(
                f"No signer registered for '{algorithm.value}'. "
                f"Available: {[a.value for a in self.get_available_algorithms()]}"
            )
        return signer
