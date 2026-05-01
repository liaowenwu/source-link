"""在线接单执行门面。"""

from __future__ import annotations

from typing import Any, Dict

from .execution_service import OnlineOrderExecutionService


# 执行在线接单任务，实际逻辑委托给服务对象处理。
def execute(task_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
    service = OnlineOrderExecutionService(task_id=task_id, params=params)
    return service.execute()
