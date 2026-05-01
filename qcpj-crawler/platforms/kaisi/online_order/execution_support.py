"""在线接单执行链路公共辅助函数。"""

from __future__ import annotations

import time
from typing import Any, Dict, List

from platforms.kaisi.common.task_state import should_terminate, wait_if_paused
from service.reporter import (
    report_log,
    report_online_order_quotation,
)

from .runtime_support import quotation_task_no

PLATFORM_NAME = "kaisi"


# 安全转整数，失败时返回默认值。
def to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


# 安全转布尔值。
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


# 把逗号串或数组统一转成字符串列表。
def to_str_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [item.strip() for item in text.split(",") if item.strip()] if text else []


# 带暂停/终止感知的轮询休眠。
def sleep_poll(task_id: str, seconds: int) -> None:
    for _ in range(max(1, int(seconds or 1))):
        if should_terminate(task_id):
            return
        wait_if_paused(task_id)
        if should_terminate(task_id):
            return
        time.sleep(1)


# 统一提取报价主键。
def quotation_id(quotation: Dict[str, Any]) -> str:
    return str(quotation.get("id") or quotation.get("quotationId") or "")


# 把一批报价 id 拼成日志友好的文本。
def join_quotation_ids(quotations: List[Dict[str, Any]]) -> str:
    ids = [quotation_id(item) for item in quotations]
    ids = [item for item in ids if item]
    return ",".join(ids) if ids else "-"


# 兼容秒级和毫秒级时间戳。
def to_millis(value: Any) -> int:
    try:
        if value is None or value == "":
            return 0
        number = int(float(value))
        return number * 1000 if abs(number) < 100000000000 else number
    except Exception:
        return 0


# 从多个报价里选出最新一条。
def pick_latest_quotation(candidates: List[Dict[str, Any]], prefer_quotation_id: str = "") -> Dict[str, Any]:
    rows = [row for row in (candidates or []) if isinstance(row, dict)]
    if not rows:
        return {}
    preferred_id = str(prefer_quotation_id or "").strip()
    if preferred_id:
        preferred_rows = [row for row in rows if quotation_id(row) == preferred_id]
        if preferred_rows:
            rows = preferred_rows
    rows.sort(
        key=lambda row: (
            to_millis(row.get("lastUpdatedStamp")),
            to_millis(row.get("createdStamp")),
            quotation_id(row),
        ),
        reverse=True,
    )
    return rows[0]


# 把报价明细行转换成前端在线接单表格结构。
def to_online_item(record: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "inquiryId": str(record.get("inquiryId") or ""),
        "resolveResultId": str(record.get("resolveResultId") or ""),
        "partsNum": str(record.get("partsNum") or ""),
        "partsName": str(record.get("partsName") or ""),
        "partsBrandQuality": str(record.get("partsBrandQuality") or ""),
        "brandId": str(record.get("brandId") or ""),
        "brandName": str(record.get("brandName") or ""),
        "quantity": record.get("quantity"),
        "price": record.get("price"),
        "btPrice": record.get("btPrice"),
        "source": str(record.get("source") or ""),
    }


# 组装在线接单报价 payload。
def build_payload(
    task_id: str,
    quotation: Dict[str, Any],
    process_result: Dict[str, Any],
    enable_benben_price_fill: bool,
) -> Dict[str, Any]:
    quote_records = process_result.get("quoteRecords") or []
    return {
        "platform": PLATFORM_NAME,
        "scene": "online_order",
        "taskId": task_id,
        "quotationId": str(process_result.get("quotationId") or quotation.get("id") or quotation.get("quotationId") or ""),
        "inquiryId": str(process_result.get("inquiryId") or quotation.get("inquiryId") or ""),
        "storeId": str(process_result.get("storeId") or quotation.get("storeId") or ""),
        "statusId": str(quotation.get("statusId") or process_result.get("statusId") or ""),
        "statusIdDesc": str(quotation.get("statusIdDesc") or process_result.get("statusIdDesc") or ""),
        "displayModelName": str(quotation.get("displayModelName") or process_result.get("displayModelName") or ""),
        "itemCount": process_result.get("itemCount") if process_result.get("itemCount") is not None else quotation.get("itemCount"),
        "unclaimedItemCount": process_result.get("unclaimedItemCount") if process_result.get("unclaimedItemCount") is not None else quotation.get("unclaimedItemCount"),
        "effectiveQuotedItemCount": process_result.get("effectiveQuotedItemCount") if process_result.get("effectiveQuotedItemCount") is not None else quotation.get("effectiveQuotedItemCount"),
        "createdStamp": quotation.get("createdStamp") if quotation.get("createdStamp") is not None else process_result.get("createdStamp"),
        "lastUpdatedStamp": quotation.get("lastUpdatedStamp") if quotation.get("lastUpdatedStamp") is not None else process_result.get("lastUpdatedStamp"),
        "enableBenbenPriceFill": enable_benben_price_fill,
        "items": [to_online_item(row) for row in quote_records],
        "rawQuotation": quotation,
    }


# 把初始同步报价列表标准化并去重。
def normalize_sync_quotations(value: Any) -> List[Dict[str, Any]]:
    rows = [value] if isinstance(value, dict) else value
    if not isinstance(rows, (list, tuple, set)):
        return []
    result = []
    seen = set()
    for item in rows:
        if not isinstance(item, dict):
            continue
        inquiry_id = str(item.get("inquiryId") or "").strip()
        normalized_quotation_id = str(item.get("quotationId") or item.get("id") or "").strip()
        store_id = str(item.get("storeId") or "").strip()
        key = inquiry_id or f"{normalized_quotation_id}:{store_id}"
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(
            {
                "inquiryId": inquiry_id,
                "quotationId": normalized_quotation_id,
                "id": normalized_quotation_id,
                "storeId": store_id,
                "statusId": str(item.get("statusId") or "").strip(),
                "statusIdDesc": str(item.get("statusIdDesc") or "").strip(),
                "displayModelName": str(item.get("displayModelName") or "").strip(),
                "itemCount": item.get("itemCount"),
                "unclaimedItemCount": item.get("unclaimedItemCount"),
                "effectiveQuotedItemCount": item.get("effectiveQuotedItemCount"),
                "createdStamp": item.get("createdStamp"),
                "lastUpdatedStamp": item.get("lastUpdatedStamp"),
            }
        )
    return result


# 统一上传报价详情，单条和批量上传共用这里。
def flush_payloads(task_id: str, payloads: List[Dict[str, Any]]) -> int:
    rows = [item for item in (payloads or []) if isinstance(item, dict)]
    if not rows:
        return 0
    for row in rows:
        quotation_id = str(row.get("quotationId") or row.get("id") or "").strip()
        report_online_order_quotation(quotation_task_no(quotation_id, fallback=task_id), row)
    return len(rows)


# 接单成功后生成等待补价提示文案。
def waiting_after_accept_message(quotation_id_text: str, enable_benben_price_fill: bool) -> str:
    wait_text = "等待自动补价" if enable_benben_price_fill else "等待人工补价"
    return f"{quotation_id_text or '-'} 已接单，当前{wait_text}"


# 在当前轮处理完成后主动把任务置为暂停，等待前端人工继续。
def pause_before_next_round(task_id: str, quotation_ids: List[str]) -> None:
    summary = ",".join([str(item).strip() for item in quotation_ids if str(item).strip()]) or "-"
    reason = "当前轮处理完成，等待下一轮补价和提交"
    report_log(task_id, f"{reason}: quotationIds={summary}", level="WARNING")
    wait_if_paused(task_id)
