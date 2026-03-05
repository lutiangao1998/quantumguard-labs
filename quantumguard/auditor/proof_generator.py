"""
QuantumGuard Labs - Migration Proof Generator
==============================================
Generates cryptographically verifiable proofs and audit logs for all migration
activities. This module implements the "Compliance Proof" phase of the QMP platform.

The audit trail produced by this module is designed to satisfy the requirements of:
  - Internal compliance and risk management teams.
  - External auditors and security assessors.
  - Regulatory bodies (e.g., SEC, FCA, MAS) requiring evidence of quantum readiness.
  - Board-level reporting on digital asset security posture.

Key outputs:
  - Immutable, timestamped audit log entries for every migration event.
  - A "Quantum Readiness Score" for the portfolio.
  - A structured compliance report (JSON) suitable for further processing.
"""

import hashlib
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """
    Types of events recorded in the audit log.
    """
    RISK_ANALYSIS_STARTED = "RISK_ANALYSIS_STARTED"
    RISK_ANALYSIS_COMPLETED = "RISK_ANALYSIS_COMPLETED"
    MIGRATION_PLAN_CREATED = "MIGRATION_PLAN_CREATED"
    BATCH_APPROVAL_REQUESTED = "BATCH_APPROVAL_REQUESTED"
    BATCH_APPROVED = "BATCH_APPROVED"
    BATCH_EXECUTION_STARTED = "BATCH_EXECUTION_STARTED"
    TRANSACTION_CONSTRUCTED = "TRANSACTION_CONSTRUCTED"
    TRANSACTION_BROADCAST = "TRANSACTION_BROADCAST"
    TRANSACTION_CONFIRMED = "TRANSACTION_CONFIRMED"
    BATCH_COMPLETED = "BATCH_COMPLETED"
    BATCH_FAILED = "BATCH_FAILED"
    ANOMALY_DETECTED = "ANOMALY_DETECTED"
    MIGRATION_FROZEN = "MIGRATION_FROZEN"


@dataclass
class AuditLogEntry:
    """
    A single, immutable entry in the audit log.

    Each entry is chained to the previous one via a hash pointer, creating
    a tamper-evident log structure similar to a blockchain.

    Attributes:
        entry_id:       A unique identifier for this log entry.
        event_type:     The type of event being recorded.
        timestamp:      The UTC timestamp of the event.
        actor:          The entity that triggered the event (user ID, system, etc.).
        details:        A dictionary of event-specific details.
        previous_hash:  The SHA-256 hash of the previous log entry (for chaining).
        entry_hash:     The SHA-256 hash of this entry's content (computed on creation).
    """
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: AuditEventType = AuditEventType.RISK_ANALYSIS_STARTED
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    actor: str = "system"
    details: dict[str, Any] = field(default_factory=dict)
    previous_hash: str = "0" * 64  # Genesis entry has a zero hash
    entry_hash: str = field(init=False)

    def __post_init__(self):
        self.entry_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """Computes the SHA-256 hash of this entry's canonical content."""
        content = {
            "entry_id": self.entry_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "actor": self.actor,
            "details": self.details,
            "previous_hash": self.previous_hash,
        }
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()

    def to_dict(self) -> dict:
        """Serializes the entry to a dictionary."""
        return {
            "entry_id": self.entry_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "actor": self.actor,
            "details": self.details,
            "previous_hash": self.previous_hash,
            "entry_hash": self.entry_hash,
        }


