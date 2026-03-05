"""
QuantumGuard Labs - Blockchain Connector
=========================================
Provides a unified interface for interacting with Bitcoin (and future blockchain)
nodes. This module abstracts away the specifics of different node implementations
(Bitcoin Core RPC, Electrum protocol, third-party APIs) to provide a clean,
consistent data access layer for the rest of the platform.

Supported backends:
  - Bitcoin Core (via JSON-RPC)
  - Electrum Protocol (for SPV-style access)
  - Mock/Stub (for testing and demonstration)

Usage:
    # For production with a local Bitcoin Core node:
    connector = BitcoinCoreConnector(rpc_url="http://localhost:8332", ...)
    utxos = connector.get_utxos_for_address("1A1zP1eP5QGefi2DMPTfTL5SLmv7Divf")

    # For testing:
    connector = MockBitcoinConnector()
    utxos = connector.get_utxos_for_address("test_address")
"""

import logging
import random
from abc import ABC, abstractmethod
from typing import Optional

from ..analyzer.models import ScriptType, UTXO
from ..analyzer.bitcoin_analyzer import classify_script_type

logger = logging.getLogger(__name__)


# --- Abstract Connector Interface ---

class BaseBlockchainConnector(ABC):
    """
    Abstract base class for blockchain data connectors.
    All concrete connectors MUST implement this interface.
    """

    @abstractmethod
    def get_utxos_for_address(self, address: str) -> list[UTXO]:
        """
        Fetches all unspent transaction outputs (UTXOs) for a given address.

        Args:
            address: The Bitcoin address to query.

        Returns:
            A list of UTXO objects associated with the address.
        """
        ...

    @abstractmethod
    def get_utxo_set(self, limit: int = 1000) -> list[UTXO]:
        """
        Fetches a sample of UTXOs from the full UTXO set.
        Used for portfolio-level risk analysis.

        Args:
            limit: Maximum number of UTXOs to return.

        Returns:
            A list of UTXO objects.
        """
        ...

    @abstractmethod
    def broadcast_transaction(self, tx_hex: str) -> Optional[str]:
        """
        Broadcasts a signed raw transaction to the network.

        Args:
            tx_hex: The signed raw transaction in hexadecimal format.

        Returns:
            The transaction ID (txid) if successful, None otherwise.
        """
        ...

    @abstractmethod
    def get_transaction(self, txid: str) -> Optional[dict]:
        """
        Retrieves a transaction by its ID.

        Args:
            txid: The transaction ID.

        Returns:
            A dictionary containing transaction details, or None if not found.
        """
        ...


# --- Bitcoin Core RPC Connector ---

class BitcoinCoreConnector(BaseBlockchainConnector):
    """
    Connects to a Bitcoin Core node via its JSON-RPC interface.

    This is the recommended connector for production deployments where
    a full node is available. It provides the most accurate and complete
    view of the blockchain.

    Args:
        rpc_url:    The URL of the Bitcoin Core RPC endpoint.
        rpc_user:   The RPC username (from bitcoin.conf).
        rpc_password: The RPC password (from bitcoin.conf).
        network:    The Bitcoin network ('mainnet', 'testnet', 'regtest').
    """

    def __init__(
        self,
        rpc_url: str = "http://localhost:8332",
        rpc_user: str = "user",
        rpc_password: str = "password",
        network: str = "mainnet",
    ):
        self.rpc_url = rpc_url
        self.rpc_user = rpc_user
        self.rpc_password = rpc_password
        self.network = network
        logger.info(f"BitcoinCoreConnector initialized for {network} at {rpc_url}")

    def _rpc_call(self, method: str, params: list = None) -> dict:
        """
        Makes a JSON-RPC call to the Bitcoin Core node.
        In production, this would use the 'requests' library.
        """
        # Stub: In production, implement with:
        # import requests
        # response = requests.post(
        #     self.rpc_url,
        #     auth=(self.rpc_user, self.rpc_password),
        #     json={"jsonrpc": "1.0", "id": "qmp", "method": method, "params": params or []}
        # )
        # return response.json()["result"]
        logger.debug(f"RPC call (stub): {method}({params})")
        return {}

    def get_utxos_for_address(self, address: str) -> list[UTXO]:
        """Fetches UTXOs for an address using 'scantxoutset' or 'listunspent'."""
        logger.info(f"Fetching UTXOs for address: {address}")
        # In production: self._rpc_call("scantxoutset", ["start", [f"addr({address})"]])
        return []

    def get_utxo_set(self, limit: int = 1000) -> list[UTXO]:
        """Fetches a sample of the UTXO set using 'gettxoutsetinfo' and 'scantxoutset'."""
        logger.info(f"Fetching UTXO set sample (limit={limit})...")
        return []

    def broadcast_transaction(self, tx_hex: str) -> Optional[str]:
        """Broadcasts a transaction using 'sendrawtransaction'."""
        logger.info(f"Broadcasting transaction: {tx_hex[:20]}...")
        # In production: return self._rpc_call("sendrawtransaction", [tx_hex])
        return None

    def get_transaction(self, txid: str) -> Optional[dict]:
        """Retrieves a transaction using 'getrawtransaction'."""
        # In production: return self._rpc_call("getrawtransaction", [txid, True])
        return None


