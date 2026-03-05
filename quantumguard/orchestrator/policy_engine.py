"""
QuantumGuard Labs - Migration Policy Engine
============================================
Defines the policy framework that governs how asset migration is planned and executed.
Policies allow institutional users to configure migration behavior according to their
risk tolerance, operational constraints, and compliance requirements.

A policy is a set of rules that the Migration Planner uses to:
  - Filter which UTXOs to include in a migration batch.
  - Determine the order of migration (prioritization).
  - Set limits on batch size (by count or value).
  - Configure approval workflows (e.g., multi-signature requirements).
  - Define safety mechanisms (e.g., delay execution, freeze on anomaly).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from ..analyzer.models import RiskLevel


class ApprovalMode(Enum):
    """
    Defines the required approval workflow before a migration batch is executed.

    - AUTO:         No manual approval required. Suitable for low-risk, automated migrations.
    - SINGLE_SIGN:  Requires approval from a single authorized operator.
    - MULTI_SIGN:   Requires M-of-N approvals from a set of authorized signers.
                    This is the recommended mode for institutional use.
    """
    AUTO = "AUTO"
    SINGLE_SIGN = "SINGLE_SIGN"
    MULTI_SIGN = "MULTI_SIGN"


class ExecutionMode(Enum):
    """
    Defines when a migration transaction is broadcast to the network.

    - IMMEDIATE:    Broadcast as soon as the transaction is built and approved.
    - DELAYED:      Broadcast after a configurable time delay (e.g., 24 hours).
                    Allows for a cancellation window.
    - SCHEDULED:    Broadcast at a specific pre-configured time.
    - DRY_RUN:      Build and validate the transaction but do NOT broadcast.
                    Used for testing and simulation.
    """
    IMMEDIATE = "IMMEDIATE"
    DELAYED = "DELAYED"
    SCHEDULED = "SCHEDULED"
    DRY_RUN = "DRY_RUN"


@dataclass
class MigrationPolicy:
    """
    A comprehensive policy object that governs a migration campaign.

    Attributes:
        name:                   A human-readable name for this policy.
        description:            A description of the policy's purpose.
        min_risk_level:         Only migrate UTXOs at or above this risk level.
                                Defaults to HIGH, meaning CRITICAL and HIGH UTXOs are targeted.
        max_batch_value_btc:    Maximum total BTC value in a single migration batch.
                                Set to None for no limit.
        max_batch_utxo_count:   Maximum number of UTXOs in a single migration batch.
                                Set to None for no limit.
        approval_mode:          The required approval workflow.
        multisig_m:             For MULTI_SIGN mode, the number of required approvals (M).
        multisig_n:             For MULTI_SIGN mode, the total number of authorized signers (N).
        execution_mode:         When to broadcast the migration transaction.
        execution_delay_hours:  For DELAYED mode, the number of hours to wait before broadcasting.
        destination_address_type: The Bitcoin address type to migrate assets TO.
                                  Should be a quantum-resistant type in the future (e.g., P2TR with PQC).
        fee_rate_sat_per_vbyte: The transaction fee rate in satoshis per virtual byte.
        enable_rollback:        If True, the system will attempt to reverse a migration
                                if an anomaly is detected post-broadcast (where possible).
        freeze_on_anomaly:      If True, halt all pending migrations if an unexpected
                                condition is detected.
    """
    name: str = "Default Migration Policy"
    description: str = "Standard quantum risk migration policy."

    # Targeting rules
    min_risk_level: RiskLevel = RiskLevel.HIGH
    max_batch_value_btc: Optional[float] = 100.0
    max_batch_utxo_count: Optional[int] = 50

    # Approval workflow
    approval_mode: ApprovalMode = ApprovalMode.MULTI_SIGN
    multisig_m: int = 2
    multisig_n: int = 3

    # Execution control
    execution_mode: ExecutionMode = ExecutionMode.DELAYED
    execution_delay_hours: int = 24
    destination_address_type: str = "P2TR"  # Target: Taproot, future: PQC address

    # Fee management
    fee_rate_sat_per_vbyte: int = 10

    # Safety mechanisms
    enable_rollback: bool = True
    freeze_on_anomaly: bool = True

    def is_utxo_eligible(self, risk_level: RiskLevel) -> bool:
        """
        Checks if a UTXO with the given risk level is eligible for migration
        under this policy.

        Args:
            risk_level: The assessed risk level of the UTXO.

        Returns:
            True if the UTXO should be included in a migration plan.
        """
        risk_order = {
            RiskLevel.CRITICAL: 5,
            RiskLevel.HIGH: 4,
            RiskLevel.MEDIUM: 3,
            RiskLevel.LOW: 2,
            RiskLevel.SAFE: 1,
        }
        return risk_order.get(risk_level, 0) >= risk_order.get(self.min_risk_level, 0)


# --- Pre-defined Policy Templates ---

POLICY_EMERGENCY = MigrationPolicy(
    name="Emergency Critical Migration",
    description=(
        "Immediately migrates all CRITICAL risk UTXOs (P2PK) with no value limit. "
        "Requires 2-of-3 multi-signature approval. Intended for use when a quantum "
        "threat is considered imminent."
    ),
    min_risk_level=RiskLevel.CRITICAL,
    max_batch_value_btc=None,
    max_batch_utxo_count=None,
    approval_mode=ApprovalMode.MULTI_SIGN,
    multisig_m=2,
    multisig_n=3,
    execution_mode=ExecutionMode.IMMEDIATE,
    freeze_on_anomaly=True,
)

POLICY_STANDARD = MigrationPolicy(
    name="Standard Institutional Migration",
    description=(
        "Migrates HIGH and CRITICAL risk UTXOs in controlled batches. "
        "Requires 2-of-3 multi-signature approval with a 24-hour execution delay. "
        "Suitable for planned, non-emergency migration campaigns."
    ),
    min_risk_level=RiskLevel.HIGH,
    max_batch_value_btc=100.0,
    max_batch_utxo_count=50,
    approval_mode=ApprovalMode.MULTI_SIGN,
    multisig_m=2,
    multisig_n=3,
    execution_mode=ExecutionMode.DELAYED,
    execution_delay_hours=24,
)

POLICY_DRY_RUN = MigrationPolicy(
    name="Simulation / Dry Run",
    description=(
        "Simulates the full migration process for all UTXOs at MEDIUM risk or above. "
        "Transactions are built and validated but NOT broadcast to the network. "
        "Used for testing, auditing, and board-level demonstration."
    ),
    min_risk_level=RiskLevel.MEDIUM,
    max_batch_value_btc=None,
    max_batch_utxo_count=None,
    approval_mode=ApprovalMode.AUTO,
    execution_mode=ExecutionMode.DRY_RUN,
    enable_rollback=False,
    freeze_on_anomaly=False,
)
