"""
QuantumGuard Labs - API Key Management Router
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.auth import (
    APIKeyInfo, KeyTier,
    create_api_key, revoke_api_key, list_api_keys,
    require_api_key, require_scope,
    _ensure_demo_key,
)

router = APIRouter()


# ── Request / Response Models ─────────────────────────────────────────────────

class CreateKeyRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Human-readable name for this key")
    tier: KeyTier = Field(KeyTier.FREE, description="Key tier: free | pro | enterprise")
    org_name: Optional[str] = Field(None, description="Organization name")


class CreateKeyResponse(BaseModel):
    raw_key: str = Field(..., description="The API key — shown ONCE, store it securely!")
    key_id: str
    name: str
    tier: str
    scopes: List[str]
    rate_limit_per_min: int
    warning: str = "Store this key securely. It will NOT be shown again."


class KeyListItem(BaseModel):
    key_id: str
    name: str
    tier: str
    scopes: List[str]
    org_name: Optional[str]
    is_active: bool
    created_at: float
    last_used: Optional[float]
    request_count: int


class RevokeResponse(BaseModel):
    success: bool
    message: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=CreateKeyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new API key",
    description="""
Create a new API key for accessing QuantumGuard Labs API.

**Tiers:**
- `free` — 10 req/min, read-only access
- `pro` — 100 req/min, read + migrate access
- `enterprise` — 1000 req/min, full access including admin

**Note:** The raw key is shown ONLY ONCE. Store it securely.

This endpoint requires an existing API key with `admin` scope.
For initial setup, use the demo key from the server startup log.
""",
)
async def create_key(
    req: CreateKeyRequest,
    _: APIKeyInfo = Depends(require_scope("admin")),
):
    """Create a new API key (requires admin scope)."""
    raw_key, info = create_api_key(
        name=req.name,
        tier=req.tier,
        org_name=req.org_name,
    )
    return CreateKeyResponse(
        raw_key=raw_key,
        key_id=info.key_id,
        name=info.name,
        tier=info.tier.value,
        scopes=info.scopes,
        rate_limit_per_min=info.rate_limit,
    )


@router.get(
    "/",
    response_model=List[KeyListItem],
    summary="List all API keys",
)
async def list_keys(
    include_inactive: bool = False,
    _: APIKeyInfo = Depends(require_scope("admin")),
):
    """List all API keys (requires admin scope)."""
    keys = list_api_keys(include_inactive=include_inactive)
    result = []
    for k in keys:
        scopes = k["scopes"].split(",") if isinstance(k["scopes"], str) else k["scopes"]
        result.append(KeyListItem(
            key_id=k["key_id"],
            name=k["name"],
            tier=k["tier"],
            scopes=scopes,
            org_name=k.get("org_name"),
            is_active=bool(k["is_active"]),
            created_at=k["created_at"],
            last_used=k.get("last_used"),
            request_count=k.get("request_count", 0),
        ))
    return result


@router.delete(
    "/{key_id}",
    response_model=RevokeResponse,
    summary="Revoke an API key",
)
async def revoke_key(
    key_id: str,
    _: APIKeyInfo = Depends(require_scope("admin")),
):
    """Revoke an API key by its ID (requires admin scope)."""
    success = revoke_api_key(key_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Key '{key_id}' not found.")
    return RevokeResponse(success=True, message=f"Key '{key_id}' has been revoked.")


@router.get(
    "/me",
    summary="Get info about the current API key",
)
async def get_current_key(key_info: APIKeyInfo = Depends(require_api_key)):
    """Return information about the API key used in this request."""
    return {
        "key_id":     key_info.key_id,
        "name":       key_info.name,
        "tier":       key_info.tier.value,
        "scopes":     key_info.scopes,
        "rate_limit": key_info.rate_limit,
        "org_name":   key_info.org_name,
        "last_used":  key_info.last_used,
    }


@router.post(
    "/demo",
    summary="Get or create the demo API key (development only)",
    include_in_schema=os.environ.get("QUANTUMGUARD_ENV") != "production",
)
async def get_demo_key():
    """
    Return the demo API key for development/testing.
    This endpoint is disabled in production.
    """
    if os.environ.get("QUANTUMGUARD_ENV") == "production":
        raise HTTPException(status_code=404, detail="Not found.")

    demo_key_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "data", ".demo_key"
    )
    if os.path.exists(demo_key_file):
        with open(demo_key_file) as f:
            raw_key = f.read().strip()
        return {
            "demo_key": raw_key,
            "note": "This is the development demo key. Do not use in production.",
            "usage": "Add header: X-API-Key: " + raw_key,
        }

    raw_key = _ensure_demo_key()
    if raw_key:
        return {
            "demo_key": raw_key,
            "note": "Demo key created. Do not use in production.",
            "usage": "Add header: X-API-Key: " + raw_key,
        }

    return {"error": "Could not retrieve demo key. Check server logs."}
