"""
QuantumGuard Labs - Migration Plan API Router
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from quantumguard.analyzer.bitcoin_analyzer import BitcoinQuantumAnalyzer
from quantumguard.analyzer.models import RiskLevel
from quantumguard.orchestrator.migration_planner import MigrationPlanner
from quantumguard.orchestrator.policy_engine import (
    MigrationPolicy, ApprovalMode, ExecutionMode,
    POLICY_STANDARD, POLICY_EMERGENCY, POLICY_DRY_RUN,
)
from quantumguard.orchestrator.eth_transaction_builder import (
    EthereumMigrationBuilder, ETHTransactionMode,
)
from quantumguard.core.blockchain_connector import MockBitcoinConnector

router = APIRouter()

POLICIES = {
    "standard":  POLICY_STANDARD,
    "emergency": POLICY_EMERGENCY,
    "dry_run":   POLICY_DRY_RUN,
}


# ── Bitcoin Migration Models ──────────────────────────────────────────────────

class MigrationRequest(BaseModel):
    policy: str = Field("dry_run", description="Policy name: standard | emergency | dry_run")
    destination_address: str = Field(
        "bc1p_quantum_safe_destination_address",
        description="Destination quantum-safe address"
    )
    utxo_count: int = Field(200, ge=10, le=1000)


class BatchSummary(BaseModel):
    batch_id: str
    batch_number: int
    utxo_count: int
    total_value_btc: float
    status: str
    risk_levels: list[str]


class MigrationPlanResponse(BaseModel):
    plan_id: str
    policy_name: str
    total_batches: int
    total_utxos: int
    total_value_btc: float
    estimated_fees_btc: float
    destination_address: str
    batches: list[BatchSummary]


# ── Ethereum Migration Models ─────────────────────────────────────────────────

class ETHMigrationRequest(BaseModel):
    from_address: str = Field(..., description="Source Ethereum address (quantum-vulnerable)")
    to_address: str = Field(..., description="Destination Ethereum address (quantum-safe, fresh)")
    mode: str = Field("dry_run", description="Transaction mode: dry_run | sign_only | broadcast")
    include_erc20: bool = Field(True, description="Include ERC-20 token migrations")
    rpc_url: Optional[str] = Field(None, description="Ethereum JSON-RPC URL (optional, uses simulation if omitted)")


class ETHAssetResponse(BaseModel):
    asset_type: str
    symbol: str
    contract_address: Optional[str]
    balance_wei: str
    balance_human: float
    decimals: int


class ETHTxResponse(BaseModel):
    tx_id: str
    from_address: str
    to_address: str
    asset: ETHAssetResponse
    gas_limit: int
    max_fee_gwei: float
    priority_fee_gwei: float
    nonce: int
    mode: str
    status: str
    raw_tx_hex: Optional[str]
    tx_hash: Optional[str]
    estimated_gas_eth: float
    error: Optional[str]


class ETHMigrationPlanResponse(BaseModel):
    plan_id: str
    from_address: str
    to_address: str
    total_assets: int
    total_transactions: int
    total_gas_cost_eth: float
    mode: str
    quantum_risk: str
    transactions: List[ETHTxResponse]


class ETHCostEstimateResponse(BaseModel):
    from_address: str
    total_assets: int
    eth_transactions: int
    erc20_transactions: int
    total_gas_units: int
    max_fee_gwei: float
    estimated_cost_eth: float
    assets: List[ETHAssetResponse]
    simulation_mode: bool


# ── Bitcoin Migration Endpoints ───────────────────────────────────────────────

@router.post("/plan", response_model=MigrationPlanResponse, summary="Generate a BTC migration plan")
async def create_migration_plan(req: MigrationRequest):
    """
    Generate a policy-driven migration plan from a risk analysis.
    Returns a structured batch schedule ready for approval and execution.
    """
    policy = POLICIES.get(req.policy)
    if not policy:
        raise HTTPException(status_code=400, detail=f"Unknown policy '{req.policy}'. Use: standard, emergency, dry_run")

    try:
        connector = MockBitcoinConnector()
        utxos = connector.get_portfolio_utxos(count=req.utxo_count)
        analyzer = BitcoinQuantumAnalyzer()
        report = analyzer.analyze_portfolio(utxos)

        planner = MigrationPlanner()
        plan = planner.create_plan(report, policy, req.destination_address)

        batches = []
        for idx, b in enumerate(plan.batches, start=1):
            risk_levels = list({a.risk_level.value for a in b.assessments})
            batches.append(BatchSummary(
                batch_id=b.batch_id,
                batch_number=idx,
                utxo_count=len(b.assessments),
                total_value_btc=round(b.total_value_btc, 8),
                status=b.status.value,
                risk_levels=risk_levels,
            ))

        return MigrationPlanResponse(
            plan_id=plan.plan_id,
            policy_name=plan.policy_name,
            total_batches=plan.total_batches,
            total_utxos=plan.total_utxos,
            total_value_btc=round(plan.total_value_btc, 8),
            estimated_fees_btc=round(plan.estimated_fees_btc, 8),
            destination_address=req.destination_address,
            batches=batches,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/policies", summary="List available migration policies")
async def list_policies():
    return {
        "policies": [
            {"name": "dry_run",   "description": "Simulation only — no real transactions. Migrates MEDIUM risk and above.", "min_risk": "MEDIUM"},
            {"name": "standard",  "description": "Standard migration with manual approval. Migrates HIGH risk and above.", "min_risk": "HIGH"},
            {"name": "emergency", "description": "Emergency fast-track. Migrates CRITICAL risk only.", "min_risk": "CRITICAL"},
        ]
    }


# ── Ethereum Migration Endpoints ──────────────────────────────────────────────

@router.post(
    "/ethereum/plan",
    response_model=ETHMigrationPlanResponse,
    summary="Build an Ethereum migration plan",
    description="""
