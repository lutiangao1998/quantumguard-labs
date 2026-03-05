"""
QuantumGuard Labs - API Key Authentication System
===================================================
Provides API Key-based authentication for institutional clients.

Design:
  - API keys are stored as SHA-256 hashes in a SQLite database (never plaintext).
  - Each key has a tier (free / pro / enterprise) and rate limits.
  - Keys can be scoped to specific operations (read / migrate / admin).
  - FastAPI dependency injection is used for clean, per-route enforcement.

Key format:
  qgl_<tier_prefix>_<32 random hex chars>
  Example: qgl_pro_a3f8c2d1e4b5f6a7b8c9d0e1f2a3b4c5

Usage:
  @router.get("/protected")
  async def protected_route(key_info: APIKeyInfo = Depends(require_api_key)):
      ...

  @router.post("/admin-only")
  async def admin_route(key_info: APIKeyInfo = Depends(require_scope("admin"))):
      ...
"""

import hashlib
import logging
import os
import secrets
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import List, Optional

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import APIKeyHeader

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────

DB_PATH = os.environ.get(
    "QUANTUMGUARD_AUTH_DB",
    os.path.join(os.path.dirname(__file__), "..", "data", "auth.db"),
)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Rate limits per tier (requests per minute)
RATE_LIMITS = {
    "free":       10,
    "pro":        100,
    "enterprise": 1000,
}

# Scopes per tier
TIER_SCOPES = {
    "free":       ["read"],
    "pro":        ["read", "migrate"],
    "enterprise": ["read", "migrate", "admin"],
}


# ── Enums & Data Classes ──────────────────────────────────────────────────────

class KeyTier(str, Enum):
    FREE       = "free"
    PRO        = "pro"
    ENTERPRISE = "enterprise"


@dataclass
class APIKeyInfo:
    """Information about a validated API key."""
    key_id:      str
    name:        str
    tier:        KeyTier
    scopes:      List[str]
    rate_limit:  int        # requests per minute
    created_at:  float
    last_used:   Optional[float]
    is_active:   bool
    org_name:    Optional[str] = None


# ── Database Layer ────────────────────────────────────────────────────────────

def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def _db():
    conn = _get_db()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Initialize the auth database schema."""
    with _db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS api_keys (
                key_id      TEXT PRIMARY KEY,
                key_hash    TEXT NOT NULL UNIQUE,
                name        TEXT NOT NULL,
                tier        TEXT NOT NULL DEFAULT 'free',
                scopes      TEXT NOT NULL DEFAULT 'read',
                org_name    TEXT,
                is_active   INTEGER NOT NULL DEFAULT 1,
                created_at  REAL NOT NULL,
                last_used   REAL,
                request_count INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS rate_limit_log (
                key_id      TEXT NOT NULL,
                window_start REAL NOT NULL,
                request_count INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (key_id, window_start)
            );

            CREATE INDEX IF NOT EXISTS idx_key_hash ON api_keys(key_hash);
            CREATE INDEX IF NOT EXISTS idx_rate_log ON rate_limit_log(key_id, window_start);
        """)
    logger.info("Auth DB initialized at %s", DB_PATH)


# ── Key Management ────────────────────────────────────────────────────────────

def _hash_key(raw_key: str) -> str:
    """Hash an API key for storage (SHA-256)."""
    return hashlib.sha256(raw_key.encode()).hexdigest()


def create_api_key(
    name: str,
    tier: KeyTier = KeyTier.FREE,
    org_name: Optional[str] = None,
    custom_scopes: Optional[List[str]] = None,
) -> tuple[str, APIKeyInfo]:
    """
    Generate a new API key and store its hash in the database.

    Returns:
        (raw_key, APIKeyInfo) — raw_key is shown ONCE and never stored.
    """
    init_db()

    # Generate key: qgl_<tier>_<32 hex chars>
    raw_key = f"qgl_{tier.value}_{secrets.token_hex(16)}"
    key_hash = _hash_key(raw_key)
    key_id = secrets.token_hex(8)
    scopes = custom_scopes or TIER_SCOPES[tier.value]
    now = time.time()

    with _db() as conn:
        conn.execute(
            """INSERT INTO api_keys
               (key_id, key_hash, name, tier, scopes, org_name, is_active, created_at)
               VALUES (?, ?, ?, ?, ?, ?, 1, ?)""",
            (key_id, key_hash, name, tier.value, ",".join(scopes), org_name, now),
        )

    info = APIKeyInfo(
        key_id=key_id,
        name=name,
        tier=tier,
        scopes=scopes,
        rate_limit=RATE_LIMITS[tier.value],
        created_at=now,
        last_used=None,
        is_active=True,
        org_name=org_name,
    )
    logger.info("Created API key %s for '%s' (tier=%s)", key_id, name, tier.value)
    return raw_key, info


