from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional

from core.task_queue import create_task_record, get_task
from service.backend_client import create_backend_task
from service.reporter import register_task_context

from .direct_actions import run_price_fill_once, run_submit_once
from .runtime_engine import OnlineOrderRuntime
from .runtime_store import OnlineOrderRuntimeStore, create_runtime_redis_client
from .runtime_support import build_runtime_task_context

DEFAULT_ONLINE_ORDER_RUNTIME_ID = "KAISI_ONLINE_ORDER_RUNTIME"

_runtime_lock = threading.Lock()
_runtimes: Dict[str, OnlineOrderRuntime] = {}
ACTIVE_RUNTIME_STATUSES = {"RUNNING"}


def resolve_runtime_id(task_id: str = "") -> str:
    normalized_task_id = str(task_id or "").strip()
    return normalized_task_id or DEFAULT_ONLINE_ORDER_RUNTIME_ID


def get_runtime(task_id: str = "") -> Optional[OnlineOrderRuntime]:
    normalized_task_id = resolve_runtime_id(task_id)
    with _runtime_lock:
        return _runtimes.get(normalized_task_id)


def get_active_runtime(task_id: str = "") -> Optional[OnlineOrderRuntime]:
    runtime = get_runtime(task_id)
    if runtime is None:
        return None
    status = str(runtime.status().get("status") or "").strip().upper()
    if status in ACTIVE_RUNTIME_STATUSES:
        return runtime
    return None


def start_online_order_runtime(params: Dict[str, Any], task_id: str = "") -> Dict[str, Any]:
    normalized_params = _ensure_backend_task_no(params)
    normalized_task_id = resolve_runtime_id(task_id)
    with _runtime_lock:
        current = _runtimes.get(normalized_task_id)
        if current is not None:
            current_status = str(current.status().get("status") or "").strip().upper()
            if current_status not in {"STOPPED", "FAILED", "NOT_FOUND"}:
                return current.status()
        redis_client = create_runtime_redis_client()
        OnlineOrderRuntimeStore(task_id=normalized_task_id, redis_client=redis_client).reset_runtime()
        runtime = OnlineOrderRuntime(
            task_id=normalized_task_id,
            params=normalized_params,
            redis=redis_client,
        )
        _runtimes[normalized_task_id] = runtime
    register_task_context(
        normalized_task_id,
        build_runtime_task_context(
            manual_price_fill_enabled=runtime.manual_price_fill_enabled,
            auto_submit_enabled=runtime.auto_submit_enabled,
        ),
    )
    if not get_task(normalized_task_id):
        create_task_record(normalized_task_id, normalized_params)
    return runtime.start()


def _ensure_backend_task_no(params: Dict[str, Any]) -> Dict[str, Any]:
    normalized_params = dict(params or {})
    backend_task_no = str(
        normalized_params.get("backendTaskNo")
        or normalized_params.get("taskId")
        or normalized_params.get("taskNo")
        or ""
    ).strip()
    if not backend_task_no:
        backend_task_no = create_backend_task(
            task_type=str(normalized_params.get("taskType") or "single"),
            trigger_by=str(normalized_params.get("triggerBy") or "online-order"),
            total_count=max(1, int(normalized_params.get("totalCount") or 1)),
            sku=str(normalized_params.get("sku") or "").strip(),
            skus=normalized_params.get("skus") or [],
            biz_type=str(normalized_params.get("bizType") or "KAISI_ONLINE_ORDER"),
            task_params=normalized_params.get("taskParams"),
        )
    normalized_params["backendTaskNo"] = backend_task_no
    normalized_params["taskId"] = backend_task_no
    normalized_params["taskNo"] = backend_task_no
    return normalized_params


def stop_online_order_runtime(
    task_id: str = "",
    reason: str = "Stop online-order runtime",
) -> Dict[str, Any]:
    normalized_task_id = resolve_runtime_id(task_id)
    runtime = get_runtime(normalized_task_id)
    if runtime is None:
        return {"runtimeId": normalized_task_id, "status": "NOT_FOUND"}
    return runtime.stop(reason=reason)


def get_online_order_runtime_status(task_id: str = "") -> Dict[str, Any]:
    normalized_task_id = resolve_runtime_id(task_id)
    runtime = get_runtime(normalized_task_id)
    if runtime is None:
        return {"runtimeId": normalized_task_id, "status": "NOT_FOUND"}
    return runtime.status()


def enqueue_online_order_price_fill(quotations: List[Dict[str, Any]], task_id: str = "") -> Dict[str, Any]:
    runtime = get_active_runtime(task_id)
    if runtime is None:
        return run_price_fill_once(quotations, task_id=task_id)
    return runtime.enqueue_price_fill(quotations)


def enqueue_online_order_submit(quotations: List[Dict[str, Any]], task_id: str = "") -> Dict[str, Any]:
    runtime = get_active_runtime(task_id)
    if runtime is None:
        return run_submit_once(quotations, task_id=task_id)
    return runtime.enqueue_submit(quotations)
