from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from ..auth import get_current_key
from ...quantumguard.crosschain.pqc_bridge_orchestrator import PQCBridgeOrchestrator
from ...quantumguard.insurance.pqc_insurance_adapter import PQCInsuranceAdapter
from ...quantumguard.qns.qns_resolver import QNSResolver
from ...quantumguard.ai.q_day_predictor import QDayPredictor

router = APIRouter(prefix="/api/defense", tags=["Full-Stack Quantum Defense"])
bridge_orchestrator = PQCBridgeOrchestrator()
insurance_adapter = PQCInsuranceAdapter()
qns_resolver = QNSResolver()
q_day_predictor = QDayPredictor()

@router.get("/info")
async def get_defense_info(api_key: str = Depends(get_current_key)):
    """
    获取全栈量子防御与生态扩展模块信息
    """
    return {
        "bridge_orchestrator": bridge_orchestrator.get_bridge_info(),
        "insurance_adapter": insurance_adapter.get_insurance_info(),
        "qns_resolver": qns_resolver.get_qns_info(),
        "q_day_predictor": q_day_predictor.get_predictor_info()
    }

@router.post("/bridge/initiate")
async def initiate_bridge_request(source_chain: str, target_chain: str, address: str, amount: float, asset: str, api_key: str = Depends(get_current_key)):
    """
    发起跨链请求
    """
    try:
        return bridge_orchestrator.initiate_bridge_request(source_chain, target_chain, address, amount, asset)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/bridge/status/{tx_id}")
async def get_bridge_status(tx_id: str, api_key: str = Depends(get_current_key)):
    """
    查询跨链交易状态
    """
    try:
        return bridge_orchestrator.get_bridge_status(tx_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/insurance/purchase")
async def purchase_policy(address: str, amount: float, asset: str, risk_score: float, api_key: str = Depends(get_current_key)):
    """
    购买量子风险保险
    """
    return insurance_adapter.purchase_policy(address, amount, asset, risk_score)

@router.post("/qns/register")
async def register_domain(domain_name: str, address: str, owner_pqc_pubkey: str, api_key: str = Depends(get_current_key)):
    """
    注册 QNS 域名
    """
    try:
        return qns_resolver.register_domain(domain_name, address, owner_pqc_pubkey)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/qns/resolve/{domain_name}")
async def resolve_domain(domain_name: str, api_key: str = Depends(get_current_key)):
    """
    解析 QNS 域名
    """
    try:
        return qns_resolver.resolve_domain(domain_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/ai/q_day_prediction")
async def get_q_day_prediction(api_key: str = Depends(get_current_key)):
    """
    获取 Q-Day 预测结果
    """
    return q_day_predictor.get_q_day_prediction()

@router.get("/ai/threat_feed")
async def get_threat_feed(api_key: str = Depends(get_current_key)):
    """
    获取实时量子威胁情报
    """
    return q_day_predictor.get_threat_feed()
