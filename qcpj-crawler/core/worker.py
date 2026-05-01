from threading import Thread, Lock

from core.executor import execute_task
from core.task_queue import task_queue, update_task, is_task_terminate_requested
from service.reporter import report_error, report_done, report_log

_worker_started = False
_start_lock = Lock()

# 处理worker的相关逻辑。
def worker():
    while True:
        task_id, params = task_queue.get()

        try:
            update_task(task_id, status="running")
            if is_task_terminate_requested(task_id):
                report_log(task_id, "任务在执行前被终止")
                total_count = int((params or {}).get("totalCount") or 1)
                report_done(task_id, success_count=0, fail_count=total_count, total_count=total_count, message="任务已终止")
                update_task(task_id, status="terminated", result=None, error="terminated before start")
                continue
            result = execute_task(task_id, params)
            update_task(task_id, status="success", result=result, error=None)
        except Exception as e:
            error_message = str(e)
            update_task(task_id, status="failed", error=error_message, result=None)
            # Ensure backend receives failure signal even on unexpected runtime errors.
            try:
                report_error(task_id, error_message)
                total_count = int((params or {}).get("totalCount") or 1)
                report_done(task_id, success_count=0, fail_count=1, total_count=total_count, message="任务异常终止")
            except Exception:
                pass
        finally:
            task_queue.task_done()

# 启动worker。
def start_worker():
    global _worker_started
    with _start_lock:
        if _worker_started:
            return
        Thread(target=worker, daemon=True, name="crawler-task-worker").start()
        _worker_started = True
