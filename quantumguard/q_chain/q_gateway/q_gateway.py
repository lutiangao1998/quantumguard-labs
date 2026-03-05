import json
import time
from typing import Dict, Any
from quantumguard.crypto.agility_layer import AgilityLayer

class QGateway:
    """
    Q-Chain 资产跨链网关核心逻辑。
    支持 L1 资产到 Q-Chain 的抗量子存取流程。
    """
    def __init__(self):
        self.agility_layer = AgilityLayer()
        self.pqc_algorithm = "ML-DSA-65" # 默认使用 ML-DSA-65
        self.l1_deposits: Dict[str, Any] = {}
        self.l2_withdrawals: Dict[str, Any] = {}

    def deposit_to_q_chain(self, l1_tx_hash: str, l1_asset_type: str, amount: float, l2_recipient_address: str, l1_private_key: str) -> Dict[str, Any]:
        """
        模拟 L1 资产存入 Q-Chain 的过程。
        需要 L1 交易哈希、资产类型、数量、L2 接收地址和 L1 私钥进行 PQC 签名。
        """
        deposit_data = {
            "l1_tx_hash": l1_tx_hash,
            "l1_asset_type": l1_asset_type,
            "amount": amount,
            "l2_recipient_address": l2_recipient_address,
            "timestamp": int(time.time())
        }
        
        message = json.dumps(deposit_data).encode()
        signature = self.agility_layer.sign(message, l1_private_key, self.pqc_algorithm)
        
        deposit_record = {
            "data": deposit_data,
            "pqc_algorithm": self.pqc_algorithm,
            "signature": signature.hex()
        }
        self.l1_deposits[l1_tx_hash] = deposit_record
        print(f"L1 asset {amount} {l1_asset_type} deposited to Q-Chain for {l2_recipient_address}")
        return deposit_record

    def verify_deposit(self, deposit_record: Dict[str, Any], l1_public_key: str) -> bool:
        """
        验证 L1 存款记录的 PQC 签名。
        """
        data = deposit_record.get("data", {})
        signature = bytes.fromhex(deposit_record.get("signature", ""))
        pqc_algorithm = deposit_record.get("pqc_algorithm")
        message = json.dumps(data).encode()
        
        return self.agility_layer.verify(message, signature, l1_public_key, pqc_algorithm)

    def withdraw_from_q_chain(self, l2_tx_hash: str, l2_asset_type: str, amount: float, l1_recipient_address: str, l2_private_key: str) -> Dict[str, Any]:
        """
        模拟从 Q-Chain 提现到 L1 的过程。
        需要 L2 交易哈希、资产类型、数量、L1 接收地址和 L2 私钥进行 PQC 签名。
        """
        withdrawal_data = {
            "l2_tx_hash": l2_tx_hash,
            "l2_asset_type": l2_asset_type,
            "amount": amount,
            "l1_recipient_address": l1_recipient_address,
            "timestamp": int(time.time())
        }
        
        message = json.dumps(withdrawal_data).encode()
        signature = self.agility_layer.sign(message, l2_private_key, self.pqc_algorithm)
        
        withdrawal_record = {
            "data": withdrawal_data,
            "pqc_algorithm": self.pqc_algorithm,
            "signature": signature.hex()
        }
        self.l2_withdrawals[l2_tx_hash] = withdrawal_record
        print(f"L2 asset {amount} {l2_asset_type} withdrawn from Q-Chain to {l1_recipient_address}")
        return withdrawal_record

    def verify_withdrawal(self, withdrawal_record: Dict[str, Any], l2_public_key: str) -> bool:
        """
        验证 L2 提现记录的 PQC 签名。
        """
        data = withdrawal_record.get("data", {})
        signature = bytes.fromhex(withdrawal_record.get("signature", ""))
        pqc_algorithm = withdrawal_record.get("pqc_algorithm")
        message = json.dumps(data).encode()
        
        return self.agility_layer.verify(message, signature, l2_public_key, pqc_algorithm)

