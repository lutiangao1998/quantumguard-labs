"""
QuantumGuard Labs — Scan History Storage
==========================================
Persists scan results, migration plans, and audit logs to SQLite.

This module provides a lightweight, zero-dependency storage layer
suitable for single-instance deployments. For multi-instance or
high-throughput scenarios, replace with PostgreSQL via SQLAlchemy.

Tables:
  scan_records     — Individual address scan results (BTC + ETH)
  batch_scans      — Multi-address batch scan sessions
  migration_plans  — Generated migration plans
  audit_events     — Immutable audit log entries

Usage:
    db = ScanHistoryDB()
    db.save_scan(address="bc1q...", chain="bitcoin", result={...})
    history = db.get_scan_history(limit=50)
"""

import json
import logging
import os
import sqlite3
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = os.environ.get("QG_DB_PATH", "/tmp/quantumguard.db")


# ── Data Classes ──────────────────────────────────────────────────────────────

@dataclass
class ScanRecord:
    id: str
    address: str
    chain: str                  # "bitcoin" | "ethereum"
    network: str                # "mainnet" | "testnet" | "goerli"
    risk_level: str
    risk_score: float
    balance: float
    balance_unit: str           # "BTC" | "ETH"
    utxo_count: int
    is_pubkey_exposed: bool
    scan_result_json: str       # Full JSON of scan result
    scanned_at: float
    label: Optional[str] = None  # User-defined label

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "address": self.address,
            "chain": self.chain,
            "network": self.network,
            "risk_level": self.risk_level,
            "risk_score": self.risk_score,
            "balance": self.balance,
            "balance_unit": self.balance_unit,
            "utxo_count": self.utxo_count,
            "is_pubkey_exposed": self.is_pubkey_exposed,
            "scanned_at": self.scanned_at,
            "label": self.label,
            "scan_result": json.loads(self.scan_result_json) if self.scan_result_json else {},
        }


@dataclass
class BatchScanRecord:
    id: str
    chain: str
    network: str
    address_count: int
    risk_summary: str           # JSON: {"CRITICAL": 0, "HIGH": 3, ...}
    total_balance: float
    balance_unit: str
    at_risk_balance: float
    quantum_readiness_score: float
    scanned_at: float
    label: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "chain": self.chain,
            "network": self.network,
            "address_count": self.address_count,
            "risk_summary": json.loads(self.risk_summary) if self.risk_summary else {},
            "total_balance": self.total_balance,
            "balance_unit": self.balance_unit,
            "at_risk_balance": self.at_risk_balance,
            "quantum_readiness_score": self.quantum_readiness_score,
            "scanned_at": self.scanned_at,
            "label": self.label,
        }


# ── Database Manager ──────────────────────────────────────────────────────────

