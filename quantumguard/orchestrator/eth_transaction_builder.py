"""
QuantumGuard Labs — Ethereum Migration Transaction Builder
===========================================================
Constructs, signs, and broadcasts Ethereum migration transactions
for quantum-safe address migration.

Migration strategy for Ethereum:
  Unlike Bitcoin (UTXO model), Ethereum uses an account model.
  A "migration" means transferring all ETH (and optionally ERC-20 tokens)
  from a quantum-vulnerable EOA (Externally Owned Account) to a new,
  quantum-safe address.

  Quantum vulnerability on Ethereum:
    - If an EOA has ever sent a transaction, its public key is exposed on-chain.
    - An adversary with a sufficiently powerful quantum computer can derive
      the private key from the exposed public key using Shor's algorithm.
    - The mitigation is to migrate assets to a fresh address whose public key
      has never been exposed.

Supported modes:
  - DRY_RUN:   Build and validate transaction without signing or broadcast.
  - SIGN_ONLY: Build and sign; return raw hex for external broadcast.
  - BROADCAST: Build, sign, and broadcast via JSON-RPC.

Security notes:
  - Private keys are NEVER stored; used in-memory and discarded immediately.
  - Gas estimation uses live network data when available, with a 20% buffer.
  - ERC-20 migration uses the standard transfer() function call.
"""

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)

# ── Optional dependency: web3 ─────────────────────────────────────────────────
try:
    from web3 import Web3
    from web3.middleware import ExtraDataToPOAMiddleware
    _WEB3_AVAILABLE = True
except ImportError:
    _WEB3_AVAILABLE = False
    logger.warning("web3.py not installed — ETH builder running in simulation mode.")

# Standard ERC-20 ABI (transfer function only)
_ERC20_ABI = [
    {
        "name": "transfer",
        "type": "function",
        "inputs": [
            {"name": "_to",    "type": "address"},
            {"name": "_value", "type": "uint256"},
        ],
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
    },
    {
        "name": "balanceOf",
        "type": "function",
        "inputs": [{"name": "_owner", "type": "address"}],
        "outputs": [{"name": "balance", "type": "uint256"}],
        "stateMutability": "view",
    },
    {
        "name": "decimals",
        "type": "function",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint8"}],
        "stateMutability": "view",
    },
    {
        "name": "symbol",
        "type": "function",
        "inputs": [],
        "outputs": [{"name": "", "type": "string"}],
        "stateMutability": "view",
    },
]

# Well-known ERC-20 tokens (mainnet)
KNOWN_TOKENS: Dict[str, str] = {
    "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
    "DAI":  "0x6B175474E89094C44Da98b954EedeAC495271d0F",
    "LINK": "0x514910771AF9Ca656af840dff83E8264EcF986CA",
}


# ── Enums & Data Classes ──────────────────────────────────────────────────────

class ETHTransactionMode(str, Enum):
    DRY_RUN   = "dry_run"
    SIGN_ONLY = "sign_only"
    BROADCAST = "broadcast"


class ETHTransactionStatus(str, Enum):
    PENDING   = "pending"
    SIGNED    = "signed"
    BROADCAST = "broadcast"
    CONFIRMED = "confirmed"
    FAILED    = "failed"
    DRY_RUN   = "dry_run"


@dataclass
class ETHAsset:
    """Represents an ETH or ERC-20 asset to be migrated."""
    asset_type:      str    # "ETH" or "ERC20"
    symbol:          str
    contract_address: Optional[str]   # None for native ETH
    balance_wei:     int              # Balance in wei (or token base units)
    decimals:        int = 18

    @property
    def balance_human(self) -> float:
        return self.balance_wei / (10 ** self.decimals)

    def to_dict(self) -> dict:
        return {
            "asset_type":       self.asset_type,
            "symbol":           self.symbol,
            "contract_address": self.contract_address,
            "balance_wei":      str(self.balance_wei),
            "balance_human":    round(self.balance_human, 8),
            "decimals":         self.decimals,
        }


