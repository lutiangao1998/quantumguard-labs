import json
import time
from typing import Dict, Any, List, Optional

class MobileGuardManager:
    """
    移动端监控 App 核心逻辑。
    支持推送通知和实时风险预警。
    """
    def __init__(self):
        self.registered_devices = []

    def register_device(self, device_token: str, user_id: str) -> bool:
        """
        注册移动设备以接收推送通知。
        """
        if device_token not in [d["token"] for d in self.registered_devices]:
            self.registered_devices.append({"token": device_token, "user_id": user_id, "ts": time.time()})
            return True
        return False

    def send_push_notification(self, user_id: str, title: str, body: str, data: Optional[Dict[str, Any]] = None) -> int:
        """
        向指定用户的所有设备发送推送通知。
        """
        target_devices = [d for d in self.registered_devices if d["user_id"] == user_id]
        count = 0
        for device in target_devices:
            # 在原型中，我们模拟发送推送通知
            print(f"Sending push to {device['token']}: {title} - {body}")
            count += 1
        return count

    def get_risk_alerts(self, user_id: str) -> List[Dict[str, Any]]:
        """
        获取用户的实时风险预警列表。
        """
        # 模拟风险预警数据
        return [
            {
                "id": "ALERT-001",
                "type": "WHALE_MOVEMENT",
                "severity": "HIGH",
                "message": "Large vulnerable asset movement detected on BTC network.",
                "timestamp": time.time() - 3600
            },
            {
                "id": "ALERT-002",
                "type": "QUANTUM_THREAT_UPDATE",
                "severity": "MEDIUM",
                "message": "New research paper published on Shor's algorithm optimization.",
                "timestamp": time.time() - 7200
            }
        ]