class ScanHistoryDB:
    """
    SQLite-backed storage for scan history, migration plans, and audit logs.
    Thread-safe via connection-per-operation pattern.
    """

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS scan_records (
        id              TEXT PRIMARY KEY,
        address         TEXT NOT NULL,
        chain           TEXT NOT NULL DEFAULT 'bitcoin',
        network         TEXT NOT NULL DEFAULT 'mainnet',
        risk_level      TEXT NOT NULL,
        risk_score      REAL NOT NULL DEFAULT 0.0,
        balance         REAL NOT NULL DEFAULT 0.0,
        balance_unit    TEXT NOT NULL DEFAULT 'BTC',
        utxo_count      INTEGER NOT NULL DEFAULT 0,
        is_pubkey_exposed INTEGER NOT NULL DEFAULT 0,
        scan_result_json TEXT,
        scanned_at      REAL NOT NULL,
        label           TEXT,
        UNIQUE(address, chain, network, scanned_at)
    );

    CREATE INDEX IF NOT EXISTS idx_scan_address ON scan_records(address);
    CREATE INDEX IF NOT EXISTS idx_scan_chain   ON scan_records(chain);
    CREATE INDEX IF NOT EXISTS idx_scan_risk    ON scan_records(risk_level);
    CREATE INDEX IF NOT EXISTS idx_scan_time    ON scan_records(scanned_at DESC);

    CREATE TABLE IF NOT EXISTS batch_scans (
        id                      TEXT PRIMARY KEY,
        chain                   TEXT NOT NULL DEFAULT 'bitcoin',
        network                 TEXT NOT NULL DEFAULT 'mainnet',
        address_count           INTEGER NOT NULL DEFAULT 0,
        risk_summary            TEXT,
        total_balance           REAL NOT NULL DEFAULT 0.0,
        balance_unit            TEXT NOT NULL DEFAULT 'BTC',
        at_risk_balance         REAL NOT NULL DEFAULT 0.0,
        quantum_readiness_score REAL NOT NULL DEFAULT 0.0,
        scanned_at              REAL NOT NULL,
        label                   TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_batch_time ON batch_scans(scanned_at DESC);

    CREATE TABLE IF NOT EXISTS migration_plans (
        id              TEXT PRIMARY KEY,
        policy          TEXT NOT NULL,
        utxo_count      INTEGER NOT NULL DEFAULT 0,
        total_btc       REAL NOT NULL DEFAULT 0.0,
        batch_count     INTEGER NOT NULL DEFAULT 0,
        plan_json       TEXT,
        created_at      REAL NOT NULL,
        label           TEXT
    );

    CREATE TABLE IF NOT EXISTS audit_events (
        id          TEXT PRIMARY KEY,
        event_type  TEXT NOT NULL,
        entity_id   TEXT,
        description TEXT,
        data_json   TEXT,
        created_at  REAL NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_events(created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_audit_type ON audit_events(event_type);
    """

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self._init_db()
        logger.info(f"ScanHistoryDB initialized at {db_path}")

    def _init_db(self):
        """Initialize database schema."""
        with self._conn() as conn:
            conn.executescript(self.SCHEMA)

    @contextmanager
    def _conn(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ── Scan Records ──────────────────────────────────────────────────────────

    def save_scan(
        self,
        address: str,
        chain: str,
        network: str,
        risk_level: str,
        risk_score: float,
        balance: float,
        balance_unit: str,
        utxo_count: int,
        is_pubkey_exposed: bool,
        scan_result: Dict[str, Any],
        label: Optional[str] = None,
    ) -> str:
        """Save a single address scan result. Returns the record ID."""
        record_id = str(uuid.uuid4())
        now = time.time()

        with self._conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO scan_records
                (id, address, chain, network, risk_level, risk_score,
                 balance, balance_unit, utxo_count, is_pubkey_exposed,
                 scan_result_json, scanned_at, label)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_id, address, chain, network, risk_level, risk_score,
                    balance, balance_unit, utxo_count, int(is_pubkey_exposed),
                    json.dumps(scan_result), now, label,
                ),
            )

        self._log_audit("SCAN", record_id, f"Scanned {chain} address {address} → {risk_level}")
        logger.info(f"Saved scan record {record_id} for {address} ({chain}/{network})")
        return record_id

    def get_scan_history(
        self,
        chain: Optional[str] = None,
        address: Optional[str] = None,
        risk_level: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Retrieve scan history with optional filters."""
        query = "SELECT * FROM scan_records WHERE 1=1"
        params = []

        if chain:
            query += " AND chain = ?"
            params.append(chain)
        if address:
            query += " AND address LIKE ?"
            params.append(f"%{address}%")
        if risk_level:
            query += " AND risk_level = ?"
            params.append(risk_level)

        query += " ORDER BY scanned_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self._conn() as conn:
            rows = conn.execute(query, params).fetchall()

        return [
            ScanRecord(
                id=r["id"],
                address=r["address"],
                chain=r["chain"],
                network=r["network"],
                risk_level=r["risk_level"],
                risk_score=r["risk_score"],
                balance=r["balance"],
                balance_unit=r["balance_unit"],
                utxo_count=r["utxo_count"],
                is_pubkey_exposed=bool(r["is_pubkey_exposed"]),
                scan_result_json=r["scan_result_json"],
                scanned_at=r["scanned_at"],
                label=r["label"],
            ).to_dict()
            for r in rows
        ]

    def get_scan_count(self) -> int:
        """Get total number of scan records."""
        with self._conn() as conn:
            return conn.execute("SELECT COUNT(*) FROM scan_records").fetchone()[0]

    def get_address_history(self, address: str) -> List[Dict[str, Any]]:
        """Get all scan records for a specific address (risk trend over time)."""
        return self.get_scan_history(address=address, limit=100)

    def delete_scan(self, record_id: str) -> bool:
        """Delete a scan record by ID."""
        with self._conn() as conn:
            result = conn.execute("DELETE FROM scan_records WHERE id = ?", (record_id,))
        return result.rowcount > 0

    # ── Batch Scans ───────────────────────────────────────────────────────────

    def save_batch_scan(
        self,
        chain: str,
        network: str,
        address_count: int,
        risk_summary: Dict[str, int],
        total_balance: float,
        balance_unit: str,
        at_risk_balance: float,
        quantum_readiness_score: float,
        label: Optional[str] = None,
    ) -> str:
        """Save a batch scan session summary. Returns the batch ID."""
        batch_id = str(uuid.uuid4())
        now = time.time()

        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO batch_scans
                (id, chain, network, address_count, risk_summary,
                 total_balance, balance_unit, at_risk_balance,
                 quantum_readiness_score, scanned_at, label)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    batch_id, chain, network, address_count,
                    json.dumps(risk_summary), total_balance, balance_unit,
                    at_risk_balance, quantum_readiness_score, now, label,
                ),
            )

        self._log_audit("BATCH_SCAN", batch_id, f"Batch scan: {address_count} {chain} addresses, score={quantum_readiness_score:.1f}")
        return batch_id

    def get_batch_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieve batch scan history."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM batch_scans ORDER BY scanned_at DESC LIMIT ?", (limit,)
            ).fetchall()

        return [
            BatchScanRecord(
                id=r["id"],
                chain=r["chain"],
                network=r["network"],
                address_count=r["address_count"],
                risk_summary=r["risk_summary"],
                total_balance=r["total_balance"],
                balance_unit=r["balance_unit"],
                at_risk_balance=r["at_risk_balance"],
                quantum_readiness_score=r["quantum_readiness_score"],
                scanned_at=r["scanned_at"],
                label=r["label"],
            ).to_dict()
            for r in rows
        ]

    # ── Migration Plans ───────────────────────────────────────────────────────

    def save_migration_plan(
        self,
        policy: str,
        utxo_count: int,
        total_btc: float,
        batch_count: int,
        plan_data: Dict[str, Any],
        label: Optional[str] = None,
    ) -> str:
        """Save a migration plan. Returns the plan ID."""
        plan_id = str(uuid.uuid4())
        now = time.time()

        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO migration_plans
                (id, policy, utxo_count, total_btc, batch_count, plan_json, created_at, label)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (plan_id, policy, utxo_count, total_btc, batch_count,
                 json.dumps(plan_data), now, label),
            )

        self._log_audit("MIGRATION_PLAN", plan_id, f"Migration plan created: {policy}, {utxo_count} UTXOs, {batch_count} batches")
        return plan_id

    def get_migration_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieve migration plan history."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM migration_plans ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()

        return [
            {
                "id": r["id"],
                "policy": r["policy"],
                "utxo_count": r["utxo_count"],
                "total_btc": r["total_btc"],
                "batch_count": r["batch_count"],
                "created_at": r["created_at"],
                "label": r["label"],
                "plan": json.loads(r["plan_json"]) if r["plan_json"] else {},
            }
            for r in rows
        ]

    # ── Audit Log ─────────────────────────────────────────────────────────────

    def _log_audit(
        self,
        event_type: str,
        entity_id: str,
        description: str,
        data: Optional[Dict] = None,
    ):
        """Append an immutable audit event."""
        event_id = str(uuid.uuid4())
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO audit_events (id, event_type, entity_id, description, data_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (event_id, event_type, entity_id, description,
                 json.dumps(data) if data else None, time.time()),
            )

    def get_audit_log(self, limit: int = 100, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve audit log entries."""
        query = "SELECT * FROM audit_events"
        params = []
        if event_type:
            query += " WHERE event_type = ?"
            params.append(event_type)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with self._conn() as conn:
            rows = conn.execute(query, params).fetchall()

        return [
            {
                "id": r["id"],
                "event_type": r["event_type"],
                "entity_id": r["entity_id"],
                "description": r["description"],
                "data": json.loads(r["data_json"]) if r["data_json"] else None,
                "created_at": r["created_at"],
            }
            for r in rows
        ]

    # ── Statistics ────────────────────────────────────────────────────────────

    def get_statistics(self) -> Dict[str, Any]:
        """Get overall database statistics."""
        with self._conn() as conn:
            scan_count = conn.execute("SELECT COUNT(*) FROM scan_records").fetchone()[0]
            batch_count = conn.execute("SELECT COUNT(*) FROM batch_scans").fetchone()[0]
            plan_count = conn.execute("SELECT COUNT(*) FROM migration_plans").fetchone()[0]
            audit_count = conn.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0]

            risk_dist = {}
            for row in conn.execute(
                "SELECT risk_level, COUNT(*) as cnt FROM scan_records GROUP BY risk_level"
            ).fetchall():
                risk_dist[row["risk_level"]] = row["cnt"]

            latest_scan = conn.execute(
                "SELECT scanned_at FROM scan_records ORDER BY scanned_at DESC LIMIT 1"
            ).fetchone()

        return {
            "total_scans": scan_count,
            "total_batch_scans": batch_count,
            "total_migration_plans": plan_count,
            "total_audit_events": audit_count,
            "risk_distribution": risk_dist,
            "latest_scan_at": latest_scan["scanned_at"] if latest_scan else None,
            "db_path": self.db_path,
        }
