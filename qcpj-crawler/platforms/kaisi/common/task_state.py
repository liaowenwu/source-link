import time

from core.task_queue import is_task_paused, is_task_terminate_requested
from service.reporter import report_log

# 处理ifpaused。
def wait_if_paused(task_id: str) -> None:
    paused_logged = False
    while is_task_paused(task_id) and not is_task_terminate_requested(task_id):
        if not paused_logged:
            report_log(task_id, "task paused, waiting to continue", level="WARNING")
            paused_logged = True
        time.sleep(1)
    if paused_logged and not is_task_terminate_requested(task_id):
        report_log(task_id, "task resumed")

# 判断terminate。
def should_terminate(task_id: str) -> bool:
    return is_task_terminate_requested(task_id)
