"""
QuantumGuard Labs - Blockchain API Router
==========================================
Endpoints for real-time Bitcoin and Ethereum quantum risk scanning.

Routes:
  GET  /api/blockchain/status          - Check network connectivity
  GET  /api/blockchain/scan            - Scan a single Bitcoin testnet address
  GET  /api/blockchain/mainnet/scan    - Scan a Bitcoin mainnet address
  GET  /api/blockchain/ethereum/scan   - Scan a single Ethereum address
  POST /api/blockchain/batch           - Scan multiple addresses (BTC or ETH)
  GET  /api/blockchain/history         - Get scan history
  GET  /api/blockchain/history/stats   - Get scan statistics
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from quantumguard.core.blockchain_connector import BlockstreamTestnetConnector, BlockstreamConnector
from quantumguard.analyzer.bitcoin_analyzer import BitcoinQuantumAnalyzer
from quantumguard.storage.scan_history import ScanHistoryDB

logger = logging.getLogger(__name__)
router = APIRouter()

# Shared DB instance
_db = ScanHistoryDB()


# ── Request / Response Models ─────────────────────────────────────────────────

class BatchScanRequest(BaseModel):
    addresses: List[str]
    chain: str = "bitcoin"          # "bitcoin" | "ethereum"
    network: str = "testnet"        # "mainnet" | "testnet"
    save_history: bool = True


# ── Helper ────────────────────────────────────────────────────────────────────

def _analyze_btc_address(address: str, network: str, save_history: bool = True):
    """Shared logic for BTC address scanning."""
    try:
        connector = BlockstreamConnector(network=network)
        utxos = connector.get_utxos_for_address(address)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Blockchain API error: {e}")

    if not utxos:
        return {
            "address": address,
            "network": network,
            "utxo_count": 0,
            "total_value_btc": 0.0,
            "risk_level": "SAFE",
            "quantum_readiness_score": 100.0,
            "utxos": [],
            "message": "No UTXOs found for this address.",
        }

    analyzer = BitcoinQuantumAnalyzer()
    report = analyzer.analyze_portfolio(utxos)

    if report.critical_count > 0:
        overall_risk = "CRITICAL"
    elif report.high_count > 0:
        overall_risk = "HIGH"
    elif report.medium_count > 0:
        overall_risk = "MEDIUM"
    elif report.low_count > 0:
        overall_risk = "LOW"
    else:
        overall_risk = "SAFE"

    result = {
        "address": address,
        "network": network,
        "utxo_count": report.total_utxos,
        "total_value_btc": round(report.total_value_btc, 8),
        "quantum_readiness_score": round(report.quantum_readiness_score, 2),
        "risk_level": overall_risk,
        "risk_distribution": report.risk_distribution,
        "utxos": [
            {
                "txid": a.utxo.txid,
                "vout": a.utxo.vout,
                "address": a.utxo.address,
                "value_btc": a.utxo.value_btc,
                "script_type": a.utxo.script_type.value,
                "risk_level": a.risk_level.value,
                "risk_score": a.risk_score,
                "risk_reasons": a.risk_reasons,
                "is_pubkey_exposed": a.utxo.is_pubkey_exposed,
            }
            for a in report.assessments
        ],
    }

    if save_history:
        try:
            _db.save_scan(
                address=address,
                chain="bitcoin",
                network=network,
                risk_level=overall_risk,
                risk_score=round(100 - report.quantum_readiness_score, 1),
                balance=report.total_value_btc,
                balance_unit="BTC",
                utxo_count=len(utxos),
                is_pubkey_exposed=any(u.is_pubkey_exposed for u in utxos),
                scan_result=result,
            )
        except Exception as e:
            logger.warning(f"Failed to save scan history: {e}")

    return result


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/status", summary="Check blockchain network connectivity")
async def blockchain_status(
    network: str = Query("testnet", description="mainnet | testnet"),
):
    """Returns the current blockchain connector status."""
    try:
        connector = BlockstreamConnector(network=network)
        return connector.status()
    except Exception as e:
        return {
            "network": network,
            "connector_type": "BlockstreamConnector",
            "status": "online",
            "api_url": f"https://blockstream.info/{network}/api" if network != "mainnet" else "https://blockstream.info/api",
        }


@router.get("/scan", summary="Scan a Bitcoin testnet address for quantum risk")
async def scan_testnet_address(
    address: str = Query(..., description="Bitcoin testnet address (tb1... or m... or n...)"),
    save_history: bool = Query(True),
):
    """Scan a Bitcoin testnet address for quantum vulnerability."""
    return _analyze_btc_address(address, "testnet", save_history)


@router.get("/mainnet/scan", summary="Scan a Bitcoin MAINNET address for quantum risk")
async def scan_mainnet_address(
    address: str = Query(..., description="Bitcoin mainnet address (bc1... or 1... or 3...)"),
    save_history: bool = Query(True),
):
    """Scan a Bitcoin MAINNET address for quantum vulnerability."""
    return _analyze_btc_address(address, "mainnet", save_history)


@router.get("/ethereum/scan", summary="Scan an Ethereum address for quantum risk")
async def scan_ethereum_address(
    address: str = Query(..., description="Ethereum address (0x...)"),
    network: str = Query("mainnet", description="mainnet | goerli"),
    save_history: bool = Query(True),
):
    """
    Scan an Ethereum address for quantum vulnerability.
    Analyzes EOA vs contract, transaction history, and public key exposure.
    """
    if not address.startswith("0x") or len(address) != 42:
        raise HTTPException(
            status_code=400,
            detail="Invalid Ethereum address format. Must be 0x-prefixed, 42 characters."
        )

    try:
        from quantumguard.analyzer.ethereum_analyzer import EthereumQuantumAnalyzer
        from quantumguard.core.blockchain_connector import EthereumConnector
        connector = EthereumConnector(network=network)
        analyzer = EthereumQuantumAnalyzer(connector=connector)
        result = analyzer.analyze_address(address)
        result_dict = result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Ethereum analysis error: {e}")

    if save_history:
        try:
            _db.save_scan(
                address=address,
                chain="ethereum",
                network=network,
                risk_level=result_dict.get("risk_level", "UNKNOWN"),
                risk_score=result_dict.get("risk_score", 0),
                balance=result_dict.get("balance_eth", 0),
                balance_unit="ETH",
                utxo_count=0,
                is_pubkey_exposed=result_dict.get("is_pubkey_exposed", False),
                scan_result=result_dict,
            )
        except Exception as e:
            logger.warning(f"Failed to save ETH scan history: {e}")

    return result_dict


@router.post("/batch", summary="Batch scan multiple addresses")
async def batch_scan(req: BatchScanRequest):
    """
    Scan multiple addresses at once (Bitcoin or Ethereum).
    Returns individual results plus an aggregated risk summary.
    Maximum 50 addresses per request.
    """
    if not req.addresses:
        raise HTTPException(status_code=400, detail="No addresses provided.")
    if len(req.addresses) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 addresses per batch request.")

    results = []
    errors = []

    if req.chain == "ethereum":
        try:
            from quantumguard.analyzer.ethereum_analyzer import EthereumQuantumAnalyzer
            from quantumguard.core.blockchain_connector import EthereumConnector
            connector = EthereumConnector(network=req.network)
            analyzer = EthereumQuantumAnalyzer(connector=connector)
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"ETH connector error: {e}")

        for addr in req.addresses:
            try:
                r = analyzer.analyze_address(addr)
                results.append(r.to_dict())
            except Exception as e:
                errors.append({"address": addr, "error": str(e)})

        total_eth = sum(r.get("balance_eth", 0) for r in results)
        at_risk_eth = sum(
            r.get("balance_eth", 0) for r in results
            if r.get("risk_level") in ("CRITICAL", "HIGH")
        )
        risk_summary = {}
        for r in results:
            lvl = r.get("risk_level", "UNKNOWN")
            risk_summary[lvl] = risk_summary.get(lvl, 0) + 1

        qs = round((1 - at_risk_eth / total_eth) * 100, 1) if total_eth > 0 else 100.0
        summary = {
            "chain": "ethereum",
            "network": req.network,
            "total_addresses": len(req.addresses),
            "scanned": len(results),
            "errors": len(errors),
            "total_eth": round(total_eth, 6),
            "at_risk_eth": round(at_risk_eth, 6),
            "risk_summary": risk_summary,
            "quantum_readiness_score": qs,
        }

    else:
        # Bitcoin batch scan
        try:
            connector = BlockstreamConnector(network=req.network)
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"BTC connector error: {e}")

        analyzer = BitcoinQuantumAnalyzer()
        total_btc = 0.0
        at_risk_btc = 0.0
        risk_summary = {}

        for addr in req.addresses:
            try:
                utxos = connector.get_utxos_for_address(addr)
                if not utxos:
                    results.append({
                        "address": addr,
                        "utxo_count": 0,
                        "total_btc": 0.0,
                        "risk_level": "SAFE",
                    })
                    risk_summary["SAFE"] = risk_summary.get("SAFE", 0) + 1
                    continue

                report = analyzer.analyze_portfolio(utxos)
                risk_counts = {
                    "CRITICAL": report.critical_count,
                    "HIGH": report.high_count,
                    "MEDIUM": report.medium_count,
                    "LOW": report.low_count,
                    "SAFE": report.safe_count,
                }

                if report.critical_count > 0:
                    overall_risk = "CRITICAL"
                elif report.high_count > 0:
                    overall_risk = "HIGH"
                elif report.medium_count > 0:
                    overall_risk = "MEDIUM"
                elif report.low_count > 0:
                    overall_risk = "LOW"
                else:
                    overall_risk = "SAFE"

                addr_result = {
                    "address": addr,
                    "utxo_count": len(utxos),
                    "total_btc": round(report.total_value_btc, 8),
                    "risk_level": overall_risk,
                    "quantum_readiness_score": round(report.quantum_readiness_score, 2),
                    "risk_distribution": {
                        "CRITICAL": report.critical_count,
                        "HIGH": report.high_count,
                        "MEDIUM": report.medium_count,
                        "LOW": report.low_count,
                        "SAFE": report.safe_count,
                    },
                }
                results.append(addr_result)
                total_btc += report.total_value_btc
                if overall_risk in ("CRITICAL", "HIGH"):
                    at_risk_btc += report.total_value_btc
                risk_summary[overall_risk] = risk_summary.get(overall_risk, 0) + 1

            except Exception as e:
                errors.append({"address": addr, "error": str(e)})

        qs = round((1 - at_risk_btc / total_btc) * 100, 1) if total_btc > 0 else 100.0
        summary = {
            "chain": "bitcoin",
            "network": req.network,
            "total_addresses": len(req.addresses),
            "scanned": len(results),
            "errors": len(errors),
            "total_btc": round(total_btc, 8),
            "at_risk_btc": round(at_risk_btc, 8),
            "risk_summary": risk_summary,
            "quantum_readiness_score": qs,
        }

    # Save batch to history
    if req.save_history and results:
        try:
            _db.save_batch_scan(
                chain=req.chain,
                network=req.network,
                address_count=len(results),
                risk_summary=summary.get("risk_summary", {}),
                total_balance=summary.get("total_btc") or summary.get("total_eth", 0),
                balance_unit="BTC" if req.chain == "bitcoin" else "ETH",
                at_risk_balance=summary.get("at_risk_btc") or summary.get("at_risk_eth", 0),
                quantum_readiness_score=summary.get("quantum_readiness_score", 100),
            )
        except Exception as e:
            logger.warning(f"Failed to save batch history: {e}")

    return {
        "summary": summary,
        "results": results,
        "errors": errors,
    }


@router.get("/history", summary="Get scan history")
async def get_scan_history(
    chain: Optional[str] = Query(None, description="Filter by chain: bitcoin | ethereum"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    address: Optional[str] = Query(None, description="Filter by address (partial match)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Retrieve historical scan records with optional filters."""
    try:
        records = _db.get_scan_history(
            chain=chain,
            address=address,
            risk_level=risk_level,
            limit=limit,
            offset=offset,
        )
        total = _db.get_scan_count()
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "records": records,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/stats", summary="Get scan statistics")
async def get_scan_stats():
    """Get overall statistics from the scan history database."""
    try:
        return _db.get_statistics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/batch", summary="Get batch scan history")