@dataclass
class QuantumReadinessProof:
    """
    A formal proof of an organization's quantum readiness posture.

    This document is the primary deliverable for compliance and audit purposes.
    It summarizes the risk analysis, migration activities, and the resulting
    improvement in the portfolio's quantum security posture.

    Attributes:
        proof_id:               A unique identifier for this proof document.
        organization_id:        The identifier of the organization being assessed.
        generated_at:           The UTC timestamp when this proof was generated.
        analysis_period_start:  The start of the analysis period.
        analysis_period_end:    The end of the analysis period.
        initial_readiness_score: The quantum readiness score BEFORE migration.
        final_readiness_score:  The quantum readiness score AFTER migration.
        total_utxos_analyzed:   Total UTXOs analyzed.
        total_utxos_migrated:   Total UTXOs successfully migrated.
        total_value_migrated_btc: Total BTC value migrated.
        risk_summary:           A breakdown of risk levels before and after.
        audit_log_hash:         The hash of the final audit log entry (proof of integrity).
        audit_log:              The full, chained audit log for this campaign.
        attestation_statement:  A formal statement for regulatory submission.
    """
    proof_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str = "UNKNOWN_ORG"
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    analysis_period_start: Optional[datetime] = None
    analysis_period_end: Optional[datetime] = None
    initial_readiness_score: float = 0.0
    final_readiness_score: float = 0.0
    total_utxos_analyzed: int = 0
    total_utxos_migrated: int = 0
    total_value_migrated_btc: float = 0.0
    risk_summary: dict[str, Any] = field(default_factory=dict)
    audit_log_hash: str = ""
    audit_log: list[AuditLogEntry] = field(default_factory=list)
    attestation_statement: str = ""

    def to_dict(self) -> dict:
        """Serializes the proof to a dictionary for JSON export."""
        return {
            "proof_id": self.proof_id,
            "organization_id": self.organization_id,
            "generated_at": self.generated_at.isoformat(),
            "analysis_period": {
                "start": self.analysis_period_start.isoformat() if self.analysis_period_start else None,
                "end": self.analysis_period_end.isoformat() if self.analysis_period_end else None,
            },
            "quantum_readiness": {
                "initial_score": self.initial_readiness_score,
                "final_score": self.final_readiness_score,
                "improvement": round(self.final_readiness_score - self.initial_readiness_score, 2),
            },
            "migration_summary": {
                "total_utxos_analyzed": self.total_utxos_analyzed,
                "total_utxos_migrated": self.total_utxos_migrated,
                "total_value_migrated_btc": round(self.total_value_migrated_btc, 8),
            },
            "risk_summary": self.risk_summary,
            "audit_log_integrity": {
                "final_entry_hash": self.audit_log_hash,
                "log_entry_count": len(self.audit_log),
            },
            "attestation_statement": self.attestation_statement,
        }


