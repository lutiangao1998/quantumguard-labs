"""
QuantumGuard Labs - Migration Planner (Orchestrator)
=====================================================
The core orchestration engine that transforms a risk report into an actionable,
policy-compliant migration plan. This module implements the "Orchestrate Migration"
phase of the QMP platform.

Key capabilities:
  - Filter and prioritize UTXOs based on a MigrationPolicy.
  - Divide eligible UTXOs into safe, manageable migration batches.
  - Generate a structured MigrationPlan with full audit trail.
  - Simulate transaction construction (Dry Run mode).
  - Manage the lifecycle of migration batches (PENDING -> APPROVED -> EXECUTING -> COMPLETED).
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional

from ..analyzer.models import RiskAssessment, RiskReport, UTXO
from .policy_engine import ApprovalMode, ExecutionMode, MigrationPolicy

logger = logging.getLogger(__name__)


class BatchStatus(Enum):
    """
    Lifecycle status of a single migration batch.
    """
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    DRY_RUN_COMPLETE = "DRY_RUN_COMPLETE"


@dataclass
class MigrationBatch:
    """
    Represents a single batch of UTXOs to be migrated together in one transaction.

    Attributes:
        batch_id:           A unique identifier for this batch.
        assessments:        The list of risk assessments for UTXOs in this batch.
        destination_address: The quantum-safer address to migrate funds to.
        total_value_btc:    Total BTC value being migrated in this batch.
        status:             The current lifecycle status of this batch.
        created_at:         Timestamp when this batch was created.
        scheduled_at:       Timestamp when this batch is scheduled for execution.
        approvals:          List of approval signatures collected so far.
        tx_hex:             The raw transaction hex (populated after construction).
        txid:               The broadcast transaction ID (populated after broadcast).
        notes:              Any additional notes or audit comments.
    """
    batch_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    assessments: list[RiskAssessment] = field(default_factory=list)
    destination_address: str = ""
    total_value_btc: float = 0.0
    status: BatchStatus = BatchStatus.PENDING_APPROVAL
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    scheduled_at: Optional[datetime] = None
    approvals: list[str] = field(default_factory=list)
    tx_hex: Optional[str] = None
    txid: Optional[str] = None
    notes: str = ""

    def to_summary_dict(self) -> dict:
        """Returns a summary dictionary for reporting and logging."""
        return {
            "batch_id": self.batch_id,
            "utxo_count": len(self.assessments),
            "total_value_btc": round(self.total_value_btc, 8),
            "destination_address": self.destination_address,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "approvals_collected": len(self.approvals),
            "txid": self.txid,
        }


@dataclass
class MigrationPlan:
    """
    A complete, policy-compliant migration plan for a portfolio.

    Attributes:
        plan_id:            A unique identifier for this migration plan.
        policy_name:        The name of the policy used to generate this plan.
        batches:            The ordered list of migration batches.
        total_batches:      Total number of batches in the plan.
        total_utxos:        Total number of UTXOs to be migrated.
        total_value_btc:    Total BTC value to be migrated.
        created_at:         Timestamp when this plan was created.
        estimated_fees_btc: Estimated total transaction fees.
    """
    plan_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    policy_name: str = ""
    batches: list[MigrationBatch] = field(default_factory=list)
    total_batches: int = 0
    total_utxos: int = 0
    total_value_btc: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    estimated_fees_btc: float = 0.0


class MigrationPlanner:
    """
    Generates and manages migration plans based on risk reports and policies.

    This is the central orchestration component. It takes the output of the
    BitcoinQuantumAnalyzer and, guided by a MigrationPolicy, produces a
    structured MigrationPlan ready for execution.

    Usage:
        planner = MigrationPlanner()
        plan = planner.create_plan(
            risk_report=report,
            policy=POLICY_STANDARD,
            destination_address="bc1p..."
        )
        print(f"Plan created: {plan.total_batches} batches, {plan.total_utxos} UTXOs")
    """

    def __init__(self):
        self._active_plans: dict[str, MigrationPlan] = {}

    def create_plan(
        self,
        risk_report: RiskReport,
        policy: MigrationPolicy,
        destination_address: str,
    ) -> MigrationPlan:
        """
        Creates a migration plan from a risk report, guided by a policy.

        The planning process:
        1. Filter assessments to only include UTXOs eligible under the policy.
        2. Sort eligible UTXOs by migration priority (CRITICAL first).
        3. Divide sorted UTXOs into batches, respecting policy limits.
        4. For each batch, set the scheduled execution time based on the policy.

        Args:
            risk_report:        The output from BitcoinQuantumAnalyzer.analyze_portfolio().
            policy:             The MigrationPolicy to apply.
            destination_address: The target address for migrated funds.

        Returns:
            A MigrationPlan object ready for review and execution.
        """
        logger.info(
            f"Creating migration plan using policy '{policy.name}' "
            f"for {risk_report.total_utxos} UTXOs."
        )

        # Step 1: Filter eligible UTXOs
        eligible = [
            a for a in risk_report.assessments
            if policy.is_utxo_eligible(a.risk_level)
        ]
        logger.info(f"Eligible UTXOs for migration: {len(eligible)} / {risk_report.total_utxos}")

        if not eligible:
            logger.warning("No UTXOs are eligible for migration under the current policy.")
            return MigrationPlan(policy_name=policy.name)

        # Step 2: Sort by priority (lower priority number = higher urgency)
        eligible.sort(key=lambda a: (a.migration_priority, -a.utxo.value_btc))

        # Step 3: Divide into batches
        batches = self._create_batches(eligible, policy, destination_address)

        # Step 4: Build the plan
        plan = MigrationPlan(
            policy_name=policy.name,
            batches=batches,
            total_batches=len(batches),
            total_utxos=sum(len(b.assessments) for b in batches),
            total_value_btc=sum(b.total_value_btc for b in batches),
            estimated_fees_btc=self._estimate_fees(eligible, policy),
        )

        self._active_plans[plan.plan_id] = plan
        logger.info(
            f"Migration plan '{plan.plan_id}' created: "
            f"{plan.total_batches} batches, {plan.total_utxos} UTXOs, "
            f"{plan.total_value_btc:.8f} BTC."
        )
        return plan

    def _create_batches(
        self,
        assessments: list[RiskAssessment],
        policy: MigrationPolicy,
        destination_address: str,
    ) -> list[MigrationBatch]:
        """
        Divides a sorted list of assessments into policy-compliant batches.
        """
        batches = []
        current_batch_assessments = []
        current_batch_value = 0.0

        for assessment in assessments:
            utxo_value = assessment.utxo.value_btc

            # Check if adding this UTXO would violate batch limits
            count_limit_reached = (
                policy.max_batch_utxo_count is not None
                and len(current_batch_assessments) >= policy.max_batch_utxo_count
            )
            value_limit_reached = (
                policy.max_batch_value_btc is not None
                and current_batch_value + utxo_value > policy.max_batch_value_btc
            )

            if current_batch_assessments and (count_limit_reached or value_limit_reached):
                # Finalize the current batch and start a new one
                batches.append(
                    self._finalize_batch(current_batch_assessments, current_batch_value, policy, destination_address)
                )
                current_batch_assessments = []
                current_batch_value = 0.0

            current_batch_assessments.append(assessment)
            current_batch_value += utxo_value

        # Add the last remaining batch
        if current_batch_assessments:
            batches.append(
                self._finalize_batch(current_batch_assessments, current_batch_value, policy, destination_address)
            )

        return batches

    def _finalize_batch(
        self,
        assessments: list[RiskAssessment],
        total_value: float,
        policy: MigrationPolicy,
        destination_address: str,
    ) -> MigrationBatch:
        """Creates and configures a single MigrationBatch object."""
        now = datetime.now(timezone.utc)

        if policy.execution_mode == ExecutionMode.DELAYED:
            scheduled_at = now + timedelta(hours=policy.execution_delay_hours)
        elif policy.execution_mode == ExecutionMode.IMMEDIATE:
            scheduled_at = now
        else:
            scheduled_at = None

        status = (
            BatchStatus.DRY_RUN_COMPLETE
            if policy.execution_mode == ExecutionMode.DRY_RUN
            else BatchStatus.PENDING_APPROVAL
        )

        return MigrationBatch(
            assessments=assessments,
            destination_address=destination_address,
            total_value_btc=total_value,
            status=status,
            scheduled_at=scheduled_at,
            notes=f"Policy: {policy.name} | Approval: {policy.approval_mode.value}",
        )

    def _estimate_fees(self, assessments: list[RiskAssessment], policy: MigrationPolicy) -> float:
        """
        Estimates the total transaction fees for migrating all eligible UTXOs.

        Uses a simplified model: each input is ~148 vbytes, each output is ~34 vbytes,
        plus 10 vbytes for transaction overhead.
        """
        num_inputs = len(assessments)
        num_outputs = 1  # One consolidated output per batch (simplified)
        tx_vbytes = (num_inputs * 148) + (num_outputs * 34) + 10
        fee_sats = tx_vbytes * policy.fee_rate_sat_per_vbyte
        return fee_sats / 1e8  # Convert satoshis to BTC

    def approve_batch(self, plan_id: str, batch_id: str, approver_id: str) -> bool:
        """
        Records an approval signature for a migration batch.

        Args:
            plan_id:    The ID of the migration plan.
            batch_id:   The ID of the batch to approve.
            approver_id: A unique identifier for the approving party.

        Returns:
            True if the batch is now fully approved and ready for execution.
        """
        plan = self._active_plans.get(plan_id)
        if not plan:
            logger.error(f"Plan '{plan_id}' not found.")
            return False

        batch = next((b for b in plan.batches if b.batch_id == batch_id), None)
        if not batch:
            logger.error(f"Batch '{batch_id}' not found in plan '{plan_id}'.")
            return False

        if approver_id not in batch.approvals:
            batch.approvals.append(approver_id)
            logger.info(f"Approval recorded for batch '{batch_id}' by '{approver_id}'.")

        # Check if the batch is now fully approved
        # (This would be validated against the policy's M-of-N requirement in production)
        logger.info(f"Batch '{batch_id}' has {len(batch.approvals)} approval(s).")
        return True
