"""
QuantumGuard Labs - Migration Plan API Router
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from quantumguard.analyzer.bitcoin_analyzer import BitcoinQuantumAnalyzer
from quantumguard.analyzer.models import RiskLevel
from quantumguard.orchestrator.migration_planner import MigrationPlanner
from quantumguard.orchestrator.policy_engine import (
    MigrationPolicy, ApprovalMode, ExecutionMode,
    POLICY_STANDARD, POLICY_EMERGENCY, POLICY_DRY_RUN,
)
from quantumguard.core.blockchain_connector import MockBitcoinConnector

router = APIRouter()

POLICIES = {
    "standard":  POLICY_STANDARD,
    "emergency": POLICY_EMERGENCY,
    "dry_run":   POLICY_DRY_RUN,
}


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


@router.post("/plan", response_model=MigrationPlanResponse, summary="Generate a migration plan")
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
