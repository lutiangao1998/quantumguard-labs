import time
from typing import Dict, Any, List
from quantumguard.crypto.agility_layer import AgilityLayer

class QConsensusEngine:
    """
    Q-Chain 原生 PQC 共识引擎核心逻辑。
    支持基于 ML-DSA/Falcon 签名的区块签名与验证。
    """
    def __init__(self):
        self.agility_layer = AgilityLayer()
        self.pqc_algorithm = "ML-DSA-65" # 默认使用 ML-DSA-65
        self.validators: Dict[str, str] = {}

    def register_validator(self, validator_id: str, public_key: str):
        """
        注册验证者及其 PQC 公钥。
        """
        self.validators[validator_id] = public_key

    def create_block(self, block_data: Dict[str, Any], private_key: str, validator_id: str) -> Dict[str, Any]:
        """
        创建并签名一个 Q-Chain 区块。
        """
        if validator_id not in self.validators:
            raise ValueError(f"Validator {validator_id} not registered.")

        block = {
            "timestamp": int(time.time()),
            "data": block_data,
            "validator_id": validator_id,
            "pqc_algorithm": self.pqc_algorithm,
            "signature": ""
        }
        
        message = json.dumps(block["data"]).encode()
        signature = self.agility_layer.sign(message, private_key, self.pqc_algorithm)
        block["signature"] = signature.hex()
        
        return block

    def verify_block(self, block: Dict[str, Any]) -> bool:
        """
        验证一个 Q-Chain 区块的签名。
        """
        validator_id = block.get("validator_id")
        signature = bytes.fromhex(block.get("signature", ""))
        pqc_algorithm = block.get("pqc_algorithm")
        message = json.dumps(block.get("data", {})).encode()

        if not validator_id or validator_id not in self.validators:
            return False

        public_key = self.validators[validator_id]
        
        return self.agility_layer.verify(message, signature, public_key, pqc_algorithm)

