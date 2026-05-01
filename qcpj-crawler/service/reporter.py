from __future__ import annotations

import threading
from datetime import datetime
from typing import Any, Dict, Optional

from uuid import uuid4

from service.backend_client import post_online_order_event, post_online_order_quotation

_lock = threading.Lock()
_task_context_lock = threading.Lock()
_task_contexts: Dict[str, Dict[str, Any]] = {}


def _safe_send(message: Dict[str, Any], task_no: str) -> None:
    """
    统一事件上报入口：改为 HTTP ingest，沿用后端登录鉴权。
    """
    with _lock:
        post_online_order_event(task_no, message)


def register_task_context(task_id: str, context: Optional[Dict[str, Any]]) -> None:
    normalized_task_id = str(task_id or "").strip()
    if not normalized_task_id or not isinstance(context, dict):
        return
    cleaned = {key: value for key, value in context.items() if value is not None and value != ""}
    if not cleaned:
        return
    with _task_context_lock:
        current = _task_contexts.setdefault(normalized_task_id, {})
        current.update(cleaned)


def clear_task_context(task_id: str) -> None:
    normalized_task_id = str(task_id or "").strip()
    if not normalized_task_id:
        return
    with _task_context_lock:
        _task_contexts.pop(normalized_task_id, None)


def _resolve_task_context(task_id: str) -> Dict[str, Any]:
    normalized_task_id = str(task_id or "").strip()
    if not normalized_task_id:
        return {}
    with _task_context_lock:
        return dict(_task_contexts.get(normalized_task_id) or {})


def _merge_payload(task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    task_context = _resolve_task_context(task_id)
    return {
        **task_context,
        **(payload or {}),
        "sentAt": datetime.now().isoformat(timespec="seconds"),
    }


def _emit(task_id: str, event: str, payload: Dict[str, Any]) -> None:
    normalized_task_id = str(task_id or "").strip()
    body = {
        "event": event,
        "taskNo": normalized_task_id,
        "eventId": uuid4().hex,
        "payload": _merge_payload(task_id, payload),
    }
    _safe_send(body, normalized_task_id)


def flush_online_order_quotation(task_id: str = "") -> None:
    # Quotation sync is sent immediately over HTTP now. Keep this as a no-op for callers.
    return None


def report_custom_event(task_id: str, event: str, payload: Optional[Dict[str, Any]] = None) -> None:
    _emit(task_id, event, payload or {})


def report_task_start(task_id: str, task_type: str, trigger_by: str, total_count: int) -> None:
    _emit(task_id, "TASK_START", {
        "taskType": task_type,
        "triggerBy": trigger_by,
        "totalCount": total_count,
        "message": "任务已启动",
    })


def report_log(task_id: str, message: str, level: str = "INFO") -> None:
    _emit(task_id, "TASK_LOG", {
        "level": level,
        "message": message,
    })


def report_progress(task_id: str, success_count: int, fail_count: int, total_count: int, message: str = "") -> None:
    _emit(task_id, "TASK_PROGRESS", {
        "successCount": success_count,
        "failCount": fail_count,
        "totalCount": total_count,
        "message": message or "任务进度已更新",
    })


def report_result(task_id: str, result: Dict[str, Any]) -> None:
    flush_online_order_quotation(task_id)
    _emit(task_id, "TASK_RESULT", result)


def report_item(task_id: str, payload: Dict[str, Any]) -> None:
    _emit(task_id, "TASK_ITEM", payload)


def report_online_order_quotation(task_id: str, payload: Dict[str, Any]) -> None:
    normalized_task_id = str(task_id or "").strip()
    body = _merge_payload(normalized_task_id, payload)
    post_online_order_quotation(normalized_task_id, body)


def report_online_order_quotation_batch(task_id: str, payloads: list[Dict[str, Any]]) -> None:
    for payload in payloads or []:
        if isinstance(payload, dict):
            report_online_order_quotation(task_id, payload)


def report_control(task_id: str, action: str, message: str = "") -> None:
    _emit(task_id, "TASK_CONTROL", {
        "action": action,
        "message": message or f"任务控制动作: {action}",
    })


def report_error(task_id: str, message: str, sku: str = "", supplier_name: str = "") -> None:
    _emit(task_id, "TASK_ERROR", {
        "sku": sku,
        "supplierName": supplier_name,
        "error": message,
    })


def report_done(task_id: str, success_count: int, fail_count: int, total_count: int, message: str = "任务已完成") -> None:
    flush_online_order_quotation(task_id)
    _emit(task_id, "TASK_DONE", {
        "successCount": success_count,
        "failCount": fail_count,
        "totalCount": total_count,
        "message": message,
    })
    clear_task_context(task_id)


def ws_status(reconnect: bool = True) -> Dict[str, Any]:
    _ = reconnect
    # 当前版本已切换为 HTTP ingest，兼容保留该状态接口。
    return {"connected": True, "error": ""}
