"""在线接单未接单列表过滤缓存。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, Optional, Set

from redis import Redis
from redis.exceptions import RedisError

from .runtime_store import create_runtime_redis_client
from .runtime_support import quotation_key


@dataclass(frozen=True)
class OnlineOrderUnclaimedFilterKeys:
    """按任务维度维护未接单过滤缓存的 Redis key。"""

    task_id: str

    @property
    def filtered_hash_key(self) -> str:
        """保存被过滤报价单原始数据的 hash key。"""
        return f"online-order:runtime:{self.task_id}:unclaimed-filter"


class OnlineOrderUnclaimedFilterStore:
    """封装未接单列表过滤缓存的读写逻辑。"""

    def __init__(
        self,
        task_id: str,
        redis_client: Optional[Redis] = None,
        log_fn: Optional[Callable[[str], None]] = None,
    ) -> None:
        # 任务号统一转成字符串，避免 Redis key 出现空白或 None。
        normalized_task_id = str(task_id or "").strip()
        # 优先复用外部传入的 Redis 连接，没有时再按项目配置创建。
        self.redis = redis_client or create_runtime_redis_client()
        # 过滤缓存的 key 统一集中管理，避免业务代码里散落字符串拼接。
        self.keys = OnlineOrderUnclaimedFilterKeys(task_id=normalized_task_id)
        # 日志函数由调用方注入，缓存组件本身不直接依赖 reporter。
        self.log_fn = log_fn

    def remember_rows(self, rows: Iterable[Dict[str, Any]]) -> int:
        """把本轮被过滤的报价单原始数据写入 Redis。"""

        # 先在内存里按报价单唯一键组装 mapping，重复项会自动覆盖为最新数据。
        mapping: Dict[str, str] = {}
        # 逐条处理被过滤的报价单，提取唯一键后再序列化存入 Redis。
        for row in rows or []:
            # 没有报价单主键或门店标识的脏数据不写缓存，避免产生无效 key。
            cache_key = self._row_key(row)
            if not cache_key:
                continue
            # 直接保存原始报价单数据，后续需要排查时可以从 Redis 里回看。
            mapping[cache_key] = json.dumps(dict(row or {}), ensure_ascii=False)

        # 没有可写入的数据时直接返回，避免无意义的 Redis 调用。
        if not mapping:
            return 0

        try:
            # 使用 hash 按唯一键保存被过滤的报价单原始数据。
            self.redis.hset(self.keys.filtered_hash_key, mapping=mapping)
            # 返回本次实际写入的唯一报价单数量，供上层日志统计使用。
            return len(mapping)
        except RedisError as exc:
            # Redis 不可用时只记录告警，不能影响主轮询流程继续执行。
            self._log(f"写入未接单过滤缓存失败：{exc}")
            return 0

    def load_keys(self) -> Set[str]:
        """读取当前任务下所有已缓存的过滤报价单唯一键。"""

        try:
            # Redis hash 的 field 就是报价单唯一键，取出后转成 set 便于快速判断。
            raw_keys = self.redis.hkeys(self.keys.filtered_hash_key) or []
            # 统一去掉空白字符串，避免脏 key 影响过滤判断。
            return {
                str(item or "").strip()
                for item in raw_keys
                if str(item or "").strip()
            }
        except RedisError as exc:
            # 读取缓存失败时回退为空集合，表示本轮不走 Redis 过滤。
            self._log(f"读取未接单过滤缓存失败：{exc}")
            return set()

    def contains_row(self, row: Dict[str, Any], cached_keys: Optional[Set[str]] = None) -> bool:
        """判断报价单是否已经存在于过滤缓存中。"""

        # 先从报价单原始数据里拼装唯一键，缺少关键字段时直接判定为未命中。
        cache_key = self._row_key(row)
        if not cache_key:
            return False
        # 上层已提前读取缓存键时直接复用，避免循环里重复访问 Redis。
        effective_keys = cached_keys if cached_keys is not None else self.load_keys()
        # 只要唯一键命中缓存，就表示该报价单应在本轮直接过滤掉。
        return cache_key in effective_keys

    def _row_key(self, row: Dict[str, Any]) -> str:
        """从报价单行数据提取 Redis 过滤缓存使用的唯一键。"""

        # 报价单 ID 兼容接口里的 id / quotationId 两种字段名。
        quotation_id = str((row or {}).get("quotationId") or (row or {}).get("id") or "").strip()
        # 门店 ID 是在线接单报价单的必要维度，没有时不能参与缓存判断。
        store_id = str((row or {}).get("storeId") or "").strip()
        # 关键字段缺失时返回空字符串，交给上层忽略这条数据。
        if not quotation_id or not store_id:
            return ""
        # 统一复用在线接单已有的报价单组合键格式。
        return quotation_key(quotation_id, store_id)

    def _log(self, message: str) -> None:
        """按需输出缓存组件内部告警日志。"""

        # 没有注入日志函数时静默返回，避免组件内部再抛异常。
        if not self.log_fn:
            return
        # 日志输出本身也需要兜底，避免告警日志反向影响主流程。
        try:
            self.log_fn(str(message or "").strip())
        except Exception:
            return
