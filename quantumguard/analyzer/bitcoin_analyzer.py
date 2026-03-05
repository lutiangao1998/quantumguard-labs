"""
QuantumGuard Labs - Bitcoin Quantum Risk Analyzer
=================================================
Core module for analyzing Bitcoin UTXOs and assessing their quantum attack
exposure surface. This module implements the "Identify Risk" phase of the QMP platform.

Key capabilities:
  - Parse Bitcoin transaction scripts to determine script type.
  - Identify UTXOs where the public key is directly exposed (P2PK).
  - Identify UTXOs where the address has been reused (public key revealed via signature).
  - Assign a risk level and score to each UTXO.
  - Generate a consolidated risk report for a given portfolio.
"""

import logging
from typing import Optional

from .models import (
    UTXO,
    RiskAssessment,
    RiskLevel,
    RiskReport,
    ScriptType,
)

logger = logging.getLogger(__name__)


# --- Script Type Classification ---

def classify_script_type(script_hex: str) -> tuple[ScriptType, Optional[str]]:
    """
    Classifies a Bitcoin ScriptPubKey hex string into a known script type.

    This is a simplified heuristic-based classifier. A production implementation
    would use a full Bitcoin script parser.

    Args:
        script_hex: The ScriptPubKey as a hexadecimal string.

    Returns:
        A tuple of (ScriptType, pubkey_hex). pubkey_hex is only non-None for P2PK.
    """
    if not script_hex:
        return ScriptType.UNKNOWN, None

    # P2PK: OP_PUSH <pubkey> OP_CHECKSIG
    # Uncompressed pubkey: 41 bytes (0x04...) -> script: 43 bytes
    # Compressed pubkey: 33 bytes (0x02/0x03...) -> script: 35 bytes
    if script_hex.startswith("41") and script_hex.endswith("ac") and len(script_hex) == 86:
        pubkey = script_hex[2:84]
        return ScriptType.P2PK, pubkey
    if script_hex.startswith(("2102", "2103")) and script_hex.endswith("ac") and len(script_hex) == 70:
        pubkey = script_hex[2:68]
        return ScriptType.P2PK, pubkey

    # P2PKH: OP_DUP OP_HASH160 <hash160> OP_EQUALVERIFY OP_CHECKSIG
    if script_hex.startswith("76a914") and script_hex.endswith("88ac") and len(script_hex) == 50:
        return ScriptType.P2PKH, None

    # P2SH: OP_HASH160 <hash160> OP_EQUAL
    if script_hex.startswith("a914") and script_hex.endswith("87") and len(script_hex) == 46:
        return ScriptType.P2SH, None

    # P2WPKH: OP_0 <20-byte-key-hash>
    if script_hex.startswith("0014") and len(script_hex) == 44:
        return ScriptType.P2WPKH, None

    # P2WSH: OP_0 <32-byte-script-hash>
    if script_hex.startswith("0020") and len(script_hex) == 68:
        return ScriptType.P2WSH, None

    # P2TR (Taproot): OP_1 <32-byte-x-only-pubkey>
    if script_hex.startswith("5120") and len(script_hex) == 68:
        return ScriptType.P2TR, None

    return ScriptType.UNKNOWN, None


# --- Risk Assessment Logic ---

