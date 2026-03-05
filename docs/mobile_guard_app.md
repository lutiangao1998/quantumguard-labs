# 移动端监控 App (Mobile Guard) 技术文档

## 1. 简介

Mobile Guard 是 QuantumGuard Labs 的移动端伴侣应用，旨在为用户提供实时的量子威胁监控和资产风险预警。无论用户身在何处，都能第一时间掌握其资产的量子安全状态。

## 2. 核心功能

### 2.1 实时推送通知 (Push Notifications)
集成 Firebase Cloud Messaging (FCM) 和 Apple Push Notification service (APNs)，在检测到重大风险或资产异动时，立即向用户发送推送通知。

### 2.2 风险仪表盘 (Risk Dashboard)
提供简洁直观的移动端看板，展示用户的量子就绪评分、风险资产分布和最新的全网量子威胁情报。

### 2.3 快速响应操作 (Quick Actions)
支持在移动端直接触发预设的紧急迁移计划（Emergency Migration），实现秒级风险响应。

## 3. 技术架构

*   **前端框架**：React Native (跨平台支持 iOS 和 Android)。
*   **推送服务**：FCM / APNs。
*   **API 通信**：通过 HTTPS 与 QuantumGuard Labs 后端进行安全交互。
*   **本地存储**：使用加密的本地存储保护用户的配置和预警历史。

## 4. 安全特性

*   **生物识别认证**：支持 FaceID / TouchID 登录。
*   **端到端加密**：所有敏感数据传输均经过加密处理。
*   **无私钥设计**：App 本身不存储私钥，仅作为监控和触发工具。

## 5. 未来扩展

*   支持多语言版本。
*   集成硬件钱包蓝牙连接支持。
*   增加社交分享功能（如分享量子安全成就）。
