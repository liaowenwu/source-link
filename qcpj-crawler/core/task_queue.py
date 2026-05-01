from queue import Queue
from threading import Lock
from typing import Dict, Any

task_queue: Queue = Queue()
tasks: Dict[str, Dict[str, Any]] = {}
_task_lock = Lock()

# 创建任务记录。
def create_task_record(task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    record = {
        "taskId": task_id,
        "status": "queued",
        "result": None,
        "error": None,
        "payload": payload,
        "paused": False,
        "terminateRequested": False,
    }
    with _task_lock:
        tasks[task_id] = record
    return record

# 更新任务。
def update_task(task_id: str, **updates) -> Dict[str, Any]:
    with _task_lock:
        current = tasks.setdefault(task_id, {"taskId": task_id, "status": "queued"})
        current.update(updates)
        return current

# 获取任务。
def get_task(task_id: str) -> Dict[str, Any]:
    with _task_lock:
        return tasks.get(task_id)

# 处理任务。
def enqueue_task(task_id: str, params: Dict[str, Any]) -> None:
    task_queue.put((task_id, params))

# 设置任务paused。
def set_task_paused(task_id: str, paused: bool) -> Dict[str, Any]:
    with _task_lock:
        current = tasks.setdefault(task_id, {"taskId": task_id, "status": "queued"})
        current["paused"] = bool(paused)
        return dict(current)

# 请求任务terminate。
def request_task_terminate(task_id: str) -> Dict[str, Any]:
    with _task_lock:
        current = tasks.setdefault(task_id, {"taskId": task_id, "status": "queued"})
        current["terminateRequested"] = True
        current["paused"] = False
        return dict(current)

# 判断任务paused。
def is_task_paused(task_id: str) -> bool:
    with _task_lock:
        current = tasks.get(task_id) or {}
        return bool(current.get("paused"))

# 判断任务terminaterequested。
def is_task_terminate_requested(task_id: str) -> bool:
    with _task_lock:
        current = tasks.get(task_id) or {}
        return bool(current.get("terminateRequested"))
