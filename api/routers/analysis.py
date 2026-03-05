"""
QuantumGuard Labs - Risk Analysis API Router
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from quantumguard.analyzer.bitcoin_analyzer import BitcoinQuantumAnalyzer
from quantumguard.analyzer.models import RiskLevel, ScriptType
from quantumguard.core.blockchain_connector import MockBitcoinConnector, BlockstreamTestnetConnector

router = APIRouter()


class AnalysisRequest(BaseModel):
    source: str = Field("mock", description="Data source: 'mock' or 'testnet'")
    address: Optional[str] = Field(None, description="Bitcoin address (for testnet)")
    utxo_count: int = Field(200, ge=1, le=1000, description="Number of mock UTXOs to generate")


class UTXOResult(BaseModel):
    txid: str
    vout: int
    address: str
    value_btc: float
    script_type: str
    risk_level: str
    risk_score: float
    migration_priority: int
    risk_reasons: list[str]


class AnalysisResponse(BaseModel):
    total_utxos: int
    quantum_readiness_score: float
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    safe_count: int
    critical_value_btc: float
    high_value_btc: float
    total_value_btc: float
    assessments: list[UTXOResult]


@router.post("/run", response_model=AnalysisResponse, summary="Run quantum risk analysis on a portfolio")
async def run_analysis(req: AnalysisRequest):
    """
    Analyze a portfolio of UTXOs for quantum attack exposure.
    Returns a full risk report with per-UTXO assessments and a portfolio-level
    Quantum Readiness Score.
    """
    try:
        if req.source == "testnet" and req.address:
            connector = BlockstreamTestnetConnector()
            utxos = connector.get_utxos_for_address(req.address)
            if not utxos:
                raise HTTPException(status_code=404, detail=f"No UTXOs found for address: {req.address}")
        else:
            connector = MockBitcoinConnector()
            utxos = connector.get_portfolio_utxos(count=req.utxo_count)

        analyzer = BitcoinQuantumAnalyzer()
        report = analyzer.analyze_portfolio(utxos)

        assessments = [
            UTXOResult(
                txid=a.utxo.txid,
                vout=a.utxo.vout,
                address=a.utxo.address,
                value_btc=a.utxo.value_btc,
                script_type=a.utxo.script_type.value,
                risk_level=a.risk_level.value,
                risk_score=float(a.risk_score),
                migration_priority=a.migration_priority,
                risk_reasons=a.risk_reasons,
            )
            for a in report.assessments
        ]

        return AnalysisResponse(
            total_utxos=report.total_utxos,
            quantum_readiness_score=round(report.quantum_readiness_score, 2),
            critical_count=report.critical_count,
            high_count=report.high_count,
            medium_count=report.medium_count,
            low_count=report.low_count,
            safe_count=report.safe_count,
            critical_value_btc=round(report.critical_value_btc, 8),
            high_value_btc=round(report.high_value_btc, 8),
            total_value_btc=round(report.total_value_btc, 8),
            assessments=assessments,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/demo", response_model=AnalysisResponse, summary="Run demo analysis with mock data")
async def demo_analysis(utxo_count: int = Query(200, ge=10, le=1000)):
    """Quick demo endpoint using mock data — no parameters required."""
    return await run_analysis(AnalysisRequest(source="mock", utxo_count=utxo_count))
