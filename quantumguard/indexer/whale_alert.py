import logging
from typing import List, Dict, Any
from .indexer_db import IndexerDB

logger = logging.getLogger(__name__)

class WhaleAlertSystem:
    """
    巨鲸预警系统
    实时监控高风险大额地址异动并触发通知
    """
    def __init__(self, db: IndexerDB):
        self.db = db
        self.min_whale_value = 100.0 # 默认 100 BTC/ETH 为巨鲸

    def check_for_alerts(self, new_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        检查新抓取的数据是否触发预警
        """
        alerts = []
        for item in new_data:
            if item['value_btc'] >= self.min_whale_value and item['risk_level'] in ['CRITICAL', 'HIGH']:
                alert = {
                    'address': item['address'],
                    'blockchain': 'BTC',
                    'value': item['value_btc'],
                    'risk_level': item['risk_level'],
                    'alert_type': 'LARGE_RISK_ASSET_DETECTED'
                }
                alerts.append(alert)
                logger.warning(f"🚨 WHALE ALERT: {alert['alert_type']} on {alert['blockchain']}! Address: {alert['address']}, Value: {alert['value']} BTC")
        
        return alerts

    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取最近的预警记录
        """
        # 模拟从数据库获取最近预警
        return [
            {"address": "1P5ZED... (Satoshi?)", "blockchain": "BTC", "value": 50.0, "risk_level": "CRITICAL", "timestamp": "2026-03-05 12:00:00"},
            {"address": "0xde0b... (Ethereum Foundation)", "blockchain": "ETH", "value": 1200.0, "risk_level": "HIGH", "timestamp": "2026-03-05 11:30:00"}
        ]