def revoke_api_key(key_id: str) -> bool:
    """Revoke an API key by key_id."""
    with _db() as conn:
        cur = conn.execute(
            "UPDATE api_keys SET is_active=0 WHERE key_id=?", (key_id,)
        )
    return cur.rowcount > 0


def list_api_keys(include_inactive: bool = False) -> List[dict]:
    """List all API keys (without hashes)."""
    init_db()
    with _db() as conn:
        if include_inactive:
            rows = conn.execute(
                "SELECT key_id, name, tier, scopes, org_name, is_active, created_at, last_used, request_count FROM api_keys ORDER BY created_at DESC"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT key_id, name, tier, scopes, org_name, is_active, created_at, last_used, request_count FROM api_keys WHERE is_active=1 ORDER BY created_at DESC"
            ).fetchall()
    return [dict(r) for r in rows]


def _lookup_key(raw_key: str) -> Optional[APIKeyInfo]:
    """Look up an API key by its raw value. Returns None if not found/inactive."""
    init_db()
    key_hash = _hash_key(raw_key)
    with _db() as conn:
        row = conn.execute(
            "SELECT * FROM api_keys WHERE key_hash=? AND is_active=1", (key_hash,)
        ).fetchone()
        if not row:
            return None
        # Update last_used and request_count
        conn.execute(
            "UPDATE api_keys SET last_used=?, request_count=request_count+1 WHERE key_hash=?",
            (time.time(), key_hash),
        )

    scopes = row["scopes"].split(",") if row["scopes"] else []
    return APIKeyInfo(
        key_id=row["key_id"],
        name=row["name"],
        tier=KeyTier(row["tier"]),
        scopes=scopes,
        rate_limit=RATE_LIMITS.get(row["tier"], 10),
        created_at=row["created_at"],
        last_used=row["last_used"],
        is_active=bool(row["is_active"]),
        org_name=row["org_name"],
    )


def _check_rate_limit(key_id: str, limit: int) -> bool:
    """
    Check and enforce rate limiting using a 1-minute sliding window.
    Returns True if the request is allowed, False if rate limited.
    """
    now = time.time()
    window = int(now // 60) * 60  # 1-minute window

    with _db() as conn:
        row = conn.execute(
            "SELECT request_count FROM rate_limit_log WHERE key_id=? AND window_start=?",
            (key_id, window),
        ).fetchone()

        if row is None:
            conn.execute(
                "INSERT INTO rate_limit_log (key_id, window_start, request_count) VALUES (?, ?, 1)",
                (key_id, window),
            )
            # Clean up old windows (keep last 5 minutes)
            conn.execute(
                "DELETE FROM rate_limit_log WHERE key_id=? AND window_start < ?",
                (key_id, window - 300),
            )
            return True

        if row["request_count"] >= limit:
            return False

        conn.execute(
            "UPDATE rate_limit_log SET request_count=request_count+1 WHERE key_id=? AND window_start=?",
            (key_id, window),
        )
        return True


# ── FastAPI Security Scheme ───────────────────────────────────────────────────

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Demo key for development/testing (created on first startup)
_DEMO_KEY_FILE = os.path.join(os.path.dirname(DB_PATH), ".demo_key")


def _ensure_demo_key():
    """Create a demo API key on first startup if none exist."""
    init_db()
    keys = list_api_keys()
    if not keys:
        raw_key, info = create_api_key(
            name="Demo Key",
            tier=KeyTier.PRO,
            org_name="QuantumGuard Labs Demo",
        )
        with open(_DEMO_KEY_FILE, "w") as f:
            f.write(raw_key)
        logger.info("Demo API key created: %s (saved to %s)", raw_key, _DEMO_KEY_FILE)
        return raw_key
    return None


async def get_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> Optional[APIKeyInfo]:
    """
    FastAPI dependency: optionally validate an API key.
    Returns None if no key is provided (for public endpoints).
    """
    if not x_api_key:
        return None
    return _lookup_key(x_api_key)


async def require_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> APIKeyInfo:
    """
    FastAPI dependency: require a valid API key.
    Raises 401 if missing, 403 if invalid/revoked, 429 if rate limited.
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Include 'X-API-Key: <your_key>' in the request header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    key_info = _lookup_key(x_api_key)
    if not key_info:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or revoked API key.",
        )

    if not _check_rate_limit(key_info.key_id, key_info.rate_limit):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded ({key_info.rate_limit} req/min for {key_info.tier.value} tier).",
            headers={"Retry-After": "60"},
        )

    return key_info


def require_scope(scope: str):
    """
    FastAPI dependency factory: require a specific scope.

    Usage:
        @router.post("/migrate")
        async def migrate(key: APIKeyInfo = Depends(require_scope("migrate"))):
            ...
    """
    async def _check(key_info: APIKeyInfo = Depends(require_api_key)) -> APIKeyInfo:
        if scope not in key_info.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This endpoint requires '{scope}' scope. Your key has: {key_info.scopes}",
            )
        return key_info
    return _check
