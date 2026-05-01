"""在线接单自动补价门面。"""

from __future__ import annotations

from typing import Any, Dict, List

from .auto_fill_config import (
    normalize_benben_config,
    normalize_match_strategy,
    normalize_online_order_item_map,
    normalize_online_order_item_meta_map,
    normalize_robot_config,
)
from .auto_fill_selector import build_auto_fill_payloads

AUTO_FILL_SCENE = "online_order_auto_fill"


# 根据场景决定是否执行在线接单自动补价候选选择。
def build_report_payloads(
    sku: str,
    scene: str,
    sku_records: List[Dict[str, Any]],
    online_order_item_ids: List[int],
    online_order_item_metas: List[Dict[str, Any]],
    match_strategy: Dict[str, Any],
) -> List[Dict[str, Any]]:
    # 非自动补价场景直接透传奔奔记录，保持旧链路兼容。
    if scene != AUTO_FILL_SCENE:
        return [
            {
                **record,
                "scene": scene,
                "onlineOrderItemIds": online_order_item_ids,
                "message": "price record collected",
            }
            for record in sku_records
        ]
    # 在线接单自动补价场景走新的候选选择器。
    return build_auto_fill_payloads(
        sku=sku,
        sku_records=sku_records,
        online_order_item_ids=online_order_item_ids,
        online_order_item_metas=online_order_item_metas,
        match_strategy=match_strategy,
    )


__all__ = [
    "AUTO_FILL_SCENE",
    "build_report_payloads",
    "normalize_benben_config",
    "normalize_match_strategy",
    "normalize_robot_config",
    "normalize_online_order_item_map",
    "normalize_online_order_item_meta_map",
]
