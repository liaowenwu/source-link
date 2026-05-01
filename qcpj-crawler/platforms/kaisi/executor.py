from typing import Any, Dict

from service.reporter import report_log

from platforms.kaisi.history.executor import execute as execute_history
from platforms.kaisi.online_order.executor import execute as execute_online_order

SCENE_HISTORY = "history"
SCENE_ONLINE_ORDER = "online_order"

# 规范化场景。
def _normalize_scene(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in {"online", "online-order", "online_order", "接单", "在线接单"}:
        return SCENE_ONLINE_ORDER
    if text in {"history", "historical", "history_quote", "历史", "历史报价"}:
        return SCENE_HISTORY
    return ""

# 解析凯思场景。
def resolve_kaisi_scene(params: Dict[str, Any]) -> str:
    payload = params or {}

    for key in ("kaisiScene", "kaisiJobType", "scene", "bizType"):
        scene = _normalize_scene(payload.get(key))
        if scene:
            return scene

    trigger_by = str(payload.get("triggerBy") or "").strip().lower()
    if trigger_by in {"online-order", "online_order", "onlineorder"}:
        return SCENE_ONLINE_ORDER

    return SCENE_HISTORY

# 执行execute的相关逻辑。
def execute(task_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
    scene = resolve_kaisi_scene(params)
    report_log(task_id, f"[开思] 任务场景分发: {scene}")

    if scene == SCENE_ONLINE_ORDER:
        return execute_online_order(task_id, params)
    return execute_history(task_id, params)
