# Q-Chain 开发者 SDK (Q-SDK) 开发指南

## 1. 简介

Q-SDK 是 QuantumGuard L2 (Q-Chain) 的核心开发者工具包，旨在简化抗量子智能合约的开发、部署和交互。通过 Q-SDK，开发者可以轻松地利用 Q-Chain 的原生 PQC 安全特性，构建面向未来的去中心化应用 (DApp)。

## 2. 核心功能

### 2.1 PQC 密钥管理

Q-SDK 提供了一套完整的 PQC 密钥生成、导入和导出工具，支持 Q-Chain 原生 PQC 算法（如 ML-DSA、Falcon）。

### 2.2 抗量子合约部署

开发者可以使用 Q-SDK 部署基于 PQC 签名的智能合约。部署过程中的交易签名将自动使用指定的 PQC 算法进行。

### 2.3 抗量子合约交互

Q-SDK 允许开发者通过 PQC 签名与 Q-Chain 上的智能合约进行交互，确保所有函数调用和状态变更都具备抗量子安全性。

### 2.4 交易构建与签名

提供高级 API，用于构建和 PQC 签名 Q-Chain 上的交易，包括资产转移、合约调用等。

## 3. 技术实现

### 3.1 核心依赖

Q-SDK 依赖于 QuantumGuard Labs 的 `AgilityLayer` 模块，该模块封装了底层 `liboqs` 库，提供了统一的 PQC 签名和验证接口。

### 3.2 密钥生成

`QSDK.generate_pqc_keypair()` 方法将调用 `AgilityLayer` 生成指定 PQC 算法的私钥和公钥。

### 3.3 合约部署流程

1.  **准备合约字节码**：开发者提供编译后的智能合约字节码和构造函数参数。
2.  **构建部署交易**：Q-SDK 内部构建一个包含合约字节码和参数的部署交易。
3.  **PQC 签名**：开发者使用其 PQC 私钥对部署交易进行签名。
4.  **广播部署**：Q-SDK 将签名后的部署交易广播到 Q-Chain 网络。

### 3.4 合约交互流程

1.  **指定合约与方法**：开发者提供目标合约地址、要调用的方法名和参数。
2.  **构建交互交易**：Q-SDK 内部构建一个包含方法调用指令和参数的交易。
3.  **PQC 签名**：开发者使用其 PQC 私钥对交互交易进行签名。
4.  **广播交互**：Q-SDK 将签名后的交互交易广播到 Q-Chain 网络。

## 4. 示例代码 (Python)

```python
from quantumguard.q_chain.q_sdk.q_sdk import QSDK

# 初始化 SDK
sdk = QSDK()

# 1. 生成 PQC 密钥对
keypair = sdk.generate_pqc_keypair()
print("Generated PQC Keypair:", keypair)

# 2. 模拟部署抗量子智能合约
contract_bytecode = "0x6080604052..." # 示例字节码
constructor_args = {"initialValue": 100}

deployment_result = sdk.deploy_pqc_contract(
    contract_bytecode,
    constructor_args,
    bytes.fromhex(keypair["private_key"])
)
print("Contract Deployment Result:", deployment_result)

# 3. 模拟与抗量子智能合约交互
contract_address = deployment_result["contract_address"]
interaction_result = sdk.interact_with_pqc_contract(
    contract_address,
    "setValue",
    {"newValue": 200},
    bytes.fromhex(keypair["private_key"])
)
print("Contract Interaction Result:", interaction_result)
```

## 5. 未来展望

*   支持更多编程语言的 SDK 版本（如 JavaScript, Go）。
*   集成开发环境 (IDE) 插件。
*   提供更丰富的合约模板和库。
