"""在线接单运行时公共工具。"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

SCENE_ONLINE_ORDER = "online_order"
EVENT_ONLINE_ORDER_STATUS = "TASK_ONLINE_ORDER_STATUS"
EVENT_ONLINE_ORDER_QUOTATION = "TASK_ONLINE_ORDER_QUOTATION"
EVENT_ONLINE_ORDER_SUBMIT = "TASK_ONLINE_ORDER_SUBMIT"

NODE_NAME_RECEIVE_QUOTATION = "接单并采集详情"
NODE_NAME_QUEUE_PRICE_FILL = "进入补价队列"
NODE_NAME_WAIT_PRICE_FILL = "等待补价"
NODE_NAME_PRICE_FILLING = "自动补价中"
NODE_NAME_WAIT_SUBMIT = "等待提交"
NODE_NAME_QUEUE_SUBMIT = "进入提交队列"
NODE_NAME_SUBMIT_QUOTATION = "提交报价"
NODE_NAME_COMPLETED = "处理完成"


# 将任意类型尽量转换为布尔值，供运行时参数解析复用。
def to_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    return default


# 将任意值尽量转换为整数，转换失败则返回默认值。
def to_int(value: Any, default: int) -> int:
    if value is None or value == "":
        return default
    try:
        return int(float(value))
    except Exception:
        return default


# 生成当前时间的 ISO 字符串，统一运行时上报格式。
def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


# 拼装报价唯一键，供 Redis 队列和上下文存储共用。
def quotation_key(quotation_id: str, store_id: str) -> str:
    normalized_quotation_id = str(quotation_id or "").strip()
    normalized_store_id = str(store_id or "").strip()
    return f"{normalized_quotation_id}::{normalized_store_id}"


# 把 Redis 队列里的组合键拆回 quotationId 和 storeId。
def split_quotation_key(value: Any) -> Tuple[str, str]:
    parts = str(value or "").split("::", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return str(value or "").strip(), ""


# 把轮询种子统一规范成后续流程稳定依赖的字段结构。
def normalize_seed(seed: Dict[str, Any]) -> Dict[str, Any]:
    row = dict(seed or {})
    row["quotationId"] = str(row.get("quotationId") or row.get("id") or "").strip()
    row["storeId"] = str(row.get("storeId") or "").strip()
    row["inquiryId"] = str(row.get("inquiryId") or "").strip()
    row["supplierCompanyId"] = str(row.get("supplierCompanyId") or "").strip()
    row["statusId"] = str(row.get("statusId") or "").strip()
    row["statusIdDesc"] = str(row.get("statusIdDesc") or "").strip()
    row["displayModelName"] = str(row.get("displayModelName") or "").strip()
    return row


# 安全解析 JSON，解析失败时返回调用方给出的默认值。
def safe_json_loads(value: Any, default: Any) -> Any:
    if value is None or value == "":
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


# 构造 task context，统一在线接单事件的公共字段。
def build_runtime_task_context(
    manual_price_fill_enabled: bool,
    auto_submit_enabled: bool,
) -> Dict[str, Any]:
    return {
        "scene": SCENE_ONLINE_ORDER,
        "kaisiScene": SCENE_ONLINE_ORDER,
        "onlineOrderScene": SCENE_ONLINE_ORDER,
        "manualPriceFillEnabled": manual_price_fill_enabled,
        "autoSubmitEnabled": auto_submit_enabled,
    }


def quotation_task_no(quotation_id: Any, fallback: str = "") -> str:
    normalized_quotation_id = str(quotation_id or "").strip()
    if normalized_quotation_id:
        return normalized_quotation_id
    return str(fallback or "").strip()


def build_quotation_task_context(
    *,
    quotation_id: Any,
    store_id: Any,
    manual_price_fill_enabled: bool,
    auto_submit_enabled: bool,
    backend_task_no: str = "",
    runtime_id: str = "",
    extra_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    quotation_task_id = quotation_task_no(quotation_id, fallback=backend_task_no or runtime_id)
    context = {
        **build_runtime_task_context(
            manual_price_fill_enabled=manual_price_fill_enabled,
            auto_submit_enabled=auto_submit_enabled,
        ),
        "quotationId": str(quotation_id or "").strip(),
        "storeId": str(store_id or "").strip(),
        "backendTaskNo": str(backend_task_no or "").strip(),
        "runtimeId": str(runtime_id or "").strip(),
        "taskId": quotation_task_id,
        "taskNo": quotation_task_id,
    }
    for key, value in (extra_context or {}).items():
        if value is None or value == "":
            continue
        context[key] = value
    return context
