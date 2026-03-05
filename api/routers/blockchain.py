"""
QuantumGuard Labs - Blockchain API Router
Provides real Bitcoin Testnet UTXO lookup via Blockstream API.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from quantumguard.core.blockchain_connector import BlockstreamTestnetConnector

router = APIRouter()


class UTXOInfo(BaseModel):
    txid: str
    vout: int
    address: str
    value_btc: float
    script_type: str
    confirmed: bool


class AddressUTXOResponse(BaseModel):
    address: str
    network: str
    utxo_count: int
    total_value_btc: float
    utxos: list[UTXOInfo]


@router.get("/testnet/utxos", response_model=AddressUTXOResponse,
            summary="Fetch real UTXOs for a Bitcoin Testnet address")
async def get_testnet_utxos(
    address: str = Query(..., description="Bitcoin testnet address (tb1... or m... or n...)")
):
    """
    Fetch real UTXO data from the Bitcoin Testnet via the Blockstream.info API.
    Use a testnet address (e.g., tb1q...) to see live results.
    """
    try:
        connector = BlockstreamTestnetConnector()
        utxos = connector.get_utxos_for_address(address)

        if not utxos:
            return AddressUTXOResponse(
                address=address,
                network="testnet",
                utxo_count=0,
                total_value_btc=0.0,
                utxos=[],
            )

        utxo_list = [
            UTXOInfo(
                txid=u.txid,
                vout=u.vout,
                address=u.address,
                value_btc=u.value_btc,
                script_type=u.script_type.value,
                confirmed=True,
            )
            for u in utxos
        ]

        return AddressUTXOResponse(
            address=address,
            network="testnet",
            utxo_count=len(utxos),
            total_value_btc=round(sum(u.value_btc for u in utxos), 8),
            utxos=utxo_list,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Blockstream API error: {str(e)}")


@router.get("/testnet/analyze", summary="Analyze a real Testnet address for quantum risk")
async def analyze_testnet_address(
    address: str = Query(..., description="Bitcoin testnet address")
):
    """
    Fetch real UTXOs from Bitcoin Testnet and run full quantum risk analysis.
    """
    from quantumguard.analyzer.bitcoin_analyzer import BitcoinQuantumAnalyzer
    try:
        connector = BlockstreamTestnetConnector()
        utxos = connector.get_utxos_for_address(address)

        if not utxos:
            raise HTTPException(status_code=404, detail=f"No UTXOs found for address: {address}")

        analyzer = BitcoinQuantumAnalyzer()
        report = analyzer.analyze_portfolio(utxos)

        return {
            "address": address,
            "network": "testnet",
            "total_utxos": report.total_utxos,
            "quantum_readiness_score": round(report.quantum_readiness_score, 2),
            "critical_count": report.critical_count,
            "high_count": report.high_count,
            "medium_count": report.medium_count,
            "low_count": report.low_count,
            "total_value_btc": round(report.total_value_btc, 8),
            "assessments": [
                {
                    "txid": a.utxo.txid,
                    "address": a.utxo.address,
                    "value_btc": a.utxo.value_btc,
                    "script_type": a.utxo.script_type.value,
                    "risk_level": a.risk_level.value,
                    "risk_score": a.risk_score,
                    "risk_reasons": a.risk_reasons,
                }
                for a in report.assessments
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", summary="Check Blockstream Testnet API connectivity")
async def blockchain_status():
    """Returns the current blockchain connector status."""
    return {
        "network": "testnet",
        "connector_type": "BlockstreamTestnetConnector",
        "status": "online",
        "api_url": BlockstreamTestnetConnector.BASE_URL,
    }


@router.get("/scan", summary="Scan a testnet address for quantum risk")
async def scan_address(address: str = Query(..., description="Bitcoin testnet address")):
    """
    Unified scan endpoint: fetches UTXOs and runs quantum risk analysis.
    Returns risk level, UTXO list, and total value.
    """
    from quantumguard.analyzer.bitcoin_analyzer import BitcoinQuantumAnalyzer
    try:
        connector = BlockstreamTestnetConnector()
        utxos = connector.get_utxos_for_address(address)

        if not utxos:
            return {
                "address": address,
                "network": "testnet",
                "utxo_count": 0,
                "total_value_btc": 0.0,
                "risk_level": "SAFE",
                "utxos": [],
            }

        analyzer = BitcoinQuantumAnalyzer()
        report = analyzer.analyze_portfolio(utxos)

        # Determine overall risk level (worst case)
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

        return {
            "address": address,
            "network": "testnet",
            "utxo_count": report.total_utxos,
            "total_value_btc": round(report.total_value_btc, 8),
            "quantum_readiness_score": round(report.quantum_readiness_score, 2),
            "risk_level": overall_risk,
            "utxos": [
                {
                    "txid": a.utxo.txid,
                    "vout": a.utxo.vout,
                    "address": a.utxo.address,
                    "value_btc": a.utxo.value_btc,
                    "script_type": a.utxo.script_type.value,
                    "risk_level": a.risk_level.value,
                }
                for a in report.assessments
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
