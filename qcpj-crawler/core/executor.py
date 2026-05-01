from typing import Any, Dict

from config import DEFAULT_PLATFORM
from platforms import normalize_platform_name
from platforms.registry import get_platform_executor

# 执行任务。
def execute_task(task_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
    payload = dict(params or {})
    requested_platform = payload.get("platform") or DEFAULT_PLATFORM
    platform = normalize_platform_name(requested_platform)
    payload["platform"] = platform

    executor = get_platform_executor(platform)
    return executor(task_id, payload)
