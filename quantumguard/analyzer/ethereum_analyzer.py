"""
QuantumGuard Labs — Ethereum Quantum Risk Analyzer
====================================================
Analyzes Ethereum (EVM-compatible) addresses for quantum vulnerability.

Quantum risk on Ethereum:
  - All Ethereum accounts use ECDSA (secp256k1) — same as Bitcoin.
  - When an EOA (Externally Owned Account) sends a transaction, its ECDSA
    public key is revealed in the transaction signature.
  - A sufficiently powerful quantum computer could use Shor's algorithm to
    derive the private key from the exposed public key.
  - Smart contracts are not directly vulnerable, but their admin keys may be.

Risk classification:
  CRITICAL  — Address has sent transactions AND holds significant ETH (>10 ETH)
  HIGH      — Address has sent transactions (public key exposed)
  MEDIUM    — Smart contract with exposed admin key, or P2SH-like patterns
  LOW       — EOA with balance but no outgoing transactions (pubkey not exposed)
  SAFE      — Empty address or newly created

Supported networks:
  - Ethereum Mainnet
  - Ethereum Goerli Testnet
  - Any EVM-compatible network (via custom RPC URL)
"""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any

from .models import RiskLevel

logger = logging.getLogger(__name__)


# ── Data Classes ──────────────────────────────────────────────────────────────

@dataclass
class EthAddressRisk:
    """Quantum risk assessment for a single Ethereum address."""
    address: str
    network: str
    balance_eth: float
    balance_wei: int
    tx_count: int                    # Outgoing transaction count (nonce)
    is_contract: bool
    is_pubkey_exposed: bool          # True if address has sent any transaction
    risk_level: RiskLevel
    risk_score: float                # 0.0 (safe) to 100.0 (critical)
    risk_reason: str
    recommendation: str
    scanned_at: float = field(default_factory=time.time)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "address": self.address,
            "network": self.network,
            "balance_eth": self.balance_eth,
            "balance_wei": self.balance_wei,
            "tx_count": self.tx_count,
            "is_contract": self.is_contract,
            "is_pubkey_exposed": self.is_pubkey_exposed,
            "risk_level": self.risk_level.value,
            "risk_score": self.risk_score,
            "risk_reason": self.risk_reason,
            "recommendation": self.recommendation,
            "scanned_at": self.scanned_at,
            "error": self.error,
        }


@dataclass
class EthPortfolioReport:
    """Aggregated quantum risk report for a portfolio of Ethereum addresses."""
    addresses: List[EthAddressRisk]
    total_addresses: int
    total_eth: float
    risk_distribution: Dict[str, int]
    at_risk_eth: float               # ETH held in HIGH/CRITICAL addresses
    quantum_readiness_score: float   # 0–100, higher is safer
    network: str
    scanned_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_addresses": self.total_addresses,
            "total_eth": self.total_eth,
            "risk_distribution": self.risk_distribution,
            "at_risk_eth": self.at_risk_eth,
            "quantum_readiness_score": self.quantum_readiness_score,
            "network": self.network,
            "scanned_at": self.scanned_at,
            "addresses": [a.to_dict() for a in self.addresses],
        }


# ── Ethereum Quantum Risk Analyzer ───────────────────────────────────────────

