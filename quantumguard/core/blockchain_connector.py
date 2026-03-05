"""
QuantumGuard Labs - Blockchain Connector
=========================================
Provides a unified interface for interacting with Bitcoin nodes and APIs.

Supported backends:
  - BitcoinCoreConnector:          Local Bitcoin Core node via JSON-RPC.
  - BlockstreamTestnetConnector:   Real Testnet UTXO data via Blockstream.info API.
  - MockBitcoinConnector:          Deterministic mock data for testing and demos.

Usage:
    # Real Testnet (no node required):
    connector = BlockstreamTestnetConnector()
    utxos = connector.get_utxos_for_address("tb1q...")

    # Demo/testing:
    connector = MockBitcoinConnector()
    utxos = connector.get_portfolio_utxos(count=200)
"""

import logging
import random
import hashlib
import requests
from abc import ABC, abstractmethod
from typing import Optional

from quantumguard.analyzer.models import UTXO, ScriptType

logger = logging.getLogger(__name__)

SATOSHI = 1e-8


# ── Abstract Base ─────────────────────────────────────────────────────────────

class BaseBlockchainConnector(ABC):
    """Abstract base class for all Bitcoin connectors."""

    @abstractmethod
    def get_utxos_for_address(self, address: str) -> list[UTXO]:
        """Fetch all UTXOs for a given address."""
        ...

    @abstractmethod
    def get_portfolio_utxos(self, count: int = 200) -> list[UTXO]:
        """Fetch a portfolio-level sample of UTXOs."""
        ...

    def broadcast_transaction(self, tx_hex: str) -> Optional[str]:
        """Broadcast a signed raw transaction. Returns txid or None."""
        return None

    def get_transaction(self, txid: str) -> Optional[dict]:
        """Retrieve a transaction by txid."""
        return None

    # Alias for backward compatibility
    def get_utxo_set(self, limit: int = 1000) -> list[UTXO]:
        return self.get_portfolio_utxos(count=limit)


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

    def get_utxos_for_address(self, address: str) -> list[UTXO]:
        raw = self._rpc_call("listunspent", [0, 9999999, [address]])
        return [self._parse_rpc_utxo(u, address) for u in raw]

    def get_portfolio_utxos(self, count: int = 200) -> list[UTXO]:
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


# ── Blockstream Testnet Connector ─────────────────────────────────────────────

class BlockstreamTestnetConnector(BaseBlockchainConnector):
    """
    Fetches REAL Bitcoin Testnet UTXO data via the Blockstream.info public API.
    No API key required. Suitable for live demos and testnet validation.

    API docs: https://github.com/Blockstream/esplora/blob/master/API.md
    """

    BASE_URL = "https://blockstream.info/testnet/api"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "QuantumGuard-Labs/0.1"})
        logger.info("BlockstreamTestnetConnector initialized (Bitcoin Testnet via Blockstream).")

    def get_utxos_for_address(self, address: str) -> list[UTXO]:
        """Fetch real UTXOs for a Bitcoin testnet address."""
        try:
            resp = self.session.get(f"{self.BASE_URL}/address/{address}/utxo", timeout=15)
            resp.raise_for_status()
            raw_utxos = resp.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Blockstream API error for {address}: {e}")
            raise RuntimeError(f"Failed to fetch UTXOs from Blockstream API: {e}")

        if not raw_utxos:
            logger.info(f"No UTXOs found for testnet address: {address}")
            return []

        script_type = self._classify_address(address)
        tx_count = self._get_tx_count(address)
        address_reused = tx_count > 1

        utxos = []
        for u in raw_utxos:
            utxos.append(UTXO(
                txid=u.get("txid", "unknown"),
                vout=u.get("vout", 0),
                address=address,
                value_btc=round(u.get("value", 0) * SATOSHI, 8),
                script_type=script_type,
                is_pubkey_exposed=script_type == ScriptType.P2PK,
                is_reused=address_reused,
            ))

        logger.info(f"Blockstream: Fetched {len(utxos)} UTXOs for {address} (testnet).")
        return utxos

    def get_portfolio_utxos(self, count: int = 200) -> list[UTXO]:
        """Not applicable for Blockstream — use get_utxos_for_address() instead."""
        raise NotImplementedError(
            "BlockstreamTestnetConnector does not support portfolio scanning. "
            "Use get_utxos_for_address(address) instead."
        )

    def _get_tx_count(self, address: str) -> int:
        """Get the number of confirmed transactions for an address."""
        try:
            resp = self.session.get(f"{self.BASE_URL}/address/{address}", timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return data.get("chain_stats", {}).get("tx_count", 0)
        except Exception:
            return 0

    @staticmethod
    def _classify_address(address: str) -> ScriptType:
        """Infer script type from Bitcoin address format."""
        if address.startswith("tb1q") and len(address) == 42:
            return ScriptType.P2WPKH
        if address.startswith("tb1q") and len(address) > 42:
            return ScriptType.P2WSH
        if address.startswith("tb1p"):
            return ScriptType.P2TR
        if address.startswith(("m", "n")):
            return ScriptType.P2PKH
        if address.startswith("2"):
            return ScriptType.P2SH
        return ScriptType.UNKNOWN


# ── Mock Connector ────────────────────────────────────────────────────────────

class MockBitcoinConnector(BaseBlockchainConnector):
    """
    Generates deterministic mock UTXO data for testing and demos.
    Uses a fixed random seed for full reproducibility.
    """

    # Realistic mainnet UTXO set composition
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

    def get_portfolio_utxos(self, count: int = 200) -> list[UTXO]:
        """Generate a realistic mock portfolio of UTXOs."""
        script_types = [st for st, _ in self.SCRIPT_DISTRIBUTION]
        weights = [w for _, w in self.SCRIPT_DISTRIBUTION]
        utxos = []
        for i in range(count):
            script_type = self._rng.choices(script_types, weights=weights, k=1)[0]
            value_btc = round(self._rng.lognormvariate(mu=-2, sigma=2), 8)
            value_btc = max(0.00001, min(value_btc, 500.0))
            txid = hashlib.sha256(f"mock_tx_{i}_{script_type.value}".encode()).hexdigest()
            address = self._mock_address(script_type, i)
            reuse_prob = {
                ScriptType.P2PKH: 0.30,
                ScriptType.P2WPKH: 0.20,
            }.get(script_type, 0.05)
            utxos.append(UTXO(
                txid=txid,
                vout=self._rng.randint(0, 3),
                address=address,
                value_btc=value_btc,
                script_type=script_type,
                is_pubkey_exposed=script_type == ScriptType.P2PK,
                is_reused=self._rng.random() < reuse_prob,
            ))
        logger.info(f"MockConnector: Generated {len(utxos)} UTXOs.")
        return utxos

    def get_utxos_for_address(self, address: str) -> list[UTXO]:
        """Return a small set of mock UTXOs for a given address."""
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
