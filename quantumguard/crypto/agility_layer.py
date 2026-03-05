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
  - Classical: ECDSA (secp256k1), Schnorr (BIP-340)
  - Post-Quantum (PQC): CRYSTALS-Dilithium (ML-DSA), FALCON, SPHINCS+
  - Hybrid: Classical + PQC combined signatures for transitional security

Reference: NIST Post-Quantum Cryptography Standardization
  https://csrc.nist.gov/projects/post-quantum-cryptography
"""

import hashlib
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class AlgorithmType(Enum):
    """
    Supported cryptographic algorithm identifiers.
    """
    # Classical algorithms
    ECDSA_SECP256K1 = "ECDSA_SECP256K1"
    SCHNORR_BIP340 = "SCHNORR_BIP340"

    # NIST PQC Standards (FIPS 204, 205, 206)
    ML_DSA_44 = "ML_DSA_44"       # CRYSTALS-Dilithium (NIST FIPS 204), security level 2
    ML_DSA_65 = "ML_DSA_65"       # CRYSTALS-Dilithium, security level 3
    ML_DSA_87 = "ML_DSA_87"       # CRYSTALS-Dilithium, security level 5
    SLH_DSA_128S = "SLH_DSA_128S" # SPHINCS+ (NIST FIPS 205), small variant
    FN_DSA_512 = "FN_DSA_512"     # FALCON-512 (NIST FIPS 206)

    # Hybrid modes
    HYBRID_ECDSA_MLDSA44 = "HYBRID_ECDSA_MLDSA44"
    HYBRID_SCHNORR_MLDSA65 = "HYBRID_SCHNORR_MLDSA65"


@dataclass
class KeyPair:
    """
    Represents a cryptographic key pair.

    Attributes:
        algorithm:      The algorithm this key pair is associated with.
        public_key:     The public key as bytes.
        private_key:    The private key as bytes (handle with extreme care).
        key_id:         An optional identifier for key management systems.
    """
    algorithm: AlgorithmType
    public_key: bytes
    private_key: Optional[bytes] = None
    key_id: Optional[str] = None

    def public_key_hex(self) -> str:
        """Returns the public key as a hexadecimal string."""
        return self.public_key.hex()


@dataclass
class Signature:
    """
    Represents a cryptographic signature.

    Attributes:
        algorithm:      The algorithm used to produce this signature.
        signature_bytes: The raw signature bytes.
        public_key:     The public key corresponding to the signing key.
        message_hash:   The hash of the message that was signed.
    """
    algorithm: AlgorithmType
    signature_bytes: bytes
    public_key: bytes
    message_hash: bytes

    def to_hex(self) -> str:
        """Returns the signature as a hexadecimal string."""
        return self.signature_bytes.hex()


@dataclass
class HybridSignature:
    """
    A composite signature containing both a classical and a PQC signature.
    Both signatures must be valid for the hybrid signature to be considered valid.
    This provides security against both classical and quantum adversaries.

    Attributes:
        classical_sig:  The classical (e.g., ECDSA) signature component.
        pqc_sig:        The post-quantum (e.g., ML-DSA) signature component.
        algorithm:      The hybrid algorithm identifier.
    """
    classical_sig: Signature
    pqc_sig: Signature
    algorithm: AlgorithmType

    def serialize(self) -> bytes:
        """
        Serializes the hybrid signature to bytes for transmission.
        Format: [4-byte classical sig length][classical sig][pqc sig]
        """
        classical_bytes = self.classical_sig.signature_bytes
        pqc_bytes = self.pqc_sig.signature_bytes
        length_prefix = len(classical_bytes).to_bytes(4, "big")
        return length_prefix + classical_bytes + pqc_bytes

    @classmethod
    def deserialize(cls, data: bytes, algorithm: AlgorithmType) -> "HybridSignature":
        """Deserializes a hybrid signature from bytes."""
        classical_len = int.from_bytes(data[:4], "big")
        classical_bytes = data[4 : 4 + classical_len]
        pqc_bytes = data[4 + classical_len :]
        # Note: In a real implementation, public keys would also be included.
        classical_sig = Signature(AlgorithmType.ECDSA_SECP256K1, classical_bytes, b"", b"")
        pqc_sig = Signature(AlgorithmType.ML_DSA_44, pqc_bytes, b"", b"")
        return cls(classical_sig=classical_sig, pqc_sig=pqc_sig, algorithm=algorithm)


# --- Abstract Signer Interface ---

class BaseSigner(ABC):
    """
    Abstract base class for all signing algorithm implementations.
    All concrete signers MUST implement this interface to be compatible
    with the Crypto-Agility Layer.
    """

    @property
    @abstractmethod
    def algorithm(self) -> AlgorithmType:
        """Returns the algorithm type this signer implements."""
        ...

    @abstractmethod
    def generate_keypair(self) -> KeyPair:
        """Generates a new key pair for this algorithm."""
        ...

    @abstractmethod
    def sign(self, message: bytes, private_key: bytes) -> Signature:
        """
        Signs a message with the given private key.

        Args:
            message:     The raw message bytes to sign.
            private_key: The private key bytes.

        Returns:
            A Signature object.
        """
        ...

    @abstractmethod
    def verify(self, message: bytes, signature: Signature, public_key: bytes) -> bool:
        """
        Verifies a signature against a message and public key.

        Args:
            message:    The raw message bytes.
            signature:  The Signature object to verify.
            public_key: The public key bytes.

        Returns:
            True if the signature is valid, False otherwise.
        """
        ...


# --- Stub Implementations (for prototype/testing) ---

class EcdsaSecp256k1Signer(BaseSigner):
    """
    Stub implementation of ECDSA secp256k1 signing.
    In production, this would use a library like 'cryptography' or 'python-bitcoinlib'.
    """

    @property
    def algorithm(self) -> AlgorithmType:
        return AlgorithmType.ECDSA_SECP256K1

    def generate_keypair(self) -> KeyPair:
        # Stub: generate random bytes to simulate key generation
        private_key = os.urandom(32)
        # In production: derive public key from private key using secp256k1
        public_key = hashlib.sha256(private_key).digest()  # Placeholder
        logger.debug("Generated ECDSA secp256k1 key pair (stub).")
        return KeyPair(
            algorithm=self.algorithm,
            public_key=public_key,
            private_key=private_key,
        )

    def sign(self, message: bytes, private_key: bytes) -> Signature:
        message_hash = hashlib.sha256(message).digest()
        # Stub: simulate a signature
        sig_bytes = hashlib.sha256(private_key + message_hash).digest()
        public_key = hashlib.sha256(private_key).digest()  # Placeholder
        logger.debug("Signed message with ECDSA secp256k1 (stub).")
        return Signature(
            algorithm=self.algorithm,
            signature_bytes=sig_bytes,
            public_key=public_key,
            message_hash=message_hash,
        )

    def verify(self, message: bytes, signature: Signature, public_key: bytes) -> bool:
        # Stub: always returns True for simulation purposes
        logger.debug("Verified ECDSA signature (stub - always True).")
        return True


class MlDsa44Signer(BaseSigner):
    """
    Stub implementation of CRYSTALS-Dilithium ML-DSA-44 (NIST FIPS 204).
    In production, this would use the 'dilithium-py' or 'oqs-python' library.

    Reference: https://pq-crystals.org/dilithium/
    """

    @property
    def algorithm(self) -> AlgorithmType:
        return AlgorithmType.ML_DSA_44

    def generate_keypair(self) -> KeyPair:
        # Stub: ML-DSA-44 public key is 1312 bytes, private key is 2528 bytes
        private_key = os.urandom(2528)
        public_key = os.urandom(1312)
        logger.debug("Generated ML-DSA-44 key pair (stub).")
        return KeyPair(
            algorithm=self.algorithm,
            public_key=public_key,
            private_key=private_key,
        )

    def sign(self, message: bytes, private_key: bytes) -> Signature:
        message_hash = hashlib.sha3_256(message).digest()
        # Stub: ML-DSA-44 signature is 2420 bytes
        sig_bytes = os.urandom(2420)
        public_key = os.urandom(1312)  # Placeholder
        logger.debug("Signed message with ML-DSA-44 (stub).")
        return Signature(
            algorithm=self.algorithm,
            signature_bytes=sig_bytes,
            public_key=public_key,
            message_hash=message_hash,
        )

    def verify(self, message: bytes, signature: Signature, public_key: bytes) -> bool:
        # Stub: always returns True for simulation purposes
        logger.debug("Verified ML-DSA-44 signature (stub - always True).")
        return True


# --- The Crypto-Agility Layer ---

class CryptoAgilityLayer:
    """
    The central dispatcher for all cryptographic operations.

    This class maintains a registry of available signing algorithm implementations
    and routes signing/verification requests to the appropriate plugin.

    To add a new algorithm:
    1. Create a class that inherits from BaseSigner.
    2. Register it with the layer using register_signer().

    Usage:
        layer = CryptoAgilityLayer()
        keypair = layer.generate_keypair(AlgorithmType.ML_DSA_44)
        sig = layer.sign(message, keypair.private_key, AlgorithmType.ML_DSA_44)
        is_valid = layer.verify(message, sig, keypair.public_key)
    """

    def __init__(self):
        self._signers: dict[AlgorithmType, BaseSigner] = {}
        # Register default implementations
        self.register_signer(EcdsaSecp256k1Signer())
        self.register_signer(MlDsa44Signer())
        logger.info("CryptoAgilityLayer initialized with default signers.")

    def register_signer(self, signer: BaseSigner) -> None:
        """
        Registers a new signing algorithm implementation.

        Args:
            signer: An instance of a class implementing BaseSigner.
        """
        self._signers[signer.algorithm] = signer
        logger.info(f"Registered signer for algorithm: {signer.algorithm.value}")

    def get_available_algorithms(self) -> list[AlgorithmType]:
        """Returns a list of all registered algorithm types."""
        return list(self._signers.keys())

    def generate_keypair(self, algorithm: AlgorithmType) -> KeyPair:
        """Generates a key pair using the specified algorithm."""
        signer = self._get_signer(algorithm)
        return signer.generate_keypair()

    def sign(self, message: bytes, private_key: bytes, algorithm: AlgorithmType) -> Signature:
        """Signs a message using the specified algorithm."""
        signer = self._get_signer(algorithm)
        return signer.sign(message, private_key)

    def verify(self, message: bytes, signature: Signature, public_key: bytes) -> bool:
        """Verifies a signature using the algorithm specified in the Signature object."""
        signer = self._get_signer(signature.algorithm)
        return signer.verify(message, signature, public_key)

    def sign_hybrid(
        self,
        message: bytes,
        classical_private_key: bytes,
        pqc_private_key: bytes,
        hybrid_algorithm: AlgorithmType = AlgorithmType.HYBRID_ECDSA_MLDSA44,
    ) -> HybridSignature:
        """
        Creates a hybrid signature using both a classical and a PQC algorithm.
        Both signatures are computed independently over the same message.

        This provides a "belt and suspenders" security model: the asset is
        protected as long as at least one of the two algorithms remains secure.

        Args:
            message:              The message to sign.
            classical_private_key: The private key for the classical algorithm.
            pqc_private_key:       The private key for the PQC algorithm.
            hybrid_algorithm:      The hybrid algorithm identifier.

        Returns:
            A HybridSignature containing both signatures.
        """
        logger.info(f"Creating hybrid signature ({hybrid_algorithm.value})...")
        classical_sig = self.sign(message, classical_private_key, AlgorithmType.ECDSA_SECP256K1)
        pqc_sig = self.sign(message, pqc_private_key, AlgorithmType.ML_DSA_44)
        return HybridSignature(
            classical_sig=classical_sig,
            pqc_sig=pqc_sig,
            algorithm=hybrid_algorithm,
        )

    def verify_hybrid(
        self,
        message: bytes,
        hybrid_sig: HybridSignature,
        classical_public_key: bytes,
        pqc_public_key: bytes,
    ) -> bool:
        """
        Verifies a hybrid signature. BOTH component signatures must be valid.

        Args:
            message:              The original message.
            hybrid_sig:           The HybridSignature to verify.
            classical_public_key: The classical public key.
            pqc_public_key:       The PQC public key.

        Returns:
            True only if BOTH the classical and PQC signatures are valid.
        """
        classical_valid = self.verify(message, hybrid_sig.classical_sig, classical_public_key)
        pqc_valid = self.verify(message, hybrid_sig.pqc_sig, pqc_public_key)
        result = classical_valid and pqc_valid
        logger.info(
            f"Hybrid signature verification: classical={classical_valid}, pqc={pqc_valid}, result={result}"
        )
        return result

    def _get_signer(self, algorithm: AlgorithmType) -> BaseSigner:
        """Retrieves the registered signer for the given algorithm."""
        signer = self._signers.get(algorithm)
        if not signer:
            raise ValueError(
                f"No signer registered for algorithm '{algorithm.value}'. "
                f"Available algorithms: {[a.value for a in self.get_available_algorithms()]}"
            )
        return signer
