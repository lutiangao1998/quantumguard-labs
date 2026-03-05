"""
QuantumGuard Labs - Example: Full Portfolio Risk Analysis
==========================================================
This script demonstrates the complete end-to-end workflow of the QMP platform:

  1. Connect to a (mock) Bitcoin node and fetch UTXOs.
  2. Run the Quantum Risk Analyzer to assess each UTXO.
  3. Generate a Migration Plan using the Standard policy.
  4. Log all events to the tamper-evident audit trail.
  5. Generate a Quantum Readiness Proof and compliance report.

Run this script from the project root:
  $ python3 scripts/run_analysis.py
"""

import json
import logging
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quantumguard.analyzer.bitcoin_analyzer import BitcoinQuantumAnalyzer
from quantumguard.auditor.proof_generator import AuditEventType, ProofGenerator
from quantumguard.auditor.reporting import ReportGenerator
from quantumguard.core.blockchain_connector import MockBitcoinConnector
from quantumguard.orchestrator.migration_planner import MigrationPlanner
from quantumguard.orchestrator.policy_engine import POLICY_STANDARD, POLICY_DRY_RUN

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("qmp.demo")


def main():
    print("=" * 70)
    print("  QuantumGuard Labs - Quantum Migration Platform (QMP)")
    print("  Full Portfolio Risk Analysis Demo")
    print("=" * 70)
    print()

    # ----------------------------------------------------------------
    # Step 1: Initialize Components
    # ----------------------------------------------------------------
    print("[1/5] Initializing platform components...")
    connector = MockBitcoinConnector(seed=2026)
    analyzer = BitcoinQuantumAnalyzer()
    planner = MigrationPlanner()
    proof_gen = ProofGenerator(organization_id="DEMO_CUSTODY_CORP_001")
    reporter = ReportGenerator()

    # ----------------------------------------------------------------
    # Step 2: Fetch UTXOs and Run Risk Analysis
    # ----------------------------------------------------------------
    print("[2/5] Fetching UTXO portfolio from blockchain (mock data)...")
    proof_gen.log_event(
        AuditEventType.RISK_ANALYSIS_STARTED,
        actor="system",
        details={"source": "MockBitcoinConnector", "utxo_limit": 200},
    )

    utxos = connector.get_utxo_set(limit=200)
    print(f"      -> Fetched {len(utxos)} UTXOs.")

    print("[3/5] Running quantum risk analysis...")
    risk_report = analyzer.analyze_portfolio(utxos)

    proof_gen.log_event(
        AuditEventType.RISK_ANALYSIS_COMPLETED,
        actor="system",
        details={
            "total_utxos": risk_report.total_utxos,
            "quantum_readiness_score": risk_report.quantum_readiness_score,
            "critical_count": risk_report.critical_count,
            "high_count": risk_report.high_count,
        },
    )

    print(f"      -> Analysis complete.")
    print(f"      -> Quantum Readiness Score: {risk_report.quantum_readiness_score:.1f}/100")
    print(f"      -> CRITICAL: {risk_report.critical_count} UTXOs | HIGH: {risk_report.high_count} UTXOs")
    print()

    # ----------------------------------------------------------------
    # Step 3: Create Migration Plan
    # ----------------------------------------------------------------
    print("[4/5] Generating migration plan (Standard Policy, Dry Run)...")
    # Use DRY_RUN policy for demo - no real transactions will be broadcast
    migration_plan = planner.create_plan(
        risk_report=risk_report,
        policy=POLICY_DRY_RUN,
        destination_address="bc1p_DEMO_QUANTUM_SAFE_ADDRESS_PLACEHOLDER",
    )

    proof_gen.log_event(
        AuditEventType.MIGRATION_PLAN_CREATED,
        actor="system",
        details={
            "plan_id": migration_plan.plan_id,
            "policy": migration_plan.policy_name,
            "total_batches": migration_plan.total_batches,
            "total_utxos": migration_plan.total_utxos,
            "total_value_btc": migration_plan.total_value_btc,
        },
    )

    print(f"      -> Plan ID: {migration_plan.plan_id}")
    print(f"      -> Total batches: {migration_plan.total_batches}")
    print(f"      -> Total UTXOs to migrate: {migration_plan.total_utxos}")
    print(f"      -> Total value to migrate: {migration_plan.total_value_btc:.8f} BTC")
    print(f"      -> Estimated fees: {migration_plan.estimated_fees_btc:.8f} BTC")
    print()

    # ----------------------------------------------------------------
    # Step 4: Generate Compliance Report
    # ----------------------------------------------------------------
    print("[5/5] Generating compliance report and quantum readiness proof...")

    # Simulate post-migration score improvement for demo
    simulated_final_score = min(100.0, risk_report.quantum_readiness_score + 35.0)

    proof = proof_gen.generate_proof(
        initial_readiness_score=risk_report.quantum_readiness_score,
        final_readiness_score=simulated_final_score,
        total_utxos_analyzed=risk_report.total_utxos,
        total_utxos_migrated=migration_plan.total_utxos,
        total_value_migrated_btc=migration_plan.total_value_btc,
        risk_summary={
            "CRITICAL": risk_report.critical_count,
            "HIGH": risk_report.high_count,
            "MEDIUM": risk_report.medium_count,
            "LOW": risk_report.low_count,
            "SAFE": risk_report.safe_count,
        },
    )

    # Verify audit log integrity
    is_valid = proof_gen.verify_log_integrity()
    print(f"      -> Audit log integrity: {'✅ VALID' if is_valid else '❌ COMPROMISED'}")
    print(f"      -> Proof ID: {proof.proof_id}")
    print()

    # Generate and print the executive summary
    summary = reporter.generate_executive_summary(
        risk_report=risk_report,
        proof=proof,
        organization_name="Demo Custody Corp",
    )

    # Save outputs
    output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    os.makedirs(output_dir, exist_ok=True)

    summary_path = os.path.join(output_dir, "executive_summary.md")
    with open(summary_path, "w") as f:
        f.write(summary)

    proof_path = os.path.join(output_dir, "quantum_readiness_proof.json")
    with open(proof_path, "w") as f:
        f.write(json.dumps(proof.to_dict(), indent=2))

    json_report_path = os.path.join(output_dir, "risk_report.json")
    with open(json_report_path, "w") as f:
        f.write(reporter.generate_json_report(risk_report))

    print("=" * 70)
    print("  DEMO COMPLETE - Output files saved to ./output/")
    print(f"  - Executive Summary:       output/executive_summary.md")
    print(f"  - Quantum Readiness Proof: output/quantum_readiness_proof.json")
    print(f"  - Full Risk Report (JSON): output/risk_report.json")
    print("=" * 70)


if __name__ == "__main__":
    main()
