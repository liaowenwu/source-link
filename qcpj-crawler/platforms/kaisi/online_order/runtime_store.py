"""在线接单运行时的 Redis 存储封装。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Tuple

from redis import Redis

from config import REDIS_DB, REDIS_HOST, REDIS_PASSWORD, REDIS_PORT, REDIS_URL

from .runtime_support import quotation_key, safe_json_loads, split_quotation_key


# 按任务维度维护 Redis key，避免在业务代码里散落字符串拼接。
@dataclass(frozen=True)
class OnlineOrderRuntimeKeys:
    task_id: str

    @property
    def meta_key(self) -> str:
        return f"online-order:runtime:{self.task_id}:meta"

    @property
    def queue1_key(self) -> str:
        return f"online-order:runtime:{self.task_id}:queue:1"

    @property
    def queue2_key(self) -> str:
        return f"online-order:runtime:{self.task_id}:queue:2"

    @property
    def queue3_key(self) -> str:
        return f"online-order:runtime:{self.task_id}:queue:3"

    @property
    def quotation_set_key(self) -> str:
        return f"online-order:runtime:{self.task_id}:quotation-set"

    def quotation_context_key(self, quotation_id: str, store_id: str) -> str:
        return f"online-order:runtime:{self.task_id}:quotation:{quotation_key(quotation_id, store_id)}"


# 根据项目配置创建 Redis 客户端，供运行时和 API 共享。
def create_runtime_redis_client() -> Redis:
    # 优先使用完整 URL，方便一键切换不同环境。
    if REDIS_URL:
        return Redis.from_url(REDIS_URL, decode_responses=True)
    # 否则退回 host/port/db/password 组合配置。
    return Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
        decode_responses=True,
    )


# 把 Redis 的元数据、队列和报价上下文封装成可复用对象。
class OnlineOrderRuntimeStore:
    def __init__(self, task_id: str, redis_client: Redis) -> None:
        # 任务 id 会参与所有 key 拼装，初始化阶段统一规范。
        normalized_task_id = str(task_id or "").strip()
        # 保留底层 Redis 连接，便于执行 hset/rpush/blpop 等操作。
        self.redis = redis_client
        # 集中维护当前任务的 key 集合。
        self.keys = OnlineOrderRuntimeKeys(task_id=normalized_task_id)

    # 写入运行时元数据，供状态接口实时查询。
    def save_meta(self, mapping: Dict[str, Any]) -> None:
        self.redis.hset(self.keys.meta_key, mapping=mapping)

    # 读取运行时元数据，不存在时返回空字典。
    def load_meta(self) -> Dict[str, Any]:
        return self.redis.hgetall(self.keys.meta_key) or {}

    # 读取指定队列长度，供限流和状态面板复用。
    def queue_size(self, queue_key: str) -> int:
        return int(self.redis.llen(queue_key) or 0)

    # 把新接到的报价种子放入详情采集队列。
    def enqueue_queue1(self, seed: Dict[str, Any]) -> None:
        self.redis.rpush(self.keys.queue1_key, json.dumps(seed, ensure_ascii=False))

    # 把报价放入补价队列。
    def enqueue_queue2(self, quotation_id: str, store_id: str) -> None:
        self.redis.rpush(self.keys.queue2_key, quotation_key(quotation_id, store_id))

    # 把报价放入提交队列。
    def enqueue_queue3(self, quotation_id: str, store_id: str) -> None:
        self.redis.rpush(self.keys.queue3_key, quotation_key(quotation_id, store_id))

    # 从详情采集队列取一条任务，没有任务时返回空字典。
    def pop_queue1(self, timeout: int = 1) -> Dict[str, Any]:
        raw = self.redis.blpop(self.keys.queue1_key, timeout=timeout)
        if not raw:
            return {}
        return safe_json_loads(raw[1], {})

    # 从指定的组合键队列中取一条报价标识。
    def pop_quotation_key(self, queue_key: str, timeout: int = 1) -> Tuple[str, str]:
        raw = self.redis.blpop(queue_key, timeout=timeout)
        if not raw:
            return "", ""
        return split_quotation_key(raw[1])

    # 报价首次进入运行时才返回 True，用于去重。
    def add_quotation_once(self, quotation_id: str, store_id: str) -> bool:
        return self.redis.sadd(self.keys.quotation_set_key, quotation_key(quotation_id, store_id)) == 1

    # 把完整报价上下文存入 Redis，供补价和提交阶段继续使用。
    def save_context(self, payload: Dict[str, Any]) -> None:
        # 先从 payload 中解析上下文主键。
        quotation_id = str(payload.get("quotationId") or "").strip()
        store_id = str(payload.get("storeId") or "").strip()
        # 主键不完整时不写入，避免产生脏数据。
        if not quotation_id or not store_id:
            return
        # 上下文按整包 JSON 存储，方便多线程读取。
        self.redis.set(
            self.keys.quotation_context_key(quotation_id, store_id),
            json.dumps(payload, ensure_ascii=False),
        )

    # 读取报价上下文，不存在时返回空字典。
    def load_context(self, quotation_id: str, store_id: str) -> Dict[str, Any]:
        raw = self.redis.get(self.keys.quotation_context_key(quotation_id, store_id))
        return safe_json_loads(raw, {})

    # 删除已经完成的报价上下文，避免 Redis 长期堆积旧数据。
    def delete_context(self, quotation_id: str, store_id: str) -> None:
        self.redis.delete(self.keys.quotation_context_key(quotation_id, store_id))

    def reset_runtime(self) -> None:
        context_pattern = f"online-order:runtime:{self.keys.task_id}:quotation:*"
        context_keys = list(self.redis.scan_iter(match=context_pattern, count=200))
        base_keys = [
            self.keys.meta_key,
            self.keys.queue1_key,
            self.keys.queue2_key,
            self.keys.queue3_key,
            self.keys.quotation_set_key,
        ]
        keys_to_delete = [key for key in [*base_keys, *context_keys] if key]
        if keys_to_delete:
            self.redis.delete(*keys_to_delete)
