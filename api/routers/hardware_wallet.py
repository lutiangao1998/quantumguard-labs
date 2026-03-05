from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from ..auth import get_current_key
from ...quantumguard.orchestrator.hardware_pqc import HardwarePQCPlugin

router = APIRouter(prefix="/api/hardware_wallet", tags=["Hardware Wallet PQC"])
plugin = HardwarePQCPlugin()

@router.get("/info")
async def get_plugin_info(api_key: str = Depends(get_current_key)):
    """
    获取硬件钱包 PQC 插件信息
    """
    return plugin.get_plugin_info()

@router.post("/connect")
async def connect_hardware_wallet(device_type: str, api_key: str = Depends(get_current_key)):
    """
    连接硬件钱包
    """
    result = plugin.connect_device(device_type)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@router.post("/prepare_pqc_signing")
async def prepare_pqc_signing(tx_data: Dict[str, Any], algorithm: str, api_key: str = Depends(get_current_key)):
    """
    准备 PQC 签名负载
    """
    try:
        payload = plugin.prepare_pqc_signing_payload(tx_data, algorithm)
        return {"status": "success", "payload": payload}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/verify_pqc_signature")
async def verify_pqc_signature(signature: str, pubkey: str, algorithm: str, api_key: str = Depends(get_current_key)):
    """
    验证 PQC 签名
    """
    is_valid = plugin.verify_hardware_pqc_signature(signature, pubkey, algorithm)
    return {"status": "success", "is_valid": is_valid}
