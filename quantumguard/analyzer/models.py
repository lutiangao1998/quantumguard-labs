"""
QuantumGuard Labs - Risk Analysis Data Models
==============================================
Defines the core data structures for quantum risk assessment of blockchain assets.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class RiskLevel(Enum):
    """
    Quantum risk severity classification for a given UTXO or address.

    - CRITICAL: Public key is directly exposed on-chain (e.g., P2PK outputs).
                A sufficiently powerful quantum computer can derive the private key
                from the exposed public key using Shor's algorithm.
    - HIGH:     Public key has been revealed through a prior spending transaction
                (e.g., a P2PKH address that has been used to send funds).
    - MEDIUM:   Address type is potentially vulnerable under certain conditions
                (e.g., Taproot key-path spend with known tweaked key).
    - LOW:      Address has never been used to send funds; public key is not
                directly exposed. Risk is lower but not zero (hash preimage attacks).
    - SAFE:     Address uses a script type that does not expose the public key,
                or has already been migrated to a quantum-resistant scheme.
    """
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    SAFE = "SAFE"


class ScriptType(Enum):
    """
    Bitcoin transaction output script types.
    """
    P2PK = "P2PK"                   # Pay-to-Public-Key (highest risk)
    P2PKH = "P2PKH"                 # Pay-to-Public-Key-Hash
    P2SH = "P2SH"                   # Pay-to-Script-Hash
    P2WPKH = "P2WPKH"               # Pay-to-Witness-Public-Key-Hash (SegWit v0)
    P2WSH = "P2WSH"                 # Pay-to-Witness-Script-Hash
    P2TR = "P2TR"                   # Pay-to-Taproot (SegWit v1)
    MULTISIG = "MULTISIG"           # Bare multisig
    UNKNOWN = "UNKNOWN"             # Unrecognized script type


@dataclass
class UTXO:
    """
    Represents a single Unspent Transaction Output (UTXO).

    Attributes:
        txid:           Transaction ID containing this output.
        vout:           Output index within the transaction.
        address:        Bitcoin address associated with this output.
        value_btc:      Value of the UTXO in BTC.
        script_type:    The type of the locking script (ScriptPubKey).
        pubkey_hex:     The raw public key in hex, if directly exposed (e.g., P2PK).
        is_pubkey_exposed: True if the public key is directly readable from the script.
        is_reused:      True if the address has been used for spending before,
                        meaning the public key has been revealed in a prior signature.
    """
    txid: str
    vout: int
    address: str
    value_btc: float
    script_type: ScriptType
    pubkey_hex: Optional[str] = None
    is_pubkey_exposed: bool = False
    is_reused: bool = False


@dataclass
class RiskAssessment:
    """
    The complete quantum risk assessment result for a single UTXO.

    Attributes:
        utxo:           The UTXO being assessed.
        risk_level:     The determined risk level.
        risk_score:     A numerical score from 0 (safe) to 100 (critical).
        risk_reasons:   A list of human-readable strings explaining the risk factors.
        migration_priority: A priority rank for migration scheduling (lower = higher priority).
        recommended_action: A brief description of the recommended mitigation action.
    """
    utxo: UTXO
    risk_level: RiskLevel
    risk_score: int
    risk_reasons: list[str] = field(default_factory=list)
    migration_priority: int = 0
    recommended_action: str = ""

    def to_dict(self) -> dict:
        """Serializes the assessment to a dictionary for reporting."""
        return {
            "txid": self.utxo.txid,
            "vout": self.utxo.vout,
            "address": self.utxo.address,
            "value_btc": self.utxo.value_btc,
            "script_type": self.utxo.script_type.value,
            "pubkey_exposed": self.utxo.is_pubkey_exposed,
            "address_reused": self.utxo.is_reused,
            "risk_level": self.risk_level.value,
            "risk_score": self.risk_score,
            "risk_reasons": self.risk_reasons,
            "migration_priority": self.migration_priority,
            "recommended_action": self.recommended_action,
        }


@dataclass
class RiskReport:
    """
    Aggregated risk report for a portfolio of UTXOs.

    Attributes:
        total_utxos:            Total number of UTXOs analyzed.
        total_value_btc:        Total value of all analyzed UTXOs in BTC.
        critical_count:         Number of UTXOs with CRITICAL risk.
        high_count:             Number of UTXOs with HIGH risk.
        medium_count:           Number of UTXOs with MEDIUM risk.
        low_count:              Number of UTXOs with LOW risk.
        safe_count:             Number of UTXOs classified as SAFE.
        critical_value_btc:     Total BTC value at CRITICAL risk.
        high_value_btc:         Total BTC value at HIGH risk.
        assessments:            The full list of individual risk assessments.
        quantum_readiness_score: An overall portfolio score from 0 to 100.
    """
    total_utxos: int = 0
    total_value_btc: float = 0.0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    safe_count: int = 0
    critical_value_btc: float = 0.0
    high_value_btc: float = 0.0
    assessments: list[RiskAssessment] = field(default_factory=list)
    quantum_readiness_score: float = 0.0
