from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from ..auth import get_current_key
from ...quantumguard.orchestrator.multisig_builder import MultisigMigrationBuilder
from ...quantumguard.orchestrator.contract_migrator import SmartContractMigrator
from ...quantumguard.orchestrator.auto_migration_trigger import AutoMigrationTrigger
from ...quantumguard.notifications.webhook_manager import WebhookManager

router = APIRouter(prefix="/api/ecosystem", tags=["Ecosystem & Automation"])
multisig_builder = MultisigMigrationBuilder()
contract_migrator = SmartContractMigrator()
auto_migration_trigger = AutoMigrationTrigger()
webhook_manager = WebhookManager()

@router.get("/info")
async def get_ecosystem_info(api_key: str = Depends(get_current_key)):
    """
    获取机构级生态与自动化模块信息
    """
    return {
        "multisig_builder": multisig_builder.get_multisig_info(),
        "contract_migrator": contract_migrator.get_migrator_info(),
        "auto_migration_trigger": auto_migration_trigger.get_trigger_info(),
        "webhook_manager": webhook_manager.get_webhook_info()
    }

@router.post("/multisig/parse")
async def parse_multisig_address(address: str, blockchain: str, api_key: str = Depends(get_current_key)):
    """
    解析多签地址
    """
    try:
        return multisig_builder.parse_multisig_address(address, blockchain)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/multisig/plan")
async def build_multisig_migration_tx(multisig_info: Dict[str, Any], destination_address: str, api_key: str = Depends(get_current_key)):
    """
    构建多签迁移交易模板
    """
    return multisig_builder.build_multisig_migration_tx(multisig_info, destination_address)

@router.post("/contract/analyze")
async def analyze_contract_ownership(contract_address: str, api_key: str = Depends(get_current_key)):
    """
    分析合约所有权模式
    """
    return contract_migrator.analyze_contract_ownership(contract_address)

@router.post("/contract/transfer_ownership")
async def build_ownership_transfer_tx(contract_info: Dict[str, Any], new_owner_address: str, api_key: str = Depends(get_current_key)):
    """
    构建所有权转移交易模板
    """
    return contract_migrator.build_ownership_transfer_tx(contract_info, new_owner_address)

@router.post("/automation/trigger")
async def trigger_auto_migration(event_data: Dict[str, Any], policy: Dict[str, Any], api_key: str = Depends(get_current_key)):
    """
    触发自动化迁移
    """
    return auto_migration_trigger.trigger_auto_migration(event_data, policy)

@router.post("/webhooks/subscribe")
async def subscribe_webhook(webhook_url: str, event_types: List[str], api_key: str = Depends(get_current_key)):
    """
    订阅 Webhook
    """
    return webhook_manager.subscribe_webhook(webhook_url, event_types)
