from typing import Callable, Dict, List

from platforms import normalize_platform_name
from platforms.benben.executor import execute as execute_benben
from platforms.kaisi.executor import execute as execute_kaisi
from platforms.robot.executor import execute as execute_robot

PlatformExecutor = Callable[[str, dict], dict]

_EXECUTORS: Dict[str, PlatformExecutor] = {
    "benben": execute_benben,
    "kaisi": execute_kaisi,
    "robot": execute_robot,
}

# 获取platformexecutor。
def get_platform_executor(name: str) -> PlatformExecutor:
    platform = normalize_platform_name(name)
    executor = _EXECUTORS.get(platform)
    if executor is None:
        supported = ", ".join(sorted(_EXECUTORS.keys()))
        raise ValueError(f"unsupported platform '{platform}', supported platforms: {supported}")
    return executor

# 查询supportedplatforms列表。
def list_supported_platforms() -> List[str]:
    return sorted(_EXECUTORS.keys())
