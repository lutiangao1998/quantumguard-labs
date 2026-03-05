"""
QuantumGuard Labs — Blockchain Connector
=========================================
Provides a unified interface for interacting with Bitcoin and Ethereum.

Supported backends:
  - BlockstreamConnector:     Bitcoin Mainnet & Testnet via Blockstream.info API.
  - EthereumConnector:        Ethereum Mainnet & Goerli via public JSON-RPC.
  - BitcoinCoreConnector:     Local Bitcoin Core node via JSON-RPC.
  - MockBitcoinConnector:     Deterministic mock data for testing and demos.

Usage:
    # Bitcoin Mainnet:
    connector = BlockstreamConnector(network="mainnet")
    utxos = connector.get_utxos_for_address("bc1q...")

    # Bitcoin Testnet:
    connector = BlockstreamConnector(network="testnet")
    utxos = connector.get_utxos_for_address("tb1q...")

    # Ethereum Mainnet:
    connector = EthereumConnector(network="mainnet")
    info = connector.get_address_info("0x...")
"""

import logging
import random
import hashlib
import requests
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List

from quantumguard.analyzer.models import UTXO, ScriptType

logger = logging.getLogger(__name__)

SATOSHI = 1e-8

BLOCKSTREAM_MAINNET = "https://blockstream.info/api"
BLOCKSTREAM_TESTNET = "https://blockstream.info/testnet/api"
ETH_MAINNET_RPC    = "https://eth.llamarpc.com"
ETH_GOERLI_RPC     = "https://rpc.ankr.com/eth_goerli"


# ── Abstract Base ─────────────────────────────────────────────────────────────

class BaseBlockchainConnector(ABC):
    """Abstract base class for all blockchain connectors."""

    @abstractmethod
    def get_utxos_for_address(self, address: str) -> List[UTXO]:
        """Fetch all UTXOs for a given address."""
        ...

    @abstractmethod
    def get_portfolio_utxos(self, count: int = 200) -> List[UTXO]:
        """Fetch a portfolio-level sample of UTXOs."""
        ...

    def broadcast_transaction(self, tx_hex: str) -> Optional[str]:
        """Broadcast a signed raw transaction. Returns txid or None."""
        return None

    def get_transaction(self, txid: str) -> Optional[dict]:
        """Retrieve a transaction by txid."""
        return None

    # Alias for backward compatibility
    def get_utxo_set(self, limit: int = 1000) -> List[UTXO]:
        return self.get_portfolio_utxos(count=limit)


# ── Blockstream Connector (Mainnet + Testnet) ─────────────────────────────────

