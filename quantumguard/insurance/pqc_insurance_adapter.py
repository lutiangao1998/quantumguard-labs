import logging
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

class PQCInsuranceAdapter:
    """
    量子风险保险协议适配器
    与去中心化保险协议集成，为通过 QuantumGuard Labs 认证为“量子安全”的资产提供保险服务
    """
    def __init__(self):
        self.supported_insurance_protocols = ["NexusMutual", "Opyn", "QuantumGuard-Native"]
        self.active_policies = {}

    def calculate_premium(self, address: str, amount: float, asset: str, risk_score: float) -> Dict[str, Any]:
        """
        计算保费 (模拟)
        """
        # 基础保费率 0.1% - 0.5%，根据风险评分调整
        premium_rate = 0.001 + (risk_score * 0.004)
        premium_amount = amount * premium_rate
        
        logger.info(f"Calculated premium for {address}: {premium_amount} {asset} (Rate: {premium_rate*100:.2f}%)")
        
        return {
            "address": address,
            "amount": amount,
            "asset": asset,
            "risk_score": risk_score,
            "premium_rate": premium_rate,
            "premium_amount": premium_amount,
            "coverage_period_days": 365,
            "pqc_certified": True
        }

    def purchase_policy(self, address: str, amount: float, asset: str, risk_score: float) -> Dict[str, Any]:
        """
        购买保单 (模拟)
        """
        premium_info = self.calculate_premium(address, amount, asset, risk_score)
        policy_id = f"pol_{str(uuid.uuid4())[:8]}"
        
        policy = {
            "policy_id": policy_id,
            "address": address,
            "amount": amount,
            "asset": asset,
            "premium_paid": premium_info["premium_amount"],
            "status": "ACTIVE",
            "pqc_certified": True,
            "pqc_algorithm": "ML-DSA-65",
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now().replace(year=datetime.now().year + 1)).isoformat()
        }
        
        self.active_policies[policy_id] = policy
        logger.info(f"Purchased policy {policy_id} for {address}")
        
        return policy

    def get_policy_status(self, policy_id: str) -> Dict[str, Any]:
        """
        获取保单状态
        """
        if policy_id not in self.active_policies:
            raise ValueError("Policy not found")
        return self.active_policies[policy_id]

    def get_insurance_info(self) -> Dict[str, Any]:
        return {
            "name": "QuantumGuard Quantum Risk Insurance Adapter",
            "version": "0.1.0-alpha",
            "supported_protocols": self.supported_insurance_protocols
        }