class ProofGenerator:
    """
    Manages the audit log and generates quantum readiness proofs.

    This class maintains a running, chained audit log. At any point, a
    QuantumReadinessProof can be generated from the accumulated log.

    Usage:
        generator = ProofGenerator(organization_id="ACME_CUSTODY_001")
        generator.log_event(AuditEventType.RISK_ANALYSIS_STARTED, actor="system")
        # ... perform analysis and migration ...
        proof = generator.generate_proof(
            initial_score=45.0,
            final_score=92.0,
            ...
        )
        proof_json = json.dumps(proof.to_dict(), indent=2)
    """

    def __init__(self, organization_id: str = "UNKNOWN_ORG"):
        self.organization_id = organization_id
        self._audit_log: list[AuditLogEntry] = []
        self._last_hash = "0" * 64
        logger.info(f"ProofGenerator initialized for organization: {organization_id}")

    def log_event(
        self,
        event_type: AuditEventType,
        actor: str = "system",
        details: Optional[dict] = None,
    ) -> AuditLogEntry:
        """
        Records a new event in the tamper-evident audit log.

        Args:
            event_type: The type of event to record.
            actor:      The entity responsible for this event.
            details:    A dictionary of additional event details.

        Returns:
            The newly created AuditLogEntry.
        """
        entry = AuditLogEntry(
            event_type=event_type,
            actor=actor,
            details=details or {},
            previous_hash=self._last_hash,
        )
        self._audit_log.append(entry)
        self._last_hash = entry.entry_hash
        logger.debug(
            f"Audit event logged: [{event_type.value}] by '{actor}'. "
            f"Entry hash: {entry.entry_hash[:16]}..."
        )
        return entry

    def verify_log_integrity(self) -> bool:
        """
        Verifies the integrity of the entire audit log by re-computing
        and checking all hash chain links.

        Returns:
            True if the log is intact and has not been tampered with.
        """
        if not self._audit_log:
            return True

        prev_hash = "0" * 64
        for entry in self._audit_log:
            if entry.previous_hash != prev_hash:
                logger.error(
                    f"Audit log integrity check FAILED at entry '{entry.entry_id}'. "
                    f"Expected previous hash '{prev_hash}', got '{entry.previous_hash}'."
                )
                return False
            recomputed_hash = entry._compute_hash()
            if recomputed_hash != entry.entry_hash:
                logger.error(
                    f"Audit log integrity check FAILED at entry '{entry.entry_id}'. "
                    f"Entry hash mismatch: stored='{entry.entry_hash}', "
                    f"recomputed='{recomputed_hash}'."
                )
                return False
            prev_hash = entry.entry_hash

        logger.info("Audit log integrity check PASSED. All entries are valid.")
        return True

    def generate_proof(
        self,
        initial_readiness_score: float,
        final_readiness_score: float,
        total_utxos_analyzed: int,
        total_utxos_migrated: int,
        total_value_migrated_btc: float,
        risk_summary: dict,
        analysis_period_start: Optional[datetime] = None,
        analysis_period_end: Optional[datetime] = None,
    ) -> QuantumReadinessProof:
        """
        Generates a formal QuantumReadinessProof from the accumulated audit log.

        Args:
            initial_readiness_score:  Portfolio score before migration.
            final_readiness_score:    Portfolio score after migration.
            total_utxos_analyzed:     Number of UTXOs analyzed.
            total_utxos_migrated:     Number of UTXOs successfully migrated.
            total_value_migrated_btc: Total BTC value migrated.
            risk_summary:             Risk breakdown dictionary.
            analysis_period_start:    Start of the analysis window.
            analysis_period_end:      End of the analysis window.

        Returns:
            A QuantumReadinessProof object.
        """
        attestation = (
            f"This document certifies that {self.organization_id} has completed a "
            f"quantum risk analysis and asset migration campaign using the QuantumGuard Labs "
            f"Quantum Migration Platform (QMP). The portfolio's Quantum Readiness Score "
            f"improved from {initial_readiness_score:.1f}/100 to {final_readiness_score:.1f}/100. "
            f"A total of {total_utxos_migrated} UTXOs ({total_value_migrated_btc:.8f} BTC) "
            f"were successfully migrated to quantum-safer addresses. "
            f"The integrity of this audit trail is verifiable via the hash chain "
            f"anchored at entry hash: {self._last_hash[:32]}..."
        )

        proof = QuantumReadinessProof(
            organization_id=self.organization_id,
            analysis_period_start=analysis_period_start,
            analysis_period_end=analysis_period_end or datetime.now(timezone.utc),
            initial_readiness_score=initial_readiness_score,
            final_readiness_score=final_readiness_score,
            total_utxos_analyzed=total_utxos_analyzed,
            total_utxos_migrated=total_utxos_migrated,
            total_value_migrated_btc=total_value_migrated_btc,
            risk_summary=risk_summary,
            audit_log_hash=self._last_hash,
            audit_log=list(self._audit_log),
            attestation_statement=attestation,
        )

        logger.info(
            f"Quantum Readiness Proof generated: ID={proof.proof_id}, "
            f"Score: {initial_readiness_score} -> {final_readiness_score}"
        )
        return proof

    def export_log_json(self) -> str:
        """Exports the full audit log as a JSON string."""
        log_data = {
            "organization_id": self.organization_id,
            "log_entry_count": len(self._audit_log),
            "final_hash": self._last_hash,
            "entries": [entry.to_dict() for entry in self._audit_log],
        }
        return json.dumps(log_data, indent=2)