class EthereumQuantumAnalyzer:
    """
    Analyzes Ethereum addresses for quantum computing vulnerability.

    Uses EthereumConnector to fetch on-chain data and applies
    QuantumGuard Labs' risk classification model.
    """

    # Risk thresholds
    HIGH_VALUE_ETH = 10.0    # ETH threshold for CRITICAL vs HIGH
    MED_VALUE_ETH  = 0.1     # ETH threshold for HIGH vs LOW

    def __init__(self, connector=None):
        """
        Args:
            connector: EthereumConnector instance. If None, uses mock data.
        """
        self.connector = connector
        logger.info("EthereumQuantumAnalyzer initialized.")

    def analyze_address(self, address: str) -> EthAddressRisk:
        """
        Analyze a single Ethereum address for quantum risk.

        Args:
            address: Ethereum address (0x-prefixed, 42 chars).

        Returns:
            EthAddressRisk with full risk assessment.
        """
        if not self.connector:
            return self._mock_analysis(address)

        try:
            info = self.connector.get_address_info(address)
            return self._classify_risk(info)
        except Exception as e:
            logger.error(f"Failed to analyze Ethereum address {address}: {e}")
            return EthAddressRisk(
                address=address,
                network="unknown",
                balance_eth=0.0,
                balance_wei=0,
                tx_count=0,
                is_contract=False,
                is_pubkey_exposed=False,
                risk_level=RiskLevel.SAFE,
                risk_score=0.0,
                risk_reason="Analysis failed",
                recommendation="Retry analysis",
                error=str(e),
            )

    def analyze_batch(self, addresses: List[str]) -> EthPortfolioReport:
        """
        Analyze multiple Ethereum addresses and generate a portfolio report.

        Args:
            addresses: List of Ethereum addresses.

        Returns:
            EthPortfolioReport with aggregated risk metrics.
        """
        results = []
        for addr in addresses:
            result = self.analyze_address(addr)
            results.append(result)

        return self._build_portfolio_report(results)

    def _classify_risk(self, info: Dict[str, Any]) -> EthAddressRisk:
        """Apply QuantumGuard risk classification to raw address info."""
        address = info["address"]
        network = info.get("network", "mainnet")
        balance_eth = info.get("balance_eth", 0.0)
        balance_wei = info.get("balance_wei", 0)
        tx_count = info.get("tx_count", 0)
        is_contract = info.get("is_contract", False)
        is_pubkey_exposed = info.get("is_pubkey_exposed", False)

        # Determine risk level
        if is_contract:
            risk_level = RiskLevel.MEDIUM
            risk_score = 40.0
            risk_reason = (
                "Smart contract — quantum risk depends on admin key management. "
                "If the deployer or owner key has been used for transactions, "
                "it may be vulnerable."
            )
            recommendation = (
                "Audit all privileged keys associated with this contract. "
                "Plan migration to PQC-compatible multisig or governance."
            )
        elif is_pubkey_exposed and balance_eth >= self.HIGH_VALUE_ETH:
            risk_level = RiskLevel.CRITICAL
            risk_score = 95.0
            risk_reason = (
                f"High-value EOA ({balance_eth:.4f} ETH) with {tx_count} outgoing "
                f"transaction(s). ECDSA public key is exposed on-chain. "
                f"A quantum adversary could derive the private key."
            )
            recommendation = (
                "URGENT: Migrate all funds to a new quantum-safe address immediately. "
                "Do not reuse this address. Consider using a hardware wallet with "
                "post-quantum signature support."
            )
        elif is_pubkey_exposed:
            risk_level = RiskLevel.HIGH
            risk_score = 75.0
            risk_reason = (
                f"EOA has sent {tx_count} transaction(s); ECDSA public key is "
                f"exposed in transaction signatures. Quantum computers can use "
                f"Shor's algorithm to derive the private key from the public key."
            )
            recommendation = (
                "Migrate funds to a new address using a quantum-safe signature scheme. "
                "Generate a fresh key pair and transfer all assets."
            )
        elif balance_eth > self.MED_VALUE_ETH:
            risk_level = RiskLevel.LOW
            risk_score = 20.0
            risk_reason = (
                f"EOA holds {balance_eth:.4f} ETH but has never sent a transaction. "
                f"Public key has not been exposed on-chain. "
                f"Risk will increase if any outgoing transaction is made."
            )
            recommendation = (
                "Monitor quantum computing developments. "
                "Migrate to a quantum-safe address before making any outgoing transactions. "
                "Consider using a stealth address scheme."
            )
        elif balance_eth > 0:
            risk_level = RiskLevel.LOW
            risk_score = 10.0
            risk_reason = "Small balance, no outgoing transactions. Public key not exposed."
            recommendation = "Low priority. Monitor and migrate when convenient."
        else:
            risk_level = RiskLevel.SAFE
            risk_score = 0.0
            risk_reason = "Address has no balance. No quantum risk at this time."
            recommendation = "No action required."

        return EthAddressRisk(
            address=address,
            network=network,
            balance_eth=balance_eth,
            balance_wei=balance_wei,
            tx_count=tx_count,
            is_contract=is_contract,
            is_pubkey_exposed=is_pubkey_exposed,
            risk_level=risk_level,
            risk_score=risk_score,
            risk_reason=risk_reason,
            recommendation=recommendation,
        )

    def _build_portfolio_report(self, results: List[EthAddressRisk]) -> EthPortfolioReport:
        """Aggregate individual results into a portfolio report."""
        risk_dist = {level.value: 0 for level in RiskLevel}
        total_eth = 0.0
        at_risk_eth = 0.0
        network = "mainnet"

        for r in results:
            risk_dist[r.risk_level.value] += 1
            total_eth += r.balance_eth
            if r.risk_level in (RiskLevel.CRITICAL, RiskLevel.HIGH):
                at_risk_eth += r.balance_eth
            if r.network:
                network = r.network

        # Quantum readiness score: weighted by ETH value and risk level
        if total_eth > 0:
            safe_eth = total_eth - at_risk_eth
            readiness = (safe_eth / total_eth) * 100
        elif results:
            safe_count = risk_dist.get("SAFE", 0) + risk_dist.get("LOW", 0)
            readiness = (safe_count / len(results)) * 100
        else:
            readiness = 100.0

        return EthPortfolioReport(
            addresses=results,
            total_addresses=len(results),
            total_eth=round(total_eth, 6),
            risk_distribution=risk_dist,
            at_risk_eth=round(at_risk_eth, 6),
            quantum_readiness_score=round(readiness, 1),
            network=network,
        )

    def _mock_analysis(self, address: str) -> EthAddressRisk:
        """Generate mock analysis when no connector is available."""
        import hashlib, random
        seed = int(hashlib.md5(address.encode()).hexdigest(), 16) % (2 ** 31)
        rng = random.Random(seed)

        balance_eth = round(rng.uniform(0, 50), 4)
        tx_count = rng.randint(0, 100)
        is_contract = address.startswith("0x000") or rng.random() < 0.1
        is_pubkey_exposed = tx_count > 0 and not is_contract

        mock_info = {
            "address": address,
            "network": "mainnet (mock)",
            "balance_eth": balance_eth,
            "balance_wei": int(balance_eth * 1e18),
            "tx_count": tx_count,
            "is_contract": is_contract,
            "is_pubkey_exposed": is_pubkey_exposed,
        }
        return self._classify_risk(mock_info)
