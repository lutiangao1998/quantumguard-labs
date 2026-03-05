"""
QuantumGuard Labs - FastAPI Backend
====================================
Main application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from api.routers import analysis, migration, reports, blockchain, keys, intelligence, hardware_wallet
from api.auth import init_db, _ensure_demo_key

app = FastAPI(
    title="QuantumGuard Labs API",
    description="Quantum-safe asset migration infrastructure for digital assets.",
    version="0.2.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS - allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routers
app.include_router(analysis.router,   prefix="/api/analysis",   tags=["Risk Analysis"])
app.include_router(migration.router,  prefix="/api/migration",  tags=["Migration"])
app.include_router(reports.router,    prefix="/api/reports",    tags=["Reports"])
app.include_router(blockchain.router, prefix="/api/blockchain", tags=["Blockchain"])
app.include_router(keys.router,       prefix="/api/keys",       tags=["API Keys"])
app.include_router(intelligence.router, prefix="/api/intelligence", tags=["Intelligence"])
app.include_router(hardware_wallet.router, prefix="/api/hardware_wallet", tags=["Hardware Wallet PQC"])


@app.on_event("startup")
async def startup():
    """Initialize database and create demo key on first run."""
    init_db()
    _ensure_demo_key()


@app.get("/api/health", tags=["Health"])
async def health():
    return {"status": "ok", "version": "0.2.0", "service": "QuantumGuard Labs API"}


# Serve React frontend static files (built output)
# MUST be registered AFTER all API routes
FRONTEND_BUILD = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(FRONTEND_BUILD):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_BUILD, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        index = os.path.join(FRONTEND_BUILD, "index.html")
        return FileResponse(index)