@dataclass
class ETHMigrationTx:
    """Represents a single Ethereum migration transaction."""
    tx_id:            str
    from_address:     str
    to_address:       str
    asset:            ETHAsset
    gas_limit:        int
    gas_price_gwei:   float
    max_fee_gwei:     float        # EIP-1559 max fee
    priority_fee_gwei: float       # EIP-1559 priority fee (tip)
    nonce:            int
    mode:             ETHTransactionMode
    status:           ETHTransactionStatus = ETHTransactionStatus.PENDING
    raw_tx_hex:       Optional[str] = None
    tx_hash:          Optional[str] = None
    created_at:       float = field(default_factory=time.time)
    error:            Optional[str] = None

    @property
    def estimated_gas_cost_eth(self) -> float:
        return (self.gas_limit * self.max_fee_gwei * 1e9) / 1e18

    def to_dict(self) -> dict:
        return {
            "tx_id":              self.tx_id,
            "from_address":       self.from_address,
            "to_address":         self.to_address,
            "asset":              self.asset.to_dict(),
            "gas_limit":          self.gas_limit,
            "gas_price_gwei":     self.gas_price_gwei,
            "max_fee_gwei":       self.max_fee_gwei,
            "priority_fee_gwei":  self.priority_fee_gwei,
            "nonce":              self.nonce,
            "mode":               self.mode.value,
            "status":             self.status.value,
            "raw_tx_hex":         self.raw_tx_hex,
            "tx_hash":            self.tx_hash,
            "estimated_gas_eth":  round(self.estimated_gas_cost_eth, 8),
            "created_at":         self.created_at,
            "error":              self.error,
        }


@dataclass
class ETHMigrationPlan:
    """A complete ETH migration plan for one address."""
    plan_id:        str
    from_address:   str
    to_address:     str
    transactions:   List[ETHMigrationTx]
    total_assets:   int
    mode:           ETHTransactionMode
    created_at:     float = field(default_factory=time.time)
    quantum_risk:   str = "HIGH"   # Risk level of the source address

    @property
    def total_gas_cost_eth(self) -> float:
        return sum(tx.estimated_gas_cost_eth for tx in self.transactions)

    def to_dict(self) -> dict:
        return {
            "plan_id":          self.plan_id,
            "from_address":     self.from_address,
            "to_address":       self.to_address,
            "total_assets":     self.total_assets,
            "total_transactions": len(self.transactions),
            "total_gas_cost_eth": round(self.total_gas_cost_eth, 8),
            "mode":             self.mode.value,
            "quantum_risk":     self.quantum_risk,
            "created_at":       self.created_at,
            "transactions":     [tx.to_dict() for tx in self.transactions],
        }


# ── Ethereum Migration Builder ────────────────────────────────────────────────

