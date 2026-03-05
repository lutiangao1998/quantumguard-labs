"""
QuantumGuard Labs - Compliance Report Generator
================================================
Generates human-readable compliance and risk reports from analysis results
and quantum readiness proofs. Reports are formatted for different audiences:
  - Executive Summary: For board-level and C-suite consumption.
  - Technical Report: For security teams and auditors.
  - Regulatory Filing: For submission to regulatory bodies.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from ..analyzer.models import RiskLevel, RiskReport
from .proof_generator import QuantumReadinessProof

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generates structured compliance reports from QMP analysis data.

    Usage:
        reporter = ReportGenerator()
        markdown_report = reporter.generate_executive_summary(risk_report, proof)
        print(markdown_report)
    """

    def generate_executive_summary(
        self,
        risk_report: RiskReport,
        proof: Optional[QuantumReadinessProof] = None,
        organization_name: str = "Your Organization",
    ) -> str:
        """
        Generates a Markdown-formatted executive summary report.

        Args:
            risk_report:       The risk analysis report.
            proof:             The quantum readiness proof (optional).
            organization_name: The name of the organization.

        Returns:
            A Markdown string containing the executive summary.
        """
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        score = risk_report.quantum_readiness_score
        score_label = self._get_score_label(score)

        lines = [
            f"# Quantum Readiness Executive Summary",
            f"",
            f"**Organization:** {organization_name}  ",
            f"**Report Generated:** {now}  ",
            f"**Platform:** QuantumGuard Labs QMP v1.0  ",
            f"",
            f"---",
            f"",
            f"## Overall Quantum Readiness Score",
            f"",
            f"```",
            f"  {score:.1f} / 100  [{score_label}]",
            f"```",
            f"",
            f"> **Interpretation:** A score of {score:.1f}/100 indicates that "
            f"{score:.1f}% of the portfolio's value (by weight) is currently "
            f"protected against quantum attacks. The remaining "
            f"{100 - score:.1f}% requires attention.",
            f"",
            f"---",
            f"",
            f"## Portfolio Risk Breakdown",
            f"",
            f"| Risk Level | UTXO Count | Notes |",
            f"|---|---|---|",
            f"| 🔴 CRITICAL | {risk_report.critical_count} | Public key directly exposed (P2PK). Immediate action required. |",
            f"| 🟠 HIGH | {risk_report.high_count} | Address reused; public key revealed. High priority migration. |",
            f"| 🟡 MEDIUM | {risk_report.medium_count} | Taproot with key-path spend history. Schedule migration. |",
            f"| 🟢 LOW | {risk_report.low_count} | Unused address; only hash exposed. Monitor and plan. |",
            f"| ✅ SAFE | {risk_report.safe_count} | No significant quantum exposure detected. |",
            f"| **TOTAL** | **{risk_report.total_utxos}** | |",
            f"",
            f"",
            f"## Financial Exposure Summary",
            f"",
            f"| Category | Value (BTC) | % of Portfolio |",
            f"|---|---|---|",
        ]

        total = risk_report.total_value_btc if risk_report.total_value_btc > 0 else 1
        lines += [
            f"| Total Portfolio Value | {risk_report.total_value_btc:.8f} BTC | 100.00% |",
            f"| CRITICAL Risk Exposure | {risk_report.critical_value_btc:.8f} BTC | {risk_report.critical_value_btc / total * 100:.2f}% |",
            f"| HIGH Risk Exposure | {risk_report.high_value_btc:.8f} BTC | {risk_report.high_value_btc / total * 100:.2f}% |",
            f"| Total At-Risk Value | {(risk_report.critical_value_btc + risk_report.high_value_btc):.8f} BTC | {(risk_report.critical_value_btc + risk_report.high_value_btc) / total * 100:.2f}% |",
            f"",
            f"---",
            f"",
            f"## Recommended Actions",
            f"",
            f"1. **IMMEDIATE (0-30 days):** Initiate emergency migration for all "
            f"{risk_report.critical_count} CRITICAL-risk UTXOs ({risk_report.critical_value_btc:.4f} BTC). "
            f"These P2PK outputs have directly exposed public keys.",
            f"",
            f"2. **SHORT-TERM (30-90 days):** Schedule migration for all "
            f"{risk_report.high_count} HIGH-risk UTXOs ({risk_report.high_value_btc:.4f} BTC). "
            f"These addresses have had their public keys revealed through prior transactions.",
            f"",
            f"3. **MEDIUM-TERM (90-180 days):** Plan migration for MEDIUM and LOW risk "
            f"UTXOs as part of a comprehensive quantum security upgrade program.",
            f"",
            f"4. **ONGOING:** Implement a policy to never reuse Bitcoin addresses and "
            f"to use Taproot (P2TR) or future PQC-secured address types for all new deposits.",
            f"",
        ]

        if proof:
            lines += [
                f"---",
                f"",
                f"## Compliance Attestation",
                f"",
                f"> {proof.attestation_statement}",
                f"",
                f"**Proof ID:** `{proof.proof_id}`  ",
                f"**Audit Log Integrity Hash:** `{proof.audit_log_hash[:32]}...`  ",
                f"",
            ]

        lines += [
            f"---",
            f"",
            f"*This report was generated by the QuantumGuard Labs Quantum Migration Platform (QMP).*  ",
            f"*For technical details, refer to the full Technical Risk Report.*  ",
            f"*Contact: contact@quantumguard.io | www.quantumguard.io*",
        ]

        return "\n".join(lines)

    def generate_json_report(self, risk_report: RiskReport) -> str:
        """
        Generates a machine-readable JSON risk report.

        Args:
            risk_report: The risk analysis report.

        Returns:
            A JSON string containing the full risk report.
        """
        report_data = {
            "report_metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "platform": "QuantumGuard Labs QMP v1.0",
                "report_type": "QUANTUM_RISK_ANALYSIS",
            },
            "summary": {
                "total_utxos": risk_report.total_utxos,
                "total_value_btc": risk_report.total_value_btc,
                "quantum_readiness_score": risk_report.quantum_readiness_score,
                "risk_counts": {
                    "CRITICAL": risk_report.critical_count,
                    "HIGH": risk_report.high_count,
                    "MEDIUM": risk_report.medium_count,
                    "LOW": risk_report.low_count,
                    "SAFE": risk_report.safe_count,
                },
                "risk_values_btc": {
                    "CRITICAL": risk_report.critical_value_btc,
                    "HIGH": risk_report.high_value_btc,
                },
            },
            "assessments": [a.to_dict() for a in risk_report.assessments],
        }
        return json.dumps(report_data, indent=2)

    def _get_score_label(self, score: float) -> str:
        """Returns a human-readable label for a quantum readiness score."""
        if score >= 90:
            return "EXCELLENT - Quantum Ready"
        elif score >= 70:
            return "GOOD - Minor Exposure"
        elif score >= 50:
            return "MODERATE - Significant Exposure"
        elif score >= 30:
            return "POOR - High Exposure"
        else:
            return "CRITICAL - Immediate Action Required"