Build a complete quantum-safe migration plan for an Ethereum address.

Discovers all ETH and ERC-20 token balances, then creates one transaction
per asset to transfer everything to the destination address.

**Quantum risk context:** If an EOA has ever sent a transaction, its public key
is exposed on-chain. A sufficiently powerful quantum computer can derive the
private key using Shor's algorithm. Migration to a fresh address mitigates this risk.

Set `mode=dry_run` (default) to preview the plan without signing.
Set `mode=sign_only` to sign transactions (requires private key via separate endpoint).
""",
)
async def create_eth_migration_plan(req: ETHMigrationRequest):
    """Build an Ethereum migration plan (dry_run by default)."""
    mode_map = {
        "dry_run":   ETHTransactionMode.DRY_RUN,
        "sign_only": ETHTransactionMode.SIGN_ONLY,
        "broadcast": ETHTransactionMode.BROADCAST,
    }
    mode = mode_map.get(req.mode)
    if not mode:
        raise HTTPException(status_code=400, detail=f"Invalid mode '{req.mode}'. Use: dry_run, sign_only, broadcast")

    try:
        builder = EthereumMigrationBuilder(rpc_url=req.rpc_url)
        plan = builder.build_migration_plan(
            from_address=req.from_address,
            to_address=req.to_address,
            mode=mode,
            include_erc20=req.include_erc20,
        )
        plan_dict = plan.to_dict()

        txs = []
        for tx in plan_dict["transactions"]:
            asset = tx["asset"]
            txs.append(ETHTxResponse(
                tx_id=tx["tx_id"],
                from_address=tx["from_address"],
                to_address=tx["to_address"],
                asset=ETHAssetResponse(
                    asset_type=asset["asset_type"],
                    symbol=asset["symbol"],
                    contract_address=asset.get("contract_address"),
                    balance_wei=str(asset["balance_wei"]),
                    balance_human=asset["balance_human"],
                    decimals=asset["decimals"],
                ),
                gas_limit=tx["gas_limit"],
                max_fee_gwei=tx["max_fee_gwei"],
                priority_fee_gwei=tx["priority_fee_gwei"],
                nonce=tx["nonce"],
                mode=tx["mode"],
                status=tx["status"],
                raw_tx_hex=tx.get("raw_tx_hex"),
                tx_hash=tx.get("tx_hash"),
                estimated_gas_eth=tx["estimated_gas_eth"],
                error=tx.get("error"),
            ))

        return ETHMigrationPlanResponse(
            plan_id=plan_dict["plan_id"],
            from_address=plan_dict["from_address"],
            to_address=plan_dict["to_address"],
            total_assets=plan_dict["total_assets"],
            total_transactions=plan_dict["total_transactions"],
            total_gas_cost_eth=plan_dict["total_gas_cost_eth"],
            mode=plan_dict["mode"],
            quantum_risk=plan_dict["quantum_risk"],
            transactions=txs,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/ethereum/estimate",
    response_model=ETHCostEstimateResponse,
    summary="Estimate ETH migration gas cost",
)
async def estimate_eth_migration(
    address: str,
    rpc_url: Optional[str] = None,
):
    """
    Estimate the total gas cost for migrating all assets from an Ethereum address.
    Returns asset discovery results and fee estimates without building a full plan.
    """
    try:
        builder = EthereumMigrationBuilder(rpc_url=rpc_url)
        est = builder.estimate_migration_cost(address)
        assets = [
            ETHAssetResponse(
                asset_type=a["asset_type"],
                symbol=a["symbol"],
                contract_address=a.get("contract_address"),
                balance_wei=str(a["balance_wei"]),
                balance_human=a["balance_human"],
                decimals=a["decimals"],
            )
            for a in est["assets"]
        ]
        return ETHCostEstimateResponse(
            from_address=est["from_address"],
            total_assets=est["total_assets"],
            eth_transactions=est["eth_transactions"],
            erc20_transactions=est["erc20_transactions"],
            total_gas_units=est["total_gas_units"],
            max_fee_gwei=est["max_fee_gwei"],
            estimated_cost_eth=est["estimated_cost_eth"],
            assets=assets,
            simulation_mode=est["simulation_mode"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
