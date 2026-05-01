from typing import Any, Dict


def execute(task_id: str, params: Dict[str, Any]):
    from platforms.kaisi.executor import execute as _execute

    return _execute(task_id, params)


__all__ = ["execute"]
