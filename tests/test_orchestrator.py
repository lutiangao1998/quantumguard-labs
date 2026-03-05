"""
QuantumGuard Labs - Unit Tests: Migration Orchestrator
=======================================================
Tests for the migration planning and policy engine modules.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quantumguard.analyzer.models import RiskLevel, RiskReport, ScriptType, UTXO, RiskAssessment
from quantumguard.orchestrator.migration_planner import BatchStatus, MigrationPlanner
from quantumguard.orchestrator.policy_engine import (
    ApprovalMode,
    ExecutionMode,
    MigrationPolicy,
    POLICY_DRY_RUN,
    POLICY_EMERGENCY,
    POLICY_STANDARD,
)


def _make_assessment(risk_level: RiskLevel, value_btc: float, idx: int = 0) -> RiskAssessment:
    """Helper to create a mock RiskAssessment."""
    priority_map = {
        RiskLevel.CRITICAL: 1,
        RiskLevel.HIGH: 2,
        RiskLevel.MEDIUM: 3,
        RiskLevel.LOW: 4,
        RiskLevel.SAFE: 5,
    }
    utxo = UTXO(
        txid=f"{'a' * 63}{idx}",
        vout=0,
        address=f"addr_{idx}",
        value_btc=value_btc,
        script_type=ScriptType.P2PKH,
    )
    return RiskAssessment(
        utxo=utxo,
        risk_level=risk_level,
        risk_score=80 if risk_level == RiskLevel.CRITICAL else 50,
        migration_priority=priority_map[risk_level],
    )


def _make_report(assessments: list[RiskAssessment]) -> RiskReport:
    """Helper to create a mock RiskReport from a list of assessments."""
    report = RiskReport(
        total_utxos=len(assessments),
        assessments=assessments,
        total_value_btc=sum(a.utxo.value_btc for a in assessments),
    )
    for a in assessments:
        if a.risk_level == RiskLevel.CRITICAL:
            report.critical_count += 1
            report.critical_value_btc += a.utxo.value_btc
        elif a.risk_level == RiskLevel.HIGH:
            report.high_count += 1
            report.high_value_btc += a.utxo.value_btc
    return report


class TestMigrationPolicy(unittest.TestCase):
    """Tests for the MigrationPolicy eligibility logic."""

    def test_standard_policy_includes_critical(self):
        """Standard policy (min HIGH) should include CRITICAL UTXOs."""
        self.assertTrue(POLICY_STANDARD.is_utxo_eligible(RiskLevel.CRITICAL))

    def test_standard_policy_includes_high(self):
        """Standard policy should include HIGH UTXOs."""
        self.assertTrue(POLICY_STANDARD.is_utxo_eligible(RiskLevel.HIGH))

    def test_standard_policy_excludes_medium(self):
        """Standard policy should NOT include MEDIUM UTXOs."""
        self.assertFalse(POLICY_STANDARD.is_utxo_eligible(RiskLevel.MEDIUM))

    def test_emergency_policy_only_critical(self):
        """Emergency policy (min CRITICAL) should only include CRITICAL UTXOs."""
        self.assertTrue(POLICY_EMERGENCY.is_utxo_eligible(RiskLevel.CRITICAL))
        self.assertFalse(POLICY_EMERGENCY.is_utxo_eligible(RiskLevel.HIGH))

    def test_dry_run_policy_includes_medium(self):
        """Dry run policy (min MEDIUM) should include MEDIUM and above."""
        self.assertTrue(POLICY_DRY_RUN.is_utxo_eligible(RiskLevel.CRITICAL))
        self.assertTrue(POLICY_DRY_RUN.is_utxo_eligible(RiskLevel.HIGH))
        self.assertTrue(POLICY_DRY_RUN.is_utxo_eligible(RiskLevel.MEDIUM))
        self.assertFalse(POLICY_DRY_RUN.is_utxo_eligible(RiskLevel.LOW))


class TestMigrationPlanner(unittest.TestCase):
    """Tests for the MigrationPlanner orchestration logic."""

    def setUp(self):
        self.planner = MigrationPlanner()
        self.dest_address = "bc1p_test_quantum_safe_address"

    def test_empty_report_creates_empty_plan(self):
        """An empty risk report should produce an empty migration plan."""
        report = RiskReport()
        plan = self.planner.create_plan(report, POLICY_STANDARD, self.dest_address)
        self.assertEqual(plan.total_batches, 0)
        self.assertEqual(plan.total_utxos, 0)

    def test_no_eligible_utxos(self):
        """If no UTXOs meet the policy criteria, the plan should be empty."""
        assessments = [_make_assessment(RiskLevel.LOW, 1.0, i) for i in range(5)]
        report = _make_report(assessments)
        plan = self.planner.create_plan(report, POLICY_STANDARD, self.dest_address)
        self.assertEqual(plan.total_batches, 0)

    def test_single_batch_creation(self):
        """A small number of eligible UTXOs should fit in a single batch."""
        assessments = [_make_assessment(RiskLevel.CRITICAL, 1.0, i) for i in range(5)]
        report = _make_report(assessments)
        plan = self.planner.create_plan(report, POLICY_STANDARD, self.dest_address)
        self.assertEqual(plan.total_utxos, 5)
        self.assertEqual(plan.total_batches, 1)

    def test_batch_splitting_by_count(self):
        """UTXOs should be split into multiple batches when count limit is exceeded."""
        policy = MigrationPolicy(
            min_risk_level=RiskLevel.HIGH,
            max_batch_utxo_count=3,
            max_batch_value_btc=None,
            approval_mode=ApprovalMode.AUTO,
            execution_mode=ExecutionMode.DRY_RUN,
        )
        assessments = [_make_assessment(RiskLevel.CRITICAL, 1.0, i) for i in range(7)]
        report = _make_report(assessments)
        plan = self.planner.create_plan(report, policy, self.dest_address)
        self.assertEqual(plan.total_utxos, 7)
        self.assertEqual(plan.total_batches, 3)  # 3 + 3 + 1

    def test_batch_splitting_by_value(self):
        """UTXOs should be split into multiple batches when value limit is exceeded."""
        policy = MigrationPolicy(
            min_risk_level=RiskLevel.HIGH,
            max_batch_utxo_count=None,
            max_batch_value_btc=5.0,
            approval_mode=ApprovalMode.AUTO,
            execution_mode=ExecutionMode.DRY_RUN,
        )
        # 6 UTXOs at 2 BTC each = 12 BTC total, should split into 3 batches of 2
        assessments = [_make_assessment(RiskLevel.CRITICAL, 2.0, i) for i in range(6)]
        report = _make_report(assessments)
        plan = self.planner.create_plan(report, policy, self.dest_address)
        self.assertEqual(plan.total_utxos, 6)
        self.assertGreater(plan.total_batches, 1)

    def test_dry_run_batch_status(self):
        """Batches created under DRY_RUN policy should have DRY_RUN_COMPLETE status."""
        assessments = [_make_assessment(RiskLevel.MEDIUM, 1.0, i) for i in range(3)]
        report = _make_report(assessments)
        plan = self.planner.create_plan(report, POLICY_DRY_RUN, self.dest_address)
        for batch in plan.batches:
            self.assertEqual(batch.status, BatchStatus.DRY_RUN_COMPLETE)

    def test_standard_batch_status(self):
        """Batches created under STANDARD policy should be PENDING_APPROVAL."""
        assessments = [_make_assessment(RiskLevel.CRITICAL, 1.0, i) for i in range(3)]
        report = _make_report(assessments)
        plan = self.planner.create_plan(report, POLICY_STANDARD, self.dest_address)
        for batch in plan.batches:
            self.assertEqual(batch.status, BatchStatus.PENDING_APPROVAL)

    def test_critical_utxos_prioritized(self):
        """CRITICAL UTXOs should appear in earlier batches than HIGH UTXOs."""
        assessments = (
            [_make_assessment(RiskLevel.HIGH, 1.0, i) for i in range(3)]
            + [_make_assessment(RiskLevel.CRITICAL, 1.0, i + 3) for i in range(3)]
        )
        report = _make_report(assessments)
        policy = MigrationPolicy(
            min_risk_level=RiskLevel.HIGH,
            max_batch_utxo_count=3,
            max_batch_value_btc=None,
            approval_mode=ApprovalMode.AUTO,
            execution_mode=ExecutionMode.DRY_RUN,
        )
        plan = self.planner.create_plan(report, policy, self.dest_address)
        # First batch should contain CRITICAL UTXOs
        first_batch_risk_levels = {a.risk_level for a in plan.batches[0].assessments}
        self.assertIn(RiskLevel.CRITICAL, first_batch_risk_levels)


if __name__ == "__main__":
    unittest.main(verbosity=2)
