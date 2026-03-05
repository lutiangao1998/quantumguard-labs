from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any
from ..auth import get_current_key
from ...quantumguard.indexer.indexer_db import IndexerDB

router = APIRouter(prefix="/api/intelligence", tags=["Intelligence"])
db = IndexerDB()

@router.get("/whales")
async def get_high_risk_whales(
    min_value: float = Query(100.0, description="Minimum value in BTC/ETH"),
    blockchain: str = Query(None, regex="^(BTC|ETH)$"),
    api_key: str = Depends(get_current_key)
):
    """
    获取全网高风险大额地址 (巨鲸)
    """
    whales = db.get_high_risk_whales(min_value, blockchain)
    return {
        "count": len(whales),
        "whales": whales
    }

@router.get("/stats")
async def get_global_risk_stats(api_key: str = Depends(get_current_key)):
    """
    获取全球量子风险宏观统计数据
    """
    stats = db.get_global_stats()
    return {
        "timestamp": "2026-03-05T12:00:00Z", # 示例时间
        "global_stats": stats
    }

@router.get("/map")
async def get_risk_map_data(api_key: str = Depends(get_current_key)):
    """
    获取全球风险地图可视化数据
    """
    # 模拟地图数据
    return {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "geometry": {"type": "Point", "coordinates": [-74.006, 40.7128]}, "properties": {"risk": "HIGH", "value": 1500}},
            {"type": "Feature", "geometry": {"type": "Point", "coordinates": [0.1278, 51.5074]}, "properties": {"risk": "CRITICAL", "value": 800}},
            {"type": "Feature", "geometry": {"type": "Point", "coordinates": [116.4074, 39.9042]}, "properties": {"risk": "MEDIUM", "value": 3000}}
        ]
    }
