"""
QuantumGuard Labs - Reports API Router
Generates PDF and JSON compliance reports.
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import sys, os, tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from quantumguard.analyzer.bitcoin_analyzer import BitcoinQuantumAnalyzer
from quantumguard.orchestrator.migration_planner import MigrationPlanner
from quantumguard.orchestrator.policy_engine import POLICY_DRY_RUN
from quantumguard.auditor.proof_generator import ProofGenerator, AuditEventType
from quantumguard.auditor.pdf_report import generate_pdf_report
from quantumguard.core.blockchain_connector import MockBitcoinConnector

router = APIRouter()


@router.get("/pdf", summary="Generate and download a PDF compliance report")
async def generate_pdf(
    utxo_count: int = Query(200, ge=10, le=500, description="Number of UTXOs to analyze"),
    org_id: str = Query("DEMO_ORG_001", description="Organization identifier"),
):
    """
    Runs a full analysis pipeline and returns a professional PDF compliance report
    suitable for submission to auditors, boards, or regulators.
    """
    try:
        connector = MockBitcoinConnector()
        utxos = connector.get_portfolio_utxos(count=utxo_count)

        analyzer = BitcoinQuantumAnalyzer()
        report = analyzer.analyze_portfolio(utxos)

        planner = MigrationPlanner()
        plan = planner.create_plan(report, POLICY_DRY_RUN, "bc1p_quantum_safe_address")

        proof_gen = ProofGenerator(organization_id=org_id)
        proof_gen.log_event(AuditEventType.RISK_ANALYSIS_COMPLETED, details={"total_utxos": report.total_utxos})
        proof_gen.log_event(AuditEventType.MIGRATION_PLAN_CREATED, details={"plan_id": plan.plan_id})
        projected_score = min(100.0, report.quantum_readiness_score + 35.0)
        proof = proof_gen.generate_proof(
            initial_readiness_score=report.quantum_readiness_score,
            final_readiness_score=projected_score,
            total_utxos_analyzed=report.total_utxos,
            total_utxos_migrated=plan.total_utxos,
            total_value_migrated_btc=plan.total_value_btc,
            risk_summary={
                "critical": report.critical_count,
                "high": report.high_count,
                "medium": report.medium_count,
                "low": report.low_count,
            },
        )

        # Write PDF to a temp file
        tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False, prefix="qg_report_")
        tmp.close()
        generate_pdf_report(report, plan, proof, output_path=tmp.name, org_id=org_id)

        return FileResponse(
            path=tmp.name,
            media_type="application/pdf",
            filename=f"QuantumGuard_Compliance_Report_{org_id}.pdf",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/json", summary="Generate a full JSON compliance report")
async def generate_json_report(
    utxo_count: int = Query(200, ge=10, le=500),
    org_id: str = Query("DEMO_ORG_001"),
):
    """Returns the full compliance report as JSON."""
    try:
        connector = MockBitcoinConnector()
        utxos = connector.get_portfolio_utxos(count=utxo_count)
        analyzer = BitcoinQuantumAnalyzer()
        report = analyzer.analyze_portfolio(utxos)
        planner = MigrationPlanner()
        plan = planner.create_plan(report, POLICY_DRY_RUN, "bc1p_quantum_safe_address")
        proof_gen = ProofGenerator(organization_id=org_id)
        proof_gen.log_event(AuditEventType.RISK_ANALYSIS_COMPLETED, details={"total_utxos": report.total_utxos})
        proof_gen.log_event(AuditEventType.MIGRATION_PLAN_CREATED, details={"plan_id": plan.plan_id})
        projected_score = min(100.0, report.quantum_readiness_score + 35.0)
        proof = proof_gen.generate_proof(
            initial_readiness_score=report.quantum_readiness_score,
            final_readiness_score=projected_score,
            total_utxos_analyzed=report.total_utxos,
            total_utxos_migrated=plan.total_utxos,
            total_value_migrated_btc=plan.total_value_btc,
            risk_summary={
                "critical": report.critical_count,
                "high": report.high_count,
                "medium": report.medium_count,
                "low": report.low_count,
            },
        )

        return {
            "organization_id": org_id,
            "report_id": proof.proof_id,
            "generated_at": proof.generated_at,
            "risk_summary": {
                "total_utxos": report.total_utxos,
                "quantum_readiness_score": round(report.quantum_readiness_score, 2),
                "projected_score_after_migration": round(proof.final_readiness_score, 2),
                "critical_count": report.critical_count,
                "high_count": report.high_count,
                "medium_count": report.medium_count,
                "low_count": report.low_count,
                "total_value_btc": round(report.total_value_btc, 8),
                "critical_value_btc": round(report.critical_value_btc, 8),
                "high_value_btc": round(report.high_value_btc, 8),
            },
            "migration_plan": {
                "plan_id": plan.plan_id,
                "total_batches": plan.total_batches,
                "total_utxos": plan.total_utxos,
                "total_value_btc": round(plan.total_value_btc, 8),
                "estimated_fees_btc": round(plan.estimated_fees_btc, 8),
            },
            "audit_log_integrity": proof.audit_log_hash,
            "audit_entries": len(proof.audit_log),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