# --- Mock Connector for Testing and Demonstration ---

# Predefined script hex patterns for generating realistic test UTXOs
_MOCK_SCRIPTS = {
    ScriptType.P2PK: "4104678afdb0fe5548271967f1a67130b7105cd6a828e03909a67962e0ea1f61deb649f6bc3f4cef38c4f35504e51ec112de5c384df7ba0b8d578a4c702b6bf11d5fac",
    ScriptType.P2PKH: "76a914{hash}88ac",
    ScriptType.P2WPKH: "0014{hash}",
    ScriptType.P2TR: "5120{hash}",
}


class MockBitcoinConnector(BaseBlockchainConnector):
    """
    A mock connector that generates synthetic UTXO data for testing,
    demonstration, and development purposes.

    The generated data is designed to be realistic and representative of
    the types of UTXOs found on the Bitcoin mainnet, including a mix of
    script types and risk profiles.
    """

    def __init__(self, seed: int = 42):
        random.seed(seed)
        logger.info("MockBitcoinConnector initialized (for testing/demo only).")

    def _generate_mock_utxo(self, index: int) -> UTXO:
        """Generates a single synthetic UTXO with a random script type and risk profile."""
        # Weighted distribution to simulate realistic mainnet composition
        script_type_weights = [
            (ScriptType.P2PK, 0.05),      # ~5% - old Satoshi-era outputs
            (ScriptType.P2PKH, 0.35),     # ~35% - legacy addresses
            (ScriptType.P2SH, 0.15),      # ~15% - P2SH (multisig, etc.)
            (ScriptType.P2WPKH, 0.25),    # ~25% - SegWit v0
            (ScriptType.P2WSH, 0.05),     # ~5% - SegWit v0 script hash
            (ScriptType.P2TR, 0.15),      # ~15% - Taproot
        ]
        script_types, weights = zip(*script_type_weights)
        script_type = random.choices(script_types, weights=weights, k=1)[0]

        # Simulate address reuse for P2PKH/P2WPKH (about 30% of the time)
        is_reused = (
            script_type in (ScriptType.P2PKH, ScriptType.P2WPKH)
            and random.random() < 0.30
        )

        # Simulate public key exposure for P2PK
        is_pubkey_exposed = script_type == ScriptType.P2PK

        # Generate a fake address
        address_prefix = {
            ScriptType.P2PK: "1",
            ScriptType.P2PKH: "1",
            ScriptType.P2SH: "3",
            ScriptType.P2WPKH: "bc1q",
            ScriptType.P2WSH: "bc1q",
            ScriptType.P2TR: "bc1p",
        }.get(script_type, "1")
        fake_hash = "".join(random.choices("0123456789abcdef", k=32))
        address = f"{address_prefix}{fake_hash}"

        # Generate a realistic BTC value (log-normal distribution)
        value_btc = round(random.lognormvariate(mu=-2, sigma=2), 8)
        value_btc = max(0.00001, min(value_btc, 500.0))  # Clamp to realistic range

        txid = "".join(random.choices("0123456789abcdef", k=64))

        return UTXO(
            txid=txid,
            vout=random.randint(0, 3),
            address=address,
            value_btc=value_btc,
            script_type=script_type,
            pubkey_hex="04" + "a" * 128 if is_pubkey_exposed else None,
            is_pubkey_exposed=is_pubkey_exposed,
            is_reused=is_reused,
        )

    def get_utxos_for_address(self, address: str) -> list[UTXO]:
        """Returns a small set of mock UTXOs for a given address."""
        count = random.randint(1, 5)
        utxos = [self._generate_mock_utxo(i) for i in range(count)]
        for utxo in utxos:
            utxo.address = address
        logger.info(f"MockConnector: Generated {count} UTXOs for address '{address}'.")
        return utxos

    def get_utxo_set(self, limit: int = 1000) -> list[UTXO]:
        """Returns a set of synthetic UTXOs representing a portfolio sample."""
        utxos = [self._generate_mock_utxo(i) for i in range(limit)]
        logger.info(f"MockConnector: Generated {len(utxos)} UTXOs for portfolio analysis.")
        return utxos

    def broadcast_transaction(self, tx_hex: str) -> Optional[str]:
        """Simulates a successful transaction broadcast."""
        fake_txid = "".join(random.choices("0123456789abcdef", k=64))
        logger.info(f"MockConnector: Simulated broadcast. Fake TXID: {fake_txid}")
        return fake_txid

    def get_transaction(self, txid: str) -> Optional[dict]:
        """Returns a mock transaction object."""
        return {
            "txid": txid,
            "confirmations": random.randint(1, 10000),
            "status": "confirmed",
        }
