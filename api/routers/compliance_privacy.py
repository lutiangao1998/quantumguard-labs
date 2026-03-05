from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Optional
from api.auth import get_current_user
from quantumguard.zkp.zkp_migration import ZKPMigrationProver, ZKPMigrationVerifier
from quantumguard.compliance.compliance_engine import ComplianceEngine
from quantumguard.coldstorage.cold_storage import QSafeColdStorage
from quantumguard.mobile.mobile_guard import MobileGuardManager

router = APIRouter(prefix="/api/compliance_privacy", tags=["Compliance & Privacy"])

# 初始化核心组件
zkp_prover = ZKPMigrationProver()
zkp_verifier = ZKPMigrationVerifier()
compliance_engine = ComplianceEngine()
cold_storage = QSafeColdStorage()
mobile_manager = MobileGuardManager()

@router.post("/zkp/generate_proof")
async def generate_zkp_proof(source: str, target: str, amount: float, secret: str, user=Depends(get_current_user)):
    """生成 ZKP 隐私迁移证明"""
    return zkp_prover.generate_proof(source, target, amount, secret)

@router.post("/compliance/report")
async def generate_compliance_report(region: str, asset_data: Dict[str, Any], audit_results: Dict[str, Any], user=Depends(get_current_user)):
    """生成全球合规报告"""
    try:
        return compliance_engine.generate_compliance_report(region, asset_data, audit_results)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/coldstorage/prepare")
async def prepare_cold_storage_payload(tx_data: Dict[str, Any], user=Depends(get_current_user)):
    """准备冷存储签名负载"""
    payload = cold_storage.prepare_signing_payload(tx_data)
    return {"payload": payload, "qr_data": cold_storage.generate_qr_data(payload)}

@router.post("/mobile/register")
async def register_mobile_device(device_token: str, user=Depends(get_current_user)):
    """注册移动设备"""
    success = mobile_manager.register_device(device_token, user["user_id"])
    return {"success": success}

@router.get("/mobile/alerts")
async def get_mobile_alerts(user=Depends(get_current_user)):
    """获取移动端风险预警"""
    return mobile_manager.get_risk_alerts(user["user_id"])