class BlockstreamConnector(BaseBlockchainConnector):
    """
    Fetches REAL Bitcoin UTXO data via the Blockstream.info public API.
    Supports both Mainnet and Testnet. No API key required.

    API docs: https://github.com/Blockstream/esplora/blob/master/API.md
    """

    def __init__(self, network: str = "testnet"):
        """
        Args:
            network: "mainnet" or "testnet"
        """
        if network == "mainnet":
            self.base_url = BLOCKSTREAM_MAINNET
        elif network == "testnet":
            self.base_url = BLOCKSTREAM_TESTNET
        else:
            raise ValueError(f"Unknown network: {network}. Use 'mainnet' or 'testnet'.")
        self.network = network
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "QuantumGuard-Labs/1.0"})
        logger.info(f"BlockstreamConnector initialized for Bitcoin {network}.")

    def get_utxos_for_address(self, address: str) -> List[UTXO]:
        """Fetch real UTXOs for a Bitcoin address."""
        try:
            resp = self.session.get(
                f"{self.base_url}/address/{address}/utxo", timeout=15
            )
            resp.raise_for_status()
            raw_utxos = resp.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Blockstream API error for {address}: {e}")
            raise RuntimeError(f"Failed to fetch UTXOs from Blockstream API: {e}")

        if not raw_utxos:
            logger.info(f"No UTXOs found for {self.network} address: {address}")
            return []

        script_type = self._classify_address(address)
        tx_count = self._get_tx_count(address)
        spent_count = self._get_spent_count(address)
        address_reused = tx_count > 1
        # If address has spent outputs, public key was revealed in scriptSig/witness
        is_pubkey_exposed = spent_count > 0

        utxos = []
        for u in raw_utxos:
            utxos.append(UTXO(
                txid=u.get("txid", "unknown"),
                vout=u.get("vout", 0),
                address=address,
                value_btc=round(u.get("value", 0) * SATOSHI, 8),
                script_type=script_type,
                is_pubkey_exposed=is_pubkey_exposed or script_type == ScriptType.P2PK,
                is_reused=address_reused,
            ))

        logger.info(
            f"Blockstream ({self.network}): Fetched {len(utxos)} UTXOs for {address} "
            f"(spent={spent_count}, pubkey_exposed={is_pubkey_exposed})"
        )
        return utxos

    def get_portfolio_utxos(self, count: int = 200) -> List[UTXO]:
        """Not applicable for Blockstream — use get_utxos_for_address() instead."""
        raise NotImplementedError(
            "BlockstreamConnector does not support portfolio scanning. "
            "Use get_utxos_for_address(address) instead."
        )

    def get_fee_estimates(self) -> Dict[int, int]:
        """Fetch current fee estimates (sat/vB) keyed by confirmation target (blocks)."""
        try:
            resp = self.session.get(f"{self.base_url}/fee-estimates", timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.warning(f"Failed to fetch fee estimates: {e}")
            return {1: 20, 3: 10, 6: 5}

    def broadcast_transaction(self, tx_hex: str) -> Optional[str]:
        """Broadcast a signed raw transaction to the Bitcoin network."""
        resp = self.session.post(
            f"{self.base_url}/tx",
            data=tx_hex,
            headers={"Content-Type": "text/plain"},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.text.strip()

    def get_transaction(self, txid: str) -> Optional[dict]:
        """Fetch full transaction details."""
        try:
            resp = self.session.get(f"{self.base_url}/tx/{txid}", timeout=15)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

    def status(self) -> Dict[str, Any]:
        """Check connectivity and return network status."""
        try:
            resp = self.session.get(f"{self.base_url}/blocks/tip/height", timeout=10)
            resp.raise_for_status()
            block_height = int(resp.text.strip())
            return {
                "status": "online",
                "network": self.network,
                "connector": "BlockstreamConnector",
                "api": self.base_url,
                "latest_block_height": block_height,
            }
        except Exception as e:
            return {
                "status": "offline",
                "network": self.network,
                "connector": "BlockstreamConnector",
                "error": str(e),
            }

    def _get_tx_count(self, address: str) -> int:
        try:
            resp = self.session.get(f"{self.base_url}/address/{address}", timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return data.get("chain_stats", {}).get("tx_count", 0)
        except Exception:
            return 0

    def _get_spent_count(self, address: str) -> int:
        try:
            resp = self.session.get(f"{self.base_url}/address/{address}", timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return data.get("chain_stats", {}).get("spent_txo_count", 0)
        except Exception:
            return 0

    @staticmethod
    def _classify_address(address: str) -> ScriptType:
        """Infer script type from Bitcoin address format."""
        if address.startswith("1"):
            return ScriptType.P2PKH
        if address.startswith("3"):
            return ScriptType.P2SH
        if address.startswith("bc1q") and len(address) == 42:
            return ScriptType.P2WPKH
        if address.startswith("bc1q") and len(address) > 42:
            return ScriptType.P2WSH
        if address.startswith("bc1p"):
            return ScriptType.P2TR
        if address.startswith("tb1q") and len(address) == 42:
            return ScriptType.P2WPKH
        if address.startswith("tb1q") and len(address) > 42:
            return ScriptType.P2WSH
        if address.startswith("tb1p"):
            return ScriptType.P2TR
        if address[0] in ("m", "n"):
            return ScriptType.P2PKH
        if address.startswith("2"):
            return ScriptType.P2SH
        return ScriptType.UNKNOWN


# Convenience aliases
class BlockstreamMainnetConnector(BlockstreamConnector):
    def __init__(self):
        super().__init__(network="mainnet")


class BlockstreamTestnetConnector(BlockstreamConnector):
    def __init__(self):
        super().__init__(network="testnet")


# ── Ethereum Connector ────────────────────────────────────────────────────────

class EthereumConnector:
    """
    Ethereum address quantum risk analyzer via public JSON-RPC endpoints.
    Analyzes EOA addresses for quantum vulnerability based on:
      - Whether the address has ever sent a transaction (public key exposed)
      - Address type (EOA vs contract)
    """

    def __init__(self, network: str = "mainnet"):
        """
        Args:
            network: "mainnet" or "goerli"
        """
        if network == "mainnet":
            self.rpc_url = ETH_MAINNET_RPC
        elif network == "goerli":
            self.rpc_url = ETH_GOERLI_RPC
        else:
            raise ValueError(f"Unknown Ethereum network: {network}")
        self.network = network
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "QuantumGuard-Labs/1.0",
        })
        logger.info(f"EthereumConnector initialized for {network}.")

    def _rpc(self, method: str, params: list) -> Any:
        payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
        resp = self.session.post(self.rpc_url, json=payload, timeout=15)
        resp.raise_for_status()
        result = resp.json()
        if "error" in result:
            raise RuntimeError(f"RPC error: {result['error']}")
        return result.get("result")

    def get_address_info(self, address: str) -> Dict[str, Any]:
        """
        Fetch Ethereum address information and quantum risk assessment.

        Returns:
            Dict with balance, tx_count, is_contract, is_pubkey_exposed, risk_level, etc.
        """
        if not address.startswith("0x") or len(address) != 42:
            raise ValueError(f"Invalid Ethereum address format: {address}")

        # Get balance
        balance_hex = self._rpc("eth_getBalance", [address, "latest"])
        balance_wei = int(balance_hex, 16) if balance_hex else 0
        balance_eth = balance_wei / 1e18

        # Get transaction count (nonce) — if > 0, address has sent tx → pubkey exposed
        nonce_hex = self._rpc("eth_getTransactionCount", [address, "latest"])
        tx_count = int(nonce_hex, 16) if nonce_hex else 0

        # Check if contract
        code = self._rpc("eth_getCode", [address, "latest"])
        is_contract = code not in (None, "0x", "0x0")

        # Quantum risk assessment
        # EOA that has sent transactions → ECDSA public key exposed in tx signature
        is_pubkey_exposed = tx_count > 0 and not is_contract

        if is_contract:
            risk_level = "MEDIUM"
            risk_reason = "Smart contract — quantum risk depends on key management"
        elif is_pubkey_exposed:
            risk_level = "HIGH"
            risk_reason = f"EOA has sent {tx_count} transaction(s); ECDSA public key exposed in signatures"
        elif balance_eth > 0:
            risk_level = "LOW"
            risk_reason = "EOA has never sent a transaction; public key not yet exposed"
        else:
            risk_level = "SAFE"
            risk_reason = "Address has no balance"

        return {
            "address": address,
            "network": self.network,
            "balance_eth": round(balance_eth, 8),
            "balance_wei": balance_wei,
            "tx_count": tx_count,
            "is_contract": is_contract,
            "is_pubkey_exposed": is_pubkey_exposed,
            "risk_level": risk_level,
            "risk_reason": risk_reason,
            "recommendation": self._get_recommendation(risk_level),
        }

    def batch_analyze(self, addresses: List[str]) -> List[Dict[str, Any]]:
        """Analyze multiple Ethereum addresses for quantum risk."""
        results = []
        for addr in addresses:
            try:
                info = self.get_address_info(addr)
                results.append(info)
            except Exception as e:
                results.append({
                    "address": addr,
                    "error": str(e),
                    "risk_level": "UNKNOWN",
                })
        return results

    def status(self) -> Dict[str, Any]:
        """Check connectivity and return network status."""
        try:
            block_hex = self._rpc("eth_blockNumber", [])
            block_number = int(block_hex, 16) if block_hex else 0
            return {
                "status": "online",
                "network": self.network,
                "connector": "EthereumConnector",
                "rpc": self.rpc_url,
                "latest_block": block_number,
            }
        except Exception as e:
            return {
                "status": "offline",
                "network": self.network,
                "connector": "EthereumConnector",
                "error": str(e),
            }

    @staticmethod
    def _get_recommendation(risk_level: str) -> str:
        recommendations = {
            "CRITICAL": "URGENT: Migrate to a quantum-safe address immediately.",
            "HIGH": "Migrate to a new address using a quantum-safe signature scheme (e.g., ML-DSA-44).",
            "MEDIUM": "Review contract key management; plan migration to PQC-compatible infrastructure.",
            "LOW": "Monitor developments; migrate before making any outgoing transactions.",
            "SAFE": "No action required at this time.",
        }
        return recommendations.get(risk_level, "Assess risk and plan accordingly.")


# ── Bitcoin Core RPC Connector ────────────────────────────────────────────────

class BitcoinCoreConnector(BaseBlockchainConnector):
    """
    Connects to a Bitcoin Core node via JSON-RPC.
    Recommended for production deployments with a full node.
    """

    def __init__(
        self,
        rpc_url: str = "http://localhost:8332",
        rpc_user: str = "user",
        rpc_password: str = "password",
        network: str = "mainnet",
    ):
        self.rpc_url = rpc_url
        self.auth = (rpc_user, rpc_password)
        self.network = network
        logger.info(f"BitcoinCoreConnector initialized for {network} at {rpc_url}")

    def _rpc_call(self, method: str, params: list = None) -> dict:
        payload = {"jsonrpc": "1.0", "id": "qg", "method": method, "params": params or []}
        resp = requests.post(self.rpc_url, json=payload, auth=self.auth, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        if result.get("error"):
            raise RuntimeError(f"RPC Error: {result['error']}")
        return result["result"]

    def get_utxos_for_address(self, address: str) -> List[UTXO]:
        raw = self._rpc_call("listunspent", [0, 9999999, [address]])
        return [self._parse_rpc_utxo(u, address) for u in raw]

    def get_portfolio_utxos(self, count: int = 200) -> List[UTXO]:
        raw = self._rpc_call("listunspent", [0, 9999999])
        return [self._parse_rpc_utxo(u, u.get("address", "")) for u in raw[:count]]

    @staticmethod
    def _parse_rpc_utxo(u: dict, address: str) -> UTXO:
        script_hex = u.get("scriptPubKey", "")
        script_type = BitcoinCoreConnector._classify_script(script_hex)
        return UTXO(
            txid=u["txid"],
            vout=u["vout"],
            address=address,
            value_btc=float(u.get("amount", 0)),
            script_type=script_type,
            is_pubkey_exposed=script_type == ScriptType.P2PK,
            is_reused=False,
        )

    @staticmethod
    def _classify_script(script_hex: str) -> ScriptType:
        if script_hex.startswith("76a914"):   return ScriptType.P2PKH
        if script_hex.startswith("a914"):     return ScriptType.P2SH
        if script_hex.startswith("0014"):     return ScriptType.P2WPKH
        if script_hex.startswith("0020"):     return ScriptType.P2WSH
        if script_hex.startswith("5120"):     return ScriptType.P2TR
        if script_hex.endswith("ac"):         return ScriptType.P2PK
        return ScriptType.UNKNOWN


# ── Mock Connector ────────────────────────────────────────────────────────────

class MockBitcoinConnector(BaseBlockchainConnector):
    """
    Generates deterministic mock UTXO data for testing and demos.
    Uses a fixed random seed for full reproducibility.
    """

    SCRIPT_DISTRIBUTION = [
        (ScriptType.P2PK,   0.05),
        (ScriptType.P2PKH,  0.35),
        (ScriptType.P2SH,   0.15),
        (ScriptType.P2WPKH, 0.25),
        (ScriptType.P2WSH,  0.05),
        (ScriptType.P2TR,   0.15),
    ]

    def __init__(self, seed: int = 42):
        self._rng = random.Random(seed)
        logger.info("MockBitcoinConnector initialized (for testing/demo only).")

    def get_portfolio_utxos(self, count: int = 200) -> List[UTXO]:
        script_types = [st for st, _ in self.SCRIPT_DISTRIBUTION]
        weights = [w for _, w in self.SCRIPT_DISTRIBUTION]
        utxos = []
        for i in range(count):
            script_type = self._rng.choices(script_types, weights=weights, k=1)[0]
            value_btc = round(self._rng.lognormvariate(mu=-2, sigma=2), 8)
            value_btc = max(0.00001, min(value_btc, 500.0))
            txid = hashlib.sha256(f"mock_tx_{i}_{script_type.value}".encode()).hexdigest()
            address = self._mock_address(script_type, i)
            reuse_prob = {ScriptType.P2PKH: 0.30, ScriptType.P2WPKH: 0.20}.get(script_type, 0.05)
            utxos.append(UTXO(
                txid=txid,
                vout=self._rng.randint(0, 3),
                address=address,
                value_btc=value_btc,
                script_type=script_type,
                is_pubkey_exposed=script_type == ScriptType.P2PK,
                is_reused=self._rng.random() < reuse_prob,
            ))
        return utxos

    def get_utxos_for_address(self, address: str) -> List[UTXO]:
        seed = int(hashlib.md5(address.encode()).hexdigest(), 16) % (2 ** 31)
        rng = random.Random(seed)
        count = rng.randint(1, 5)
        script_type = (
            ScriptType.P2PKH if address.startswith("1") else
            ScriptType.P2WPKH if address.startswith("bc1q") else
            ScriptType.P2TR
        )
        return [
            UTXO(
                txid=hashlib.sha256(f"{address}_{i}".encode()).hexdigest(),
                vout=i,
                address=address,
                value_btc=round(rng.uniform(0.001, 2.0), 8),
                script_type=script_type,
                is_pubkey_exposed=False,
                is_reused=rng.random() < 0.4,
            )
            for i in range(count)
        ]

    def broadcast_transaction(self, tx_hex: str) -> Optional[str]:
        fake_txid = hashlib.sha256(tx_hex.encode()).hexdigest()
        logger.info(f"MockConnector: Simulated broadcast. Fake TXID: {fake_txid}")
        return fake_txid

    def get_transaction(self, txid: str) -> Optional[dict]:
        return {"txid": txid, "confirmations": self._rng.randint(1, 10000), "status": "confirmed"}

    @staticmethod
    def _mock_address(script_type: ScriptType, idx: int) -> str:
        prefix = {
            ScriptType.P2PK:   "1",
            ScriptType.P2PKH:  "1",
            ScriptType.P2SH:   "3",
            ScriptType.P2WPKH: "bc1q",
            ScriptType.P2WSH:  "bc1q",
            ScriptType.P2TR:   "bc1p",
        }.get(script_type, "1")
        suffix = hashlib.sha256(f"{script_type.value}_{idx}".encode()).hexdigest()[:28]
        return f"{prefix}{suffix}"
