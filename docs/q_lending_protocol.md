# Q-Lending (抗量子借贷) 技术文档

## 1. 简介

Q-Lending 是 QuantumGuard L2 (Q-Chain) 生态中的抗量子借贷协议，旨在为用户提供一个安全、去中心化的借贷市场。用户可以在 Q-Lending 上抵押其 PQC 安全资产以借入其他资产，或提供流动性赚取利息，所有操作均受 Q-Chain 的 PQC 签名保护。

## 2. 核心功能

### 2.1 PQC 资产抵押与借贷

Q-Lending 支持 Q-Chain 上所有 PQC 安全资产作为抵押物和借贷物。用户可以抵押 Q-BTC、Q-ETH、Q-Stablecoin 等资产，借入所需的其他资产。

### 2.2 赚取利息

流动性提供者可以通过向 Q-Lending 协议提供资产来赚取利息。利息率将根据资产的供需关系动态调整。

### 2.3 超额抵押与清算

所有借贷均采用超额抵押模式，确保协议的偿付能力。当抵押品价值低于预设的清算线时，协议将触发清算机制，以保护贷方的利益。

### 2.4 风险管理

Q-Lending 将实施严格的风险管理策略，包括抵押率、清算阈值和动态利率调整，以维护协议的稳定性和安全性。

## 3. 技术实现

### 3.1 智能合约架构

Q-Lending 的核心逻辑将部署为一系列抗量子智能合约在 Q-Chain 上，包括：
*   **Comptroller 合约**：管理借贷市场的核心规则，如抵押因子、清算逻辑等。
*   **cToken 合约**：每个支持借贷的资产都对应一个 cToken 合约，代表用户在协议中的存款份额，并计算利息。
*   **Price Oracle**：提供 PQC 安全资产的实时价格数据，用于抵押品价值评估和清算。

### 3.2 PQC 签名集成

所有与 Q-Lending 智能合约的交互（如 `deposit`、`borrow`、`repay`、`liquidate`）都将通过 `Q-SDK` 进行 PQC 签名。智能合约内部将包含 PQC 签名验证逻辑，确保只有经过 PQC 签名的交易才能被执行。

### 3.3 借贷流程

1.  **用户存款**：用户将 PQC 资产存入 Q-Lending 协议，获得 cToken。
2.  **用户借款**：用户抵押 cToken，借入其他 PQC 资产。协议根据抵押品价值和抵押因子计算最大可借金额。
3.  **利息累积**：借款人需按时支付利息，利息将累积到借款总额中。
4.  **还款与清算**：借款人可以随时还款。若抵押品价值不足，协议将触发清算，由清算人偿还部分借款并获得折扣抵押品。

## 4. 风险与挑战

*   **智能合约漏洞**：所有合约将经过严格的第三方安全审计。
*   **预言机攻击**：依赖于 PQC 安全的价格预言机，防止价格操纵。
*   **清算风险**：市场剧烈波动可能导致大规模清算，需优化清算机制。

## 5. 未来展望

*   集成固定利率借贷和利率互换等高级金融产品。
*   支持闪电贷 (Flash Loans) 功能。
*   与其他 Q-DeFi 协议深度集成，构建更复杂的金融乐高。

source /home/ubuntu/.user_env && cd . && mkdir -p /home/ubuntu/quantumguard-labs/quantumguard/q_defi/q_dao && cat > /home/ubuntu/quantumguard-labs/quantumguard/q_defi/q_dao/q_dao.py << 'EOF'
from typing import Dict, List, Any

class QDAO:
    def __init__(self):
        self.proposals: Dict[str, Dict[str, Any]] = {}
        self.votes: Dict[str, Dict[str, bool]] = {}
        self.next_proposal_id = 1

    def create_proposal(self, proposer: str, title: str, description: str, snapshot_block: int) -> str:
        proposal_id = f"PROPOSAL-{self.next_proposal_id}"
        self.next_proposal_id += 1
        self.proposals[proposal_id] = {
            "proposer": proposer,
            "title": title,
            "description": description,
            "snapshot_block": snapshot_block,
            "status": "Pending", # Pending, Active, Succeeded, Defeated, Executed
            "for_votes": 0,
            "against_votes": 0,
            "voters": set() # Store unique voters
        }
        print(f"Proposal {proposal_id} created by {proposer}: {title}")
        return proposal_id

    def start_voting(self, proposal_id: str):
        if proposal_id not in self.proposals:
            raise ValueError("Proposal not found")
        if self.proposals[proposal_id]["status"] != "Pending":
            raise ValueError("Voting can only start for pending proposals")
        self.proposals[proposal_id]["status"] = "Active"
        print(f"Voting started for proposal {proposal_id}")

    def vote(self, voter: str, proposal_id: str, support: bool, voting_power: int):
        if proposal_id not in self.proposals:
            raise ValueError("Proposal not found")
        if self.proposals[proposal_id]["status"] != "Active":
            raise ValueError("Voting is not active for this proposal")
        if voter in self.proposals[proposal_id]["voters"]:
            raise ValueError("Voter already cast a vote for this proposal")

        if support:
            self.proposals[proposal_id]["for_votes"] += voting_power
        else:
            self.proposals[proposal_id]["against_votes"] += voting_power
        self.proposals[proposal_id]["voters"].add(voter)
        print(f"Voter {voter} cast {voting_power} votes {'for' if support else 'against'} proposal {proposal_id}")

    def end_voting(self, proposal_id: str, quorum_threshold: int, approval_threshold: float):
        if proposal_id not in self.proposals:
            raise ValueError("Proposal not found")
        if self.proposals[proposal_id]["status"] != "Active":
            raise ValueError("Voting is not active for this proposal")

        total_votes = self.proposals[proposal_id]["for_votes"] + self.proposals[proposal_id]["against_votes"]
        if total_votes < quorum_threshold:
            self.proposals[proposal_id]["status"] = "Defeated"
            print(f"Proposal {proposal_id} defeated: Quorum not met")
            return

        if self.proposals[proposal_id]["for_votes"] / total_votes >= approval_threshold:
            self.proposals[proposal_id]["status"] = "Succeeded"
            print(f"Proposal {proposal_id} succeeded")
        else:
            self.proposals[proposal_id]["status"] = "Defeated"
            print(f"Proposal {proposal_id} defeated: Approval threshold not met")

    def execute_proposal(self, proposal_id: str):
        if proposal_id not in self.proposals:
            raise ValueError("Proposal not found")
        if self.proposals[proposal_id]["status"] != "Succeeded":
            raise ValueError("Only succeeded proposals can be executed")
        
        # In a real system, this would trigger on-chain execution of the proposal's payload
        self.proposals[proposal_id]["status"] = "Executed"
        print(f"Proposal {proposal_id} executed")

    def get_proposal_state(self, proposal_id: str) -> Dict[str, Any]:
        if proposal_id not in self.proposals:
            raise ValueError("Proposal not found")
        return self.proposals[proposal_id]

