import logging
from typing import List, Dict, Any
from bitcoin.core import CBlock, CTransaction, COutPoint, CTxOut
from bitcoin.core.script import CScript, OP_CHECKSIG, OP_DUP, OP_HASH160, OP_EQUALVERIFY
from ..analyzer.bitcoin_analyzer import BitcoinQuantumAnalyzer as BitcoinAnalyzer

logger = logging.getLogger(__name__)

class BTCIndexer:
    """
    BTC 全网地址索引器核心逻辑
    负责解析区块、提取 UTXO 并评估量子风险
    """
    def __init__(self, analyzer: BitcoinAnalyzer):
        self.analyzer = analyzer
        self.indexed_addresses: Dict[str, Dict[str, Any]] = {}

    def process_block(self, block_hex: str) -> List[Dict[str, Any]]:
        """
        解析区块并提取高风险 UTXO
        """
        try:
            block = CBlock.deserialize(bytes.fromhex(block_hex))
            high_risk_utxos = []
            
            for tx in block.vtx:
                txid = tx.GetTxid().hex()[::-1] # Bitcoin txid is little-endian
                for i, vout in enumerate(tx.vout):
                    risk_info = self._analyze_vout(vout, txid, i)
                    if risk_info and risk_info['risk_level'] in ['CRITICAL', 'HIGH']:
                        high_risk_utxos.append(risk_info)
                        # 更新索引库
                        addr = risk_info['address']
                        if addr not in self.indexed_addresses:
                            self.indexed_addresses[addr] = {
                                'total_value': 0,
                                'risk_level': risk_info['risk_level'],
                                'utxo_count': 0
                            }
                        self.indexed_addresses[addr]['total_value'] += risk_info['value_btc']
                        self.indexed_addresses[addr]['utxo_count'] += 1
            
            return high_risk_utxos
        except Exception as e:
            logger.error(f"Error processing block: {e}")
            return []

    def _analyze_vout(self, vout: CTxOut, txid: str, index: int) -> Dict[str, Any]:
        """
        分析单个输出的量子风险
        """
        script_pubkey = vout.scriptPubKey
        value_btc = vout.nValue / 100000000.0
        
        # 简单识别脚本类型
        script_type = "UNKNOWN"
        address = "UNKNOWN"
        
        if len(script_pubkey) == 35 and script_pubkey[0] == 33 and script_pubkey[34] == OP_CHECKSIG:
            script_type = "P2PK"
            # P2PK 地址通常不直接显示，这里简化处理
            address = f"p2pk_{script_pubkey[1:34].hex()}"
        elif len(script_pubkey) == 25 and script_pubkey[0] == OP_DUP and script_pubkey[1] == OP_HASH160:
            script_type = "P2PKH"
            # 简化地址生成逻辑
            address = f"p2pkh_{script_pubkey[3:23].hex()}"
        
        # 调用现有分析器评估风险
        risk_level = self.analyzer._assess_risk(script_type, False) # 假设公钥未暴露
        
        return {
            'txid': txid,
            'index': index,
            'value_btc': value_btc,
            'script_type': script_type,
            'address': address,
            'risk_level': risk_level
        }

    def get_global_stats(self) -> Dict[str, Any]:
        """
        获取索引库的宏观统计数据
        """
        total_value = sum(addr['total_value'] for addr in self.indexed_addresses.values())
        critical_count = sum(1 for addr in self.indexed_addresses.values() if addr['risk_level'] == 'CRITICAL')
        high_count = sum(1 for addr in self.indexed_addresses.values() if addr['risk_level'] == 'HIGH')
        
        return {
            'total_indexed_addresses': len(self.indexed_addresses),
            'total_at_risk_value_btc': total_value,
            'critical_addresses': critical_count,
            'high_risk_addresses': high_count
        }