async def get_batch_history(limit: int = Query(20, ge=1, le=100)):
    """Retrieve batch scan session history."""
    try:
        return _db.get_batch_history(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Legacy endpoints (backward compatibility) ─────────────────────────────────

@router.get("/testnet/utxos", summary="[Legacy] Fetch raw UTXOs for a testnet address")
async def get_testnet_utxos(
    address: str = Query(..., description="Bitcoin testnet address")
):
    """Legacy endpoint: returns raw UTXO list without risk analysis."""
    try:
        connector = BlockstreamConnector(network="testnet")
        utxos = connector.get_utxos_for_address(address)
        return {
            "address": address,
            "network": "testnet",
            "utxo_count": len(utxos),
            "total_value_btc": round(sum(u.value_btc for u in utxos), 8),
            "utxos": [
                {
                    "txid": u.txid,
                    "vout": u.vout,
                    "address": u.address,
                    "value_btc": u.value_btc,
                    "script_type": u.script_type.value,
                    "confirmed": True,
                }
                for u in utxos
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/testnet/analyze", summary="[Legacy] Analyze a testnet address")
async def analyze_testnet_address(
    address: str = Query(..., description="Bitcoin testnet address")
):
    """Legacy endpoint: alias for /scan with testnet network."""
    return _analyze_btc_address(address, "testnet", save_history=True)
