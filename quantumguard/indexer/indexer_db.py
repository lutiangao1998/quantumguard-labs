import sqlite3
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class IndexerDB:
    """
    全网地址索引器数据库管理
    负责持久化存储高风险地址及其风险状态
    """
    def __init__(self, db_path: str = "data/indexer.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """
        初始化数据库表结构
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建地址索引表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS global_addresses (
                    address TEXT PRIMARY KEY,
                    blockchain TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    total_value REAL DEFAULT 0,
                    utxo_count INTEGER DEFAULT 0,
                    is_contract BOOLEAN DEFAULT 0,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建预警记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS whale_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    address TEXT NOT NULL,
                    blockchain TEXT NOT NULL,
                    value_change REAL NOT NULL,
                    alert_type TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (address) REFERENCES global_addresses(address)
                )
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error initializing indexer database: {e}")

    def upsert_address(self, address: str, blockchain: str, risk_level: str, value: float, utxo_count: int = 1, is_contract: bool = False):
        """
        插入或更新地址信息
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO global_addresses (address, blockchain, risk_level, total_value, utxo_count, is_contract, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(address) DO UPDATE SET
                    total_value = total_value + excluded.total_value,
                    utxo_count = utxo_count + excluded.utxo_count,
                    last_seen = CURRENT_TIMESTAMP
            ''', (address, blockchain, risk_level, value, utxo_count, is_contract, datetime.now()))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error upserting address {address}: {e}")

    def get_high_risk_whales(self, min_value: float, blockchain: str = None) -> List[Dict[str, Any]]:
        """
        获取高风险大额地址 (巨鲸)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM global_addresses WHERE total_value >= ? AND risk_level IN ('CRITICAL', 'HIGH')"
            params = [min_value]
            
            if blockchain:
                query += " AND blockchain = ?"
                params.append(blockchain)
            
            query += " ORDER BY total_value DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching high risk whales: {e}")
            return []

    def get_global_stats(self) -> Dict[str, Any]:
        """
        获取全网风险统计数据
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*), SUM(total_value) FROM global_addresses WHERE blockchain = 'BTC'")
            btc_count, btc_value = cursor.fetchone()
            
            cursor.execute("SELECT COUNT(*), SUM(total_value) FROM global_addresses WHERE blockchain = 'ETH'")
            eth_count, eth_value = cursor.fetchone()
            
            conn.close()
            
            return {
                'btc': {'count': btc_count or 0, 'value': btc_value or 0},
                'eth': {'count': eth_count or 0, 'value': eth_value or 0}
            }
        except Exception as e:
            logger.error(f"Error fetching global stats: {e}")
            return {}