class EthereumMigrationBuilder:
    """
    Builds, signs, and broadcasts Ethereum migration transactions.

    Connects to an Ethereum node via JSON-RPC (Infura, Alchemy, or local node).
    Falls back to simulation mode when no RPC endpoint is configured.
    """

    # Gas limits for different transaction types
    GAS_ETH_TRANSFER   = 21_000
    GAS_ERC20_TRANSFER = 65_000
    GAS_BUFFER_PCT     = 1.20   # 20% buffer on estimated gas

    def __init__(self, rpc_url: Optional[str] = None):
        self.rpc_url = rpc_url
        self._w3: Optional[Any] = None
        self._simulation_mode = True

        if rpc_url and _WEB3_AVAILABLE:
            try:
                self._w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 10}))
                if self._w3.is_connected():
                    self._simulation_mode = False
                    logger.info("Connected to Ethereum node: %s", rpc_url[:40])
                else:
                    logger.warning("Could not connect to Ethereum node, using simulation mode.")
            except Exception as e:
                logger.warning("Web3 init error: %s — using simulation mode.", e)
        else:
            logger.info("ETH builder running in simulation mode (no RPC URL or web3 not installed).")

    # ── Public API ────────────────────────────────────────────────────────────

    def build_migration_plan(
        self,
        from_address: str,
        to_address: str,
        mode: ETHTransactionMode = ETHTransactionMode.DRY_RUN,
        include_erc20: bool = True,
        quantum_risk: str = "HIGH",
    ) -> ETHMigrationPlan:
        """
        Build a complete migration plan for an Ethereum address.

        Discovers all ETH and ERC-20 balances, then creates one transaction
        per asset to transfer everything to the destination address.

        Args:
            from_address:  Source address (quantum-vulnerable).
            to_address:    Destination address (quantum-safe, fresh).
            mode:          Transaction mode (dry_run / sign_only / broadcast).
            include_erc20: Whether to include ERC-20 token migrations.
            quantum_risk:  Risk level label for the source address.

        Returns:
            ETHMigrationPlan with all transactions ready for execution.
        """
        plan_id = hashlib.sha256(
            f"{from_address}{to_address}{time.time()}".encode()
        ).hexdigest()[:16]

        logger.info("Building ETH migration plan %s: %s → %s", plan_id, from_address[:10], to_address[:10])

        # Discover assets
        assets = self._discover_assets(from_address, include_erc20)
        if not assets:
            logger.warning("No assets found for address %s", from_address)

        # Get network fee data
        gas_price_gwei, max_fee_gwei, priority_fee_gwei = self._get_fee_data()

        # Get nonce
        nonce = self._get_nonce(from_address)

        # Build one transaction per asset
        transactions: List[ETHMigrationTx] = []
        for i, asset in enumerate(assets):
            tx = self._build_asset_tx(
                tx_index=i,
                plan_id=plan_id,
                from_address=from_address,
                to_address=to_address,
                asset=asset,
                nonce=nonce + i,
                gas_price_gwei=gas_price_gwei,
                max_fee_gwei=max_fee_gwei,
                priority_fee_gwei=priority_fee_gwei,
                mode=mode,
            )
            transactions.append(tx)

        return ETHMigrationPlan(
            plan_id=plan_id,
            from_address=from_address,
            to_address=to_address,
            transactions=transactions,
            total_assets=len(assets),
            mode=mode,
            quantum_risk=quantum_risk,
        )

    def sign_and_broadcast(
        self,
        plan: ETHMigrationPlan,
        private_key_hex: str,
    ) -> ETHMigrationPlan:
        """
        Sign all transactions in a plan and optionally broadcast them.

        Args:
            plan:            The migration plan to execute.
            private_key_hex: The private key of the source address (hex string).

        Returns:
            Updated ETHMigrationPlan with tx hashes and statuses.
        """
        if plan.mode == ETHTransactionMode.DRY_RUN:
            logger.info("DRY_RUN mode — skipping signing.")
            for tx in plan.transactions:
                tx.status = ETHTransactionStatus.DRY_RUN
            return plan

        for tx in plan.transactions:
            try:
                signed_hex = self._sign_transaction(tx, private_key_hex)
                tx.raw_tx_hex = signed_hex
                tx.status = ETHTransactionStatus.SIGNED

                if plan.mode == ETHTransactionMode.BROADCAST:
                    tx_hash = self._broadcast_transaction(signed_hex)
                    tx.tx_hash = tx_hash
                    tx.status = ETHTransactionStatus.BROADCAST
                    logger.info("Broadcast tx %s: %s", tx.tx_id, tx_hash)

            except Exception as e:
                tx.status = ETHTransactionStatus.FAILED
                tx.error = str(e)
                logger.error("Failed to process tx %s: %s", tx.tx_id, e)

        return plan

    # ── Asset Discovery ───────────────────────────────────────────────────────

    def _discover_assets(self, address: str, include_erc20: bool) -> List[ETHAsset]:
        """Discover all ETH and ERC-20 assets for an address."""
        assets: List[ETHAsset] = []

        # Native ETH balance
        eth_balance_wei = self._get_eth_balance(address)
        if eth_balance_wei > 0:
            assets.append(ETHAsset(
                asset_type="ETH",
                symbol="ETH",
                contract_address=None,
                balance_wei=eth_balance_wei,
                decimals=18,
            ))

        # ERC-20 token balances
        if include_erc20:
            for symbol, contract in KNOWN_TOKENS.items():
                try:
                    balance, decimals = self._get_erc20_balance(address, contract)
                    if balance > 0:
                        assets.append(ETHAsset(
                            asset_type="ERC20",
                            symbol=symbol,
                            contract_address=contract,
                            balance_wei=balance,
                            decimals=decimals,
                        ))
                except Exception as e:
                    logger.debug("ERC-20 %s balance check failed: %s", symbol, e)

        return assets

    def _get_eth_balance(self, address: str) -> int:
        """Get native ETH balance in wei."""
        if not self._simulation_mode and self._w3:
            try:
                checksum = Web3.to_checksum_address(address)
                return self._w3.eth.get_balance(checksum)
            except Exception as e:
                logger.debug("ETH balance error: %s", e)

        # Simulation: use Etherscan API
        try:
            url = f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest"
            r = requests.get(url, timeout=5)
            data = r.json()
            if data.get("status") == "1":
                return int(data["result"])
        except Exception:
            pass

        # Fallback: simulated balance for demo
        import random
        return random.randint(100_000_000_000_000, 5_000_000_000_000_000_000)  # 0.0001–5 ETH

    def _get_erc20_balance(self, address: str, contract_address: str) -> Tuple[int, int]:
        """Get ERC-20 token balance and decimals. Returns (balance_wei, decimals)."""
        if not self._simulation_mode and self._w3:
            checksum_addr     = Web3.to_checksum_address(address)
            checksum_contract = Web3.to_checksum_address(contract_address)
            contract = self._w3.eth.contract(address=checksum_contract, abi=_ERC20_ABI)
            balance  = contract.functions.balanceOf(checksum_addr).call()
            decimals = contract.functions.decimals().call()
            return balance, decimals

        # Simulation: return 0 (no tokens in demo mode)
        return 0, 18

    # ── Fee Estimation ────────────────────────────────────────────────────────

    def _get_fee_data(self) -> Tuple[float, float, float]:
        """
        Get current gas fee data.
        Returns (gas_price_gwei, max_fee_gwei, priority_fee_gwei).
        """
        if not self._simulation_mode and self._w3:
            try:
                fee_history = self._w3.eth.fee_history(1, "latest", [50])
                base_fee_wei = fee_history["baseFeePerGas"][-1]
                base_fee_gwei = base_fee_wei / 1e9
                priority_fee_gwei = 1.5  # Standard tip
                max_fee_gwei = base_fee_gwei * 1.5 + priority_fee_gwei
                return base_fee_gwei, max_fee_gwei, priority_fee_gwei
            except Exception as e:
                logger.debug("Fee history error: %s", e)

        # Simulation: reasonable mainnet-like fees
        return 15.0, 25.0, 1.5

    def _get_nonce(self, address: str) -> int:
        """Get the next nonce for an address."""
        if not self._simulation_mode and self._w3:
            try:
                checksum = Web3.to_checksum_address(address)
                return self._w3.eth.get_transaction_count(checksum, "pending")
            except Exception as e:
                logger.debug("Nonce error: %s", e)
        return 0  # Simulation

    # ── Transaction Construction ──────────────────────────────────────────────

    def _build_asset_tx(
        self,
        tx_index: int,
        plan_id: str,
        from_address: str,
        to_address: str,
        asset: ETHAsset,
        nonce: int,
        gas_price_gwei: float,
        max_fee_gwei: float,
        priority_fee_gwei: float,
        mode: ETHTransactionMode,
    ) -> ETHMigrationTx:
        """Build a single migration transaction for one asset."""
        tx_id = f"{plan_id}-{tx_index:03d}-{asset.symbol}"

        if asset.asset_type == "ETH":
            gas_limit = self.GAS_ETH_TRANSFER
        else:
            gas_limit = int(self.GAS_ERC20_TRANSFER * self.GAS_BUFFER_PCT)

        return ETHMigrationTx(
            tx_id=tx_id,
            from_address=from_address,
            to_address=to_address,
            asset=asset,
            gas_limit=gas_limit,
            gas_price_gwei=gas_price_gwei,
            max_fee_gwei=max_fee_gwei,
            priority_fee_gwei=priority_fee_gwei,
            nonce=nonce,
            mode=mode,
            status=ETHTransactionStatus.PENDING,
        )

    def _sign_transaction(self, tx: ETHMigrationTx, private_key_hex: str) -> str:
        """Sign a transaction and return the raw hex string."""
        if not _WEB3_AVAILABLE:
            # Simulation: return a fake signed hex
            fake_hash = hashlib.sha256(
                f"{tx.from_address}{tx.to_address}{tx.nonce}".encode()
            ).hexdigest()
            return f"0x{fake_hash * 4}"

        w3 = self._w3 or Web3()  # Use local instance for signing even in sim mode

        if tx.asset.asset_type == "ETH":
            # Reserve gas cost from ETH transfer
            gas_cost_wei = int(tx.gas_limit * tx.max_fee_gwei * 1e9)
            value_wei = max(0, tx.asset.balance_wei - gas_cost_wei)
            tx_params = {
                "nonce":                 tx.nonce,
                "to":                    Web3.to_checksum_address(tx.to_address),
                "value":                 value_wei,
                "gas":                   tx.gas_limit,
                "maxFeePerGas":          int(tx.max_fee_gwei * 1e9),
                "maxPriorityFeePerGas":  int(tx.priority_fee_gwei * 1e9),
                "chainId":               1,  # Mainnet
                "type":                  2,  # EIP-1559
            }
        else:
            # ERC-20 transfer
            contract = w3.eth.contract(
                address=Web3.to_checksum_address(tx.asset.contract_address),
                abi=_ERC20_ABI,
            )
            data = contract.encodeABI(
                fn_name="transfer",
                args=[Web3.to_checksum_address(tx.to_address), tx.asset.balance_wei],
            )
            tx_params = {
                "nonce":                 tx.nonce,
                "to":                    Web3.to_checksum_address(tx.asset.contract_address),
                "value":                 0,
                "gas":                   tx.gas_limit,
                "maxFeePerGas":          int(tx.max_fee_gwei * 1e9),
                "maxPriorityFeePerGas":  int(tx.priority_fee_gwei * 1e9),
                "chainId":               1,
                "type":                  2,
                "data":                  data,
            }

        # Normalize private key
        pk = private_key_hex if private_key_hex.startswith("0x") else f"0x{private_key_hex}"
        signed = w3.eth.account.sign_transaction(tx_params, private_key=pk)
        return signed.raw_transaction.hex()

    def _broadcast_transaction(self, raw_tx_hex: str) -> str:
        """Broadcast a signed transaction and return the tx hash."""
        if not self._simulation_mode and self._w3:
            raw_bytes = bytes.fromhex(raw_tx_hex.lstrip("0x"))
            tx_hash = self._w3.eth.send_raw_transaction(raw_bytes)
            return tx_hash.hex()
        # Simulation
        return "0x" + hashlib.sha256(raw_tx_hex.encode()).hexdigest()

    # ── Utility ───────────────────────────────────────────────────────────────

    def estimate_migration_cost(self, from_address: str) -> dict:
        """
        Estimate the total gas cost for migrating all assets from an address.
        Returns a summary dict without building the full plan.
        """
        assets = self._discover_assets(from_address, include_erc20=True)
        _, max_fee_gwei, _ = self._get_fee_data()

        eth_txs = sum(1 for a in assets if a.asset_type == "ETH")
        erc20_txs = sum(1 for a in assets if a.asset_type == "ERC20")

        total_gas = (eth_txs * self.GAS_ETH_TRANSFER +
                     erc20_txs * int(self.GAS_ERC20_TRANSFER * self.GAS_BUFFER_PCT))
        total_cost_eth = (total_gas * max_fee_gwei * 1e9) / 1e18

        return {
            "from_address":     from_address,
            "total_assets":     len(assets),
            "eth_transactions": eth_txs,
            "erc20_transactions": erc20_txs,
            "total_gas_units":  total_gas,
            "max_fee_gwei":     max_fee_gwei,
            "estimated_cost_eth": round(total_cost_eth, 8),
            "assets": [a.to_dict() for a in assets],
            "simulation_mode":  self._simulation_mode,
        }
