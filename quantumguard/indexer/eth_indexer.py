import logging
from typing import List, Dict, Any
from web3 import Web3
from ..analyzer.ethereum_analyzer import EthereumQuantumAnalyzer

logger = logging.getLogger(__name__)

class ETHIndexer:
    """
    ETH 全网地址索引器核心逻辑
    负责解析区块、提取 EOA 账户并评估量子风险
    """
    def __init__(self, analyzer: EthereumQuantumAnalyzer, rpc_url: str = "https://eth.llamarpc.com"):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.analyzer = analyzer
        self.indexed_addresses: Dict[str, Dict[str, Any]] = {}

    def process_block(self, block_number: int) -> List[Dict[str, Any]]:
        """
        解析区块并提取高风险 EOA 账户
        """
        try:
            block = self.w3.eth.get_block(block_number, full_transactions=True)
            high_risk_accounts = []
            
            # 提取区块中涉及的所有地址
            addresses_to_check = set()
            for tx in block.transactions:
                addresses_to_check.add(tx['from'])
                if tx['to']:
                    addresses_to_check.add(tx['to'])
            
            for addr in addresses_to_check:
                risk_info = self._analyze_address(addr)
                if risk_info and risk_info['risk_level'] in ['CRITICAL', 'HIGH']:
                    high_risk_accounts.append(risk_info)
                    # 更新索引库
                    if addr not in self.indexed_addresses:
                        self.indexed_addresses[addr] = {
                            'balance_eth': risk_info['balance_eth'],
                            'risk_level': risk_info['risk_level'],
                            'is_contract': risk_info['is_contract']
                        }
            
            return high_risk_accounts
        except Exception as e:
            logger.error(f"Error processing ETH block {block_number}: {e}")
            return []

    def _analyze_address(self, address: str) -> Dict[str, Any]:
        """
        分析单个以太坊地址的量子风险
        """
        try:
            # 检查是否为合约
            code = self.w3.eth.get_code(address)
            is_contract = len(code) > 0
            
            # 获取余额
            balance_wei = self.w3.eth.get_balance(address)
            balance_eth = float(self.w3.from_wei(balance_wei, 'ether'))
            
            # 调用现有分析器评估风险
            # 假设公钥未暴露 (对于 ETH，公钥在发送第一笔交易后暴露)
            risk_level = self.analyzer._assess_risk(is_contract, False)
            
            return {
                'address': address,
                'balance_eth': balance_eth,
                'is_contract': is_contract,
                'risk_level': risk_level
            }
        except Exception as e:
            logger.error(f"Error analyzing ETH address {address}: {e}")
            return None

    def get_global_stats(self) -> Dict[str, Any]:
        """
        获取索引库的宏观统计数据
        """
        total_value = sum(addr['balance_eth'] for addr in self.indexed_addresses.values())
        critical_count = sum(1 for addr in self.indexed_addresses.values() if addr['risk_level'] == 'CRITICAL')
        
        return {
            'total_indexed_addresses': len(self.indexed_addresses),
            'total_at_risk_value_eth': total_value,
            'critical_addresses': critical_count
        }