def assess_utxo_risk(utxo: UTXO) -> RiskAssessment:
    """
    Performs a quantum risk assessment on a single UTXO.

    The risk model is based on the following principles:
    1. Direct public key exposure (P2PK) is the highest risk, as a quantum
       computer can directly run Shor's algorithm on the exposed key.
    2. Address reuse for P2PKH/P2WPKH outputs reveals the public key in the
       spending transaction's scriptSig/witness, creating HIGH risk.
    3. Taproot outputs with key-path spends reveal the tweaked public key,
       creating MEDIUM risk.
    4. Unused P2PKH/P2WPKH addresses have LOW risk (only hash is exposed).
    5. Addresses already migrated to a PQC scheme are SAFE.

    Args:
        utxo: The UTXO to assess.

    Returns:
        A RiskAssessment object with the determined risk level and details.
    """
    risk_level = RiskLevel.SAFE
    risk_score = 0
    risk_reasons = []
    recommended_action = "No immediate action required."

    if utxo.script_type == ScriptType.P2PK:
        # The public key is directly embedded in the locking script.
        # This is the most dangerous scenario.
        risk_level = RiskLevel.CRITICAL
        risk_score = 95
        risk_reasons.append(
            "Script type is P2PK: the full public key is directly exposed "
            "in the ScriptPubKey on the blockchain. A quantum computer can "
            "derive the private key using Shor's algorithm."
        )
        recommended_action = (
            "URGENT: Migrate funds immediately to a quantum-resistant address. "
            "Do not spend from this address until migration is complete, as "
            "spending would broadcast the signature, giving attackers more data."
        )

    elif utxo.script_type in (ScriptType.P2PKH, ScriptType.P2WPKH):
        if utxo.is_pubkey_exposed or utxo.is_reused:
            # The address has been used to send funds before. The public key
            # was revealed in the scriptSig/witness of a prior transaction.
            risk_level = RiskLevel.HIGH
            risk_score = 75
            risk_reasons.append(
                f"Address has been previously used to send funds ({utxo.script_type.value}). "
                "The public key was revealed in a prior spending transaction's signature, "
                "making it vulnerable to quantum key derivation."
            )
            recommended_action = (
                "HIGH PRIORITY: Schedule migration to a quantum-resistant address. "
                "Avoid further use of this address."
            )
        else:
            # The address has only received funds, never sent.
            # Only the hash of the public key is exposed, providing some protection.
            risk_level = RiskLevel.LOW
            risk_score = 20
            risk_reasons.append(
                f"Address ({utxo.script_type.value}) has never been used to send funds. "
                "Only the public key hash is exposed. Risk is present but lower, "
                "as a quantum computer would need to break SHA256/RIPEMD160 first."
            )
            recommended_action = (
                "MONITOR: Plan for future migration. Do not reuse this address."
            )

    elif utxo.script_type == ScriptType.P2TR:
        if utxo.is_reused:
            # A Taproot key-path spend reveals the tweaked internal public key.
            risk_level = RiskLevel.MEDIUM
            risk_score = 50
            risk_reasons.append(
                "Taproot (P2TR) address has been used for a key-path spend, "
                "revealing the tweaked public key. This is potentially vulnerable "
                "to quantum attacks on the revealed key."
            )
            recommended_action = "MEDIUM PRIORITY: Plan migration to a PQC-secured address."
        else:
            risk_level = RiskLevel.LOW
            risk_score = 15
            risk_reasons.append(
                "Taproot (P2TR) address with no key-path spend history. "
                "The internal public key is not directly exposed."
            )
            recommended_action = "MONITOR: Low risk. Include in long-term migration plan."

    elif utxo.script_type in (ScriptType.P2SH, ScriptType.P2WSH):
        risk_level = RiskLevel.LOW
        risk_score = 10
        risk_reasons.append(
            f"Script hash type ({utxo.script_type.value}). The underlying redeem script "
            "is only revealed upon spending. Risk depends on the underlying script."
        )
        recommended_action = "MONITOR: Analyze the underlying redeem script for further risk."

    else:
        risk_level = RiskLevel.SAFE
        risk_score = 0
        risk_reasons.append("Script type is unknown or already quantum-safe.")
        recommended_action = "No action required."

    # Determine migration priority (lower number = higher priority)
    priority_map = {
        RiskLevel.CRITICAL: 1,
        RiskLevel.HIGH: 2,
        RiskLevel.MEDIUM: 3,
        RiskLevel.LOW: 4,
        RiskLevel.SAFE: 5,
    }
    migration_priority = priority_map.get(risk_level, 5)

    return RiskAssessment(
        utxo=utxo,
        risk_level=risk_level,
        risk_score=risk_score,
        risk_reasons=risk_reasons,
        migration_priority=migration_priority,
        recommended_action=recommended_action,
    )


