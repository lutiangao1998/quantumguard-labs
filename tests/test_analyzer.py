"""
QuantumGuard Labs - Unit Tests: Bitcoin Quantum Analyzer
=========================================================
Tests for the risk analysis module, covering script classification,
individual UTXO risk assessment, and portfolio-level analysis.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quantumguard.analyzer.bitcoin_analyzer import (
    BitcoinQuantumAnalyzer,
    classify_script_type,
)
from quantumguard.analyzer.models import RiskLevel, ScriptType, UTXO


class TestScriptClassification(unittest.TestCase):
    """Tests for the classify_script_type function."""

    def test_p2pkh_classification(self):
        """A standard P2PKH script should be classified correctly."""
        # OP_DUP OP_HASH160 <20 bytes> OP_EQUALVERIFY OP_CHECKSIG
        p2pkh_script = "76a914" + "a" * 40 + "88ac"
        script_type, pubkey = classify_script_type(p2pkh_script)
        self.assertEqual(script_type, ScriptType.P2PKH)
        self.assertIsNone(pubkey)

    def test_p2wpkh_classification(self):
        """A SegWit v0 P2WPKH script should be classified correctly."""
        p2wpkh_script = "0014" + "b" * 40
        script_type, pubkey = classify_script_type(p2wpkh_script)
        self.assertEqual(script_type, ScriptType.P2WPKH)
        self.assertIsNone(pubkey)

    def test_p2tr_classification(self):
        """A Taproot P2TR script should be classified correctly."""
        p2tr_script = "5120" + "c" * 64
        script_type, pubkey = classify_script_type(p2tr_script)
        self.assertEqual(script_type, ScriptType.P2TR)
        self.assertIsNone(pubkey)

    def test_p2sh_classification(self):
        """A P2SH script should be classified correctly."""
        p2sh_script = "a914" + "d" * 40 + "87"
        script_type, pubkey = classify_script_type(p2sh_script)
        self.assertEqual(script_type, ScriptType.P2SH)
        self.assertIsNone(pubkey)

    def test_unknown_script(self):
        """An unrecognized script should return UNKNOWN."""
        script_type, pubkey = classify_script_type("deadbeef")
        self.assertEqual(script_type, ScriptType.UNKNOWN)
        self.assertIsNone(pubkey)

    def test_empty_script(self):
        """An empty script should return UNKNOWN."""
        script_type, pubkey = classify_script_type("")
        self.assertEqual(script_type, ScriptType.UNKNOWN)
        self.assertIsNone(pubkey)


class TestUTXORiskAssessment(unittest.TestCase):
    """Tests for individual UTXO risk assessment logic."""

    def setUp(self):
        self.analyzer = BitcoinQuantumAnalyzer()

    def _make_utxo(self, script_type, is_pubkey_exposed=False, is_reused=False, value=1.0):
        return UTXO(
            txid="a" * 64,
            vout=0,
            address="1TestAddress",
            value_btc=value,
            script_type=script_type,
            is_pubkey_exposed=is_pubkey_exposed,
            is_reused=is_reused,
        )

    def test_p2pk_is_critical(self):
        """A P2PK UTXO must be classified as CRITICAL risk."""
        utxo = self._make_utxo(ScriptType.P2PK, is_pubkey_exposed=True)
        assessment = self.analyzer.analyze_utxo(utxo)
        self.assertEqual(assessment.risk_level, RiskLevel.CRITICAL)
        self.assertGreaterEqual(assessment.risk_score, 90)
        self.assertEqual(assessment.migration_priority, 1)

    def test_p2pkh_reused_is_high(self):
        """A reused P2PKH address must be classified as HIGH risk."""
        utxo = self._make_utxo(ScriptType.P2PKH, is_reused=True)
        assessment = self.analyzer.analyze_utxo(utxo)
        self.assertEqual(assessment.risk_level, RiskLevel.HIGH)
        self.assertEqual(assessment.migration_priority, 2)

    def test_p2pkh_unused_is_low(self):
        """An unused P2PKH address must be classified as LOW risk."""
        utxo = self._make_utxo(ScriptType.P2PKH, is_reused=False)
        assessment = self.analyzer.analyze_utxo(utxo)
        self.assertEqual(assessment.risk_level, RiskLevel.LOW)

    def test_p2wpkh_reused_is_high(self):
        """A reused P2WPKH address must be classified as HIGH risk."""
        utxo = self._make_utxo(ScriptType.P2WPKH, is_reused=True)
        assessment = self.analyzer.analyze_utxo(utxo)
        self.assertEqual(assessment.risk_level, RiskLevel.HIGH)

    def test_p2tr_reused_is_medium(self):
        """A reused Taproot address must be classified as MEDIUM risk."""
        utxo = self._make_utxo(ScriptType.P2TR, is_reused=True)
        assessment = self.analyzer.analyze_utxo(utxo)
        self.assertEqual(assessment.risk_level, RiskLevel.MEDIUM)

    def test_p2tr_unused_is_low(self):
        """An unused Taproot address must be classified as LOW risk."""
        utxo = self._make_utxo(ScriptType.P2TR, is_reused=False)
        assessment = self.analyzer.analyze_utxo(utxo)
        self.assertEqual(assessment.risk_level, RiskLevel.LOW)


class TestPortfolioAnalysis(unittest.TestCase):
    """Tests for the portfolio-level analysis and report generation."""

    def setUp(self):
        self.analyzer = BitcoinQuantumAnalyzer()

    def test_empty_portfolio(self):
        """An empty portfolio should return a default report."""
        report = self.analyzer.analyze_portfolio([])
        self.assertEqual(report.total_utxos, 0)
        self.assertEqual(report.quantum_readiness_score, 100.0)

    def test_all_critical_portfolio(self):
        """A portfolio of all P2PK UTXOs should have a very low readiness score."""
        utxos = [
            UTXO(txid="a" * 64, vout=i, address="1P2PK", value_btc=1.0,
                 script_type=ScriptType.P2PK, is_pubkey_exposed=True)
            for i in range(10)
        ]
        report = self.analyzer.analyze_portfolio(utxos)
        self.assertEqual(report.critical_count, 10)
        self.assertLess(report.quantum_readiness_score, 10.0)

    def test_mixed_portfolio_counts(self):
        """A mixed portfolio should correctly count UTXOs by risk level."""
        utxos = [
            UTXO("a" * 64, 0, "addr1", 1.0, ScriptType.P2PK, is_pubkey_exposed=True),
            UTXO("b" * 64, 0, "addr2", 1.0, ScriptType.P2PKH, is_reused=True),
            UTXO("c" * 64, 0, "addr3", 1.0, ScriptType.P2TR, is_reused=True),
            UTXO("d" * 64, 0, "addr4", 1.0, ScriptType.P2PKH, is_reused=False),
            UTXO("e" * 64, 0, "addr5", 1.0, ScriptType.P2WPKH, is_reused=False),
        ]
        report = self.analyzer.analyze_portfolio(utxos)
        self.assertEqual(report.total_utxos, 5)
        self.assertEqual(report.critical_count, 1)
        self.assertEqual(report.high_count, 1)
        self.assertEqual(report.medium_count, 1)
        self.assertEqual(report.low_count, 2)

    def test_readiness_score_range(self):
        """The quantum readiness score must always be between 0 and 100."""
        utxos = [
            UTXO("a" * 64, 0, "addr1", 10.0, ScriptType.P2PK, is_pubkey_exposed=True),
            UTXO("b" * 64, 0, "addr2", 1.0, ScriptType.P2WPKH, is_reused=False),
        ]
        report = self.analyzer.analyze_portfolio(utxos)
        self.assertGreaterEqual(report.quantum_readiness_score, 0.0)
        self.assertLessEqual(report.quantum_readiness_score, 100.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
