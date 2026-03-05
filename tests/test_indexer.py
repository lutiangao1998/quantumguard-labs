import unittest
import sys
import os

# 确保可以导入 quantumguard 模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from quantumguard.indexer.btc_indexer import BTCIndexer
from quantumguard.analyzer.bitcoin_analyzer import BitcoinQuantumAnalyzer as BitcoinAnalyzer
from quantumguard.indexer.eth_indexer import ETHIndexer
from quantumguard.analyzer.ethereum_analyzer import EthereumQuantumAnalyzer
from quantumguard.indexer.indexer_db import IndexerDB

class TestBTCIndexer(unittest.TestCase):
    def setUp(self):
        self.analyzer = BitcoinAnalyzer()
        self.indexer = BTCIndexer(self.analyzer)

    def test_process_empty_block(self):
        # 模拟一个空的区块 hex (仅包含版本、前一区块哈希、Merkle 根、时间、难度、Nonce 和 0 个交易)
        # 这是一个简化的 80 字节区块头 + 0 交易计数
        empty_block_hex = "01000000" + "00"*32 + "00"*32 + "00000000" + "00000000" + "00000000" + "00"
        results = self.indexer.process_block(empty_block_hex)
        self.assertEqual(len(results), 0)

    def test_global_stats_initial(self):
        stats = self.indexer.get_global_stats()
        self.assertEqual(stats['total_indexed_addresses'], 0)
        self.assertEqual(stats['total_at_risk_value_btc'], 0)

class TestETHIndexer(unittest.TestCase):
    def setUp(self):
        self.analyzer = EthereumQuantumAnalyzer()
        # 使用模拟 RPC URL 避免网络请求
        self.indexer = ETHIndexer(self.analyzer, rpc_url="http://localhost:8545")

    def test_global_stats_initial(self):
        stats = self.indexer.get_global_stats()
        self.assertEqual(stats['total_indexed_addresses'], 0)
        self.assertEqual(stats['total_at_risk_value_eth'], 0)

class TestIndexerDB(unittest.TestCase):
    def setUp(self):
        self.db_path = "data/test_indexer.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db = IndexerDB(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_upsert_and_get_whales(self):
        self.db.upsert_address("addr1", "BTC", "CRITICAL", 100.5)
        self.db.upsert_address("addr2", "ETH", "HIGH", 50.2)
        
        whales = self.db.get_high_risk_whales(min_value=50)
        self.assertEqual(len(whales), 2)
        self.assertEqual(whales[0]['address'], "addr1")
        self.assertEqual(whales[1]['address'], "addr2")

    def test_global_stats(self):
        self.db.upsert_address("addr1", "BTC", "CRITICAL", 100.5)
        self.db.upsert_address("addr2", "ETH", "HIGH", 50.2)
        
        stats = self.db.get_global_stats()
        self.assertEqual(stats['btc']['count'], 1)
        self.assertEqual(stats['btc']['value'], 100.5)
        self.assertEqual(stats['eth']['count'], 1)
        self.assertEqual(stats['eth']['value'], 50.2)

if __name__ == '__main__':
    unittest.main()