# --- Portfolio Analysis ---

class BitcoinQuantumAnalyzer:
    """
    Main analyzer class for assessing the quantum risk of a Bitcoin UTXO portfolio.

    This class orchestrates the full analysis pipeline:
    1. Accepts a list of UTXOs (from a blockchain connector or manual input).
    2. Classifies each UTXO's script type.
    3. Assesses the quantum risk of each UTXO.
    4. Generates a consolidated RiskReport.

    Usage:
        analyzer = BitcoinQuantumAnalyzer()
        utxos = [...]  # List of UTXO objects
        report = analyzer.analyze_portfolio(utxos)
        print(f"Quantum Readiness Score: {report.quantum_readiness_score}/100")
    """

    def analyze_utxo(self, utxo: UTXO) -> RiskAssessment:
        """
        Analyzes a single UTXO and returns its risk assessment.

        Args:
            utxo: The UTXO to analyze.

        Returns:
            A RiskAssessment for the given UTXO.
        """
        logger.debug(f"Analyzing UTXO: {utxo.txid}:{utxo.vout}")
        return assess_utxo_risk(utxo)

    def analyze_portfolio(self, utxos: list[UTXO]) -> RiskReport:
        """
        Analyzes a full portfolio of UTXOs and generates a comprehensive risk report.

        The Quantum Readiness Score is calculated as:
            score = 100 - (weighted_risk_value / total_value * 100)
        where higher-risk UTXOs contribute more to the weighted risk.

        Args:
            utxos: A list of UTXO objects representing the portfolio.

        Returns:
            A RiskReport summarizing the portfolio's quantum risk posture.
        """
        if not utxos:
            logger.warning("No UTXOs provided for analysis.")
            return RiskReport(quantum_readiness_score=100.0)

        logger.info(f"Starting portfolio analysis for {len(utxos)} UTXOs...")
        assessments = [self.analyze_utxo(utxo) for utxo in utxos]

        report = RiskReport(
            total_utxos=len(utxos),
            assessments=assessments,
        )

        # Aggregate statistics
        risk_weight_map = {
            RiskLevel.CRITICAL: 1.0,
            RiskLevel.HIGH: 0.75,
            RiskLevel.MEDIUM: 0.5,
            RiskLevel.LOW: 0.2,
            RiskLevel.SAFE: 0.0,
        }
        weighted_risk_sum = 0.0

        for assessment in assessments:
            value = assessment.utxo.value_btc
            report.total_value_btc += value

            if assessment.risk_level == RiskLevel.CRITICAL:
                report.critical_count += 1
                report.critical_value_btc += value
            elif assessment.risk_level == RiskLevel.HIGH:
                report.high_count += 1
                report.high_value_btc += value
            elif assessment.risk_level == RiskLevel.MEDIUM:
                report.medium_count += 1
            elif assessment.risk_level == RiskLevel.LOW:
                report.low_count += 1
            else:
                report.safe_count += 1

            weight = risk_weight_map.get(assessment.risk_level, 0.0)
            weighted_risk_sum += value * weight

        # Calculate Quantum Readiness Score (0 = fully at risk, 100 = fully safe)
        if report.total_value_btc > 0:
            risk_ratio = weighted_risk_sum / report.total_value_btc
            report.quantum_readiness_score = round((1.0 - risk_ratio) * 100, 2)
        else:
            report.quantum_readiness_score = 100.0

        logger.info(
            f"Analysis complete. Quantum Readiness Score: {report.quantum_readiness_score}/100. "
            f"Critical: {report.critical_count}, High: {report.high_count}, "
            f"Medium: {report.medium_count}, Low: {report.low_count}."
        )
        return report
