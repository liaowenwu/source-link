"""在线接单运行时主引擎。"""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from redis import Redis
from redis.exceptions import RedisError

from config import (
    ONLINE_ORDER_MAX_ACCEPT_PER_ROUND,
    ONLINE_ORDER_POLL_INTERVAL_SECONDS,
    ONLINE_ORDER_QUEUE1_WORKERS,
    ONLINE_ORDER_QUEUE2_WORKERS,
    ONLINE_ORDER_QUEUE3_WORKERS,
)
from core.browser import Browser
from core.task_queue import request_task_terminate, update_task
from platforms.benben.auth import BenbenAuthManager
from platforms.benben.crawler import BenbenCrawler
from platforms.kaisi.auth import KaisiAuthManager
from platforms.robot.auth import RobotAuthManager
from platforms.robot.crawler import RobotCrawler
from platforms.kaisi.online_order.auto_fill import (
    AUTO_FILL_SCENE,
    build_report_payloads,
    normalize_benben_config,
    normalize_match_strategy,
    normalize_robot_config,
)
from platforms.kaisi.online_order.crawler import AcceptInquiryTimeoutSkipError, KaisiOnlineOrderCrawler
from service.backend_client import (
    create_backend_task,
    get_backend_kaisi_crawler_config,
    get_backend_kaisi_quality_dicts,
    get_backend_online_order_quotation_items,
)
from service.reporter import (
    clear_task_context,
    report_online_order_quotation,
    register_task_context,
    report_control,
    report_custom_event,
    report_done,
    report_error,
    report_log,
    report_task_start,
)

from .quality_support import build_quality_maps, collect_quality_origin_ids, resolve_item_quality
from .query_param_support import resolve_crawl_platform_plan
from .runtime_payloads import apply_auto_fill_result, build_quotation_payload, build_status_payload, build_submit_payload
from .runtime_store import OnlineOrderRuntimeStore
from .submit_save_tool import save_online_order_quotation
from .runtime_support import (
    EVENT_ONLINE_ORDER_STATUS,
    EVENT_ONLINE_ORDER_SUBMIT,
    NODE_NAME_COMPLETED,
    NODE_NAME_PRICE_FILLING,
    NODE_NAME_QUEUE_PRICE_FILL,
    NODE_NAME_QUEUE_SUBMIT,
    NODE_NAME_RECEIVE_QUOTATION,
    NODE_NAME_SUBMIT_QUOTATION,
    NODE_NAME_WAIT_PRICE_FILL,
    NODE_NAME_WAIT_SUBMIT,
    build_quotation_task_context,
    normalize_seed,
    now_iso,
    build_runtime_task_context,
    quotation_task_no,
    to_bool,
    to_int,
)
from .unclaimed_filter_store import OnlineOrderUnclaimedFilterKeys


@dataclass
class OnlineOrderRuntime:
    # task_id 只是本地运行时别名，不再是业务 taskNo。
    task_id: str
    # params 保存启动参数快照。
    params: Dict[str, Any]
    # redis 由注册表注入，运行时只负责读写。
    redis: Redis
    # stop_event 用来通知所有线程退出。
    stop_event: threading.Event = field(default_factory=threading.Event)
    # threads 用来统计活跃线程数。
    threads: List[threading.Thread] = field(default_factory=list)
    # report_task_id 指向后端 sync_task.task_no，所有日志和事件都发到这里。
    report_task_id: str = ""
    # task_started_reported 用来保证主任务启动事件只上报一次。
    task_started_reported: bool = False
    # task_finished_reported 用来保证主任务结束事件只上报一次。
    task_finished_reported: bool = False
    # lifecycle_thread 负责在停止后收口主任务状态。
    lifecycle_thread: Optional[threading.Thread] = None

    def __post_init__(self) -> None:
        # 统一规范运行时别名和参数。
        self.task_id = str(self.task_id or "").strip()
        self.params = dict(self.params or {})
        self.params["scene"] = "online_order"
        self.params["kaisiScene"] = "online_order"
        self.params["onlineOrderScene"] = "online_order"
        # 解析运行开关和阈值。
        self.manual_price_fill_enabled = to_bool(self.params.get("manualPriceFillEnabled"), default=True)
        self.auto_submit_enabled = to_bool(
            self.params.get("autoSubmit") or self.params.get("autoSubmitEnabled"),
            default=False,
        )
        self.queue1_poll_threshold = max(
            1,
            to_int(self.params.get("queue1PollThreshold"), 5),
        )
        self.poll_interval_seconds = max(
            1,
            to_int(self.params.get("pollIntervalSeconds"), ONLINE_ORDER_POLL_INTERVAL_SECONDS),
        )
        self.max_accept_per_round = max(
            1,
            min(10, to_int(self.params.get("maxAcceptPerRound"), ONLINE_ORDER_MAX_ACCEPT_PER_ROUND)),
        )
        # 奔奔配置启动时从后端读取，这里先初始化为空结构。
        self.benben_config = normalize_benben_config({})
        self.robot_config = normalize_robot_config({})
        self.match_strategy = normalize_match_strategy(self.params.get("pricingMatchStrategy"), self.benben_config)
        self.quality_maps = build_quality_maps([])
        self.report_task_id = str(self.params.get("backendTaskNo") or "").strip()
        self.store = OnlineOrderRuntimeStore(task_id=self.task_id, redis_client=self.redis)

    def start(self) -> Dict[str, Any]:
        # 先写启动中的元数据，让状态接口立即可见。
        self._save_meta({
            "status": "STARTING",
            "manualPriceFillEnabled": json.dumps(self.manual_price_fill_enabled),
            "autoSubmitEnabled": json.dumps(self.auto_submit_enabled),
            "currentNodeCode": "RUNTIME_STARTING",
            "currentNodeName": "运行时启动中",
            "lastMessage": "在线接单运行时启动中",
            "quotationId": "",
            "storeId": "",
            "flowStatus": "",
            "processStatus": "",
            "errorMessage": "",
            "startedAt": now_iso(),
            **self._build_queue_key_meta(),
        })
        update_task(self.task_id, status="starting", error=None)
        try:
            # 在线接单启动后仍然要在后端创建 sync_task 主任务。
            self._ensure_report_task()
        except Exception as exc:
            self._mark_runtime_failed(f"创建后端同步主任务失败：{exc}")
            return self.status()
        try:
            # 主任务创建成功后，马上向后端写入启动事件和主线程日志。
            self._report_runtime_start()
        except Exception as exc:
            self._mark_runtime_failed(f"上报在线接单主任务启动事件失败：{exc}")
            return self.status()
        try:
            # 后端主任务创建完成后，再去拉奔奔配置，确保日志统一归到 sync_task。
            self._load_backend_benben_config()
        except Exception as exc:
            self._mark_runtime_failed(f"加载后端爬虫配置失败：{exc}")
            return self.status()
        try:
            # 正式启动工作线程前，先检查开思和犇犇是否已登录。
            self._prepare_platform_sessions()
        except Exception as exc:
            self._mark_runtime_failed(f"平台登录检查失败：{exc}")
            return self.status()
        # 配置准备完成后启动后台线程。
        self._save_meta({
            "status": "RUNNING",
            "currentNodeCode": "RUNTIME_READY",
            "currentNodeName": "运行时已启动",
            "lastMessage": "在线接单运行时已启动，平台登录校验通过",
            "error": "",
            "errorMessage": "",
            "backendTaskNo": self.report_task_id,
            **self._build_queue_key_meta(),
        })
        update_task(self.task_id, status="running", error=None)
        self._spawn("online-order-poller", self._poller_loop)
        for index in range(ONLINE_ORDER_QUEUE1_WORKERS):
            self._spawn(f"online-order-queue1-{index + 1}", self._queue1_loop)
        for index in range(ONLINE_ORDER_QUEUE2_WORKERS):
            self._spawn(f"online-order-queue2-{index + 1}", self._queue2_loop)
        for index in range(ONLINE_ORDER_QUEUE3_WORKERS):
            self._spawn(f"online-order-queue3-{index + 1}", self._queue3_loop)
        self._start_lifecycle_monitor()
        return self.status()

    def stop(self, reason: str = "收到停止在线接单指令") -> Dict[str, Any]:
        # 停止时只发停止信号，不强杀浏览器线程。
        self.stop_event.set()
        try:
            self._save_meta({
                "status": "STOPPING",
                "currentNodeCode": "RUNTIME_STOPPING",
                "currentNodeName": "运行时停止中",
                "lastMessage": reason,
                "stopReason": reason,
            })
        except RedisError:
            pass
        update_task(self.task_id, status="terminating", error=reason)
        if self.report_task_id:
            request_task_terminate(self.report_task_id)
            report_control(self._report_task_id(), "TERMINATE", reason)
        return self.status()

    def status(self) -> Dict[str, Any]:
        # 状态接口直接从 Redis 元数据和队列长度组装。
        meta = self.store.load_meta()
        alive_worker_count = sum(1 for thread in self.threads if thread.is_alive())
        status = str(meta.get("status") or "").strip().upper()
        if not status:
            status = "STOPPED" if self.stop_event.is_set() and alive_worker_count == 0 else "RUNNING"
        if status == "STOPPING" and self.stop_event.is_set() and alive_worker_count == 0:
            status = "STOPPED"
            try:
                self._save_meta({"status": "STOPPED"})
            except RedisError:
                pass
            update_task(self.task_id, status="stopped", error=meta.get("stopReason"))
        backend_task_no = str(meta.get("backendTaskNo") or self.report_task_id or "").strip()
        return {
            "runtimeId": self.task_id,
            "backendTaskNo": backend_task_no,
            "taskId": backend_task_no,
            "taskNo": backend_task_no,
            "status": status,
            "manualPriceFillEnabled": to_bool(meta.get("manualPriceFillEnabled"), self.manual_price_fill_enabled),
            "autoSubmitEnabled": to_bool(meta.get("autoSubmitEnabled"), self.auto_submit_enabled),
            "quotationId": str(meta.get("quotationId") or "").strip(),
            "storeId": str(meta.get("storeId") or "").strip(),
            "flowStatus": str(meta.get("flowStatus") or "").strip(),
            "processStatus": str(meta.get("processStatus") or "").strip(),
            "currentNodeCode": str(meta.get("currentNodeCode") or "").strip(),
            "currentNodeName": str(meta.get("currentNodeName") or "").strip(),
            "lastMessage": str(meta.get("lastMessage") or "").strip(),
            "errorMessage": str(meta.get("errorMessage") or meta.get("error") or "").strip(),
            "queue1Size": self.store.queue_size(self.store.keys.queue1_key),
            "queue2Size": self.store.queue_size(self.store.keys.queue2_key),
            "queue3Size": self.store.queue_size(self.store.keys.queue3_key),
            "queue1Key": self.store.keys.queue1_key,
            "queue2Key": self.store.keys.queue2_key,
            "queue3Key": self.store.keys.queue3_key,
            "quotationSetKey": self.store.keys.quotation_set_key,
            "unclaimedFilterKey": OnlineOrderUnclaimedFilterKeys(task_id=self.task_id).filtered_hash_key,
            "workerCount": len(self.threads),
            "aliveWorkerCount": alive_worker_count,
            "startedAt": str(meta.get("startedAt") or "").strip(),
            "updatedAt": str(meta.get("updatedAt") or "").strip(),
            "stopped": self.stop_event.is_set(),
        }

    def enqueue_price_fill(self, quotations: List[Dict[str, Any]]) -> Dict[str, Any]:
        # 人工补价只需要报价单主键和门店主键。
        enqueued = 0
        for row in quotations or []:
            quotation_id = str(row.get("quotationId") or "").strip()
            store_id = str(row.get("storeId") or "").strip()
            if not quotation_id or not store_id:
                continue
            existing_context = self.store.load_context(quotation_id, store_id)
            if not existing_context:
                # Manual re-price may target an already-synced quotation after the original runtime context is gone.
                seed = normalize_seed(row)
                self.store.save_context({
                    **seed,
                    "platform": "kaisi",
                    "scene": "online_order",
                    "manualPriceFillEnabled": self.manual_price_fill_enabled,
                    "autoSubmitEnabled": self.auto_submit_enabled,
                    "quotationId": quotation_id,
                    "storeId": store_id,
                    "items": row.get("items") or [],
                })
            self.store.enqueue_queue2(quotation_id, store_id)
            enqueued += 1
            self._emit_status(
                quotation_id=quotation_id,
                store_id=store_id,
                report_task_id=self._register_quotation_task_context(quotation_id, store_id, row),
                flow_status="WAIT_PRICE_FILL",
                process_status="PROCESSING",
                current_node_code="QUEUE_PRICE_FILL",
                current_node_name=NODE_NAME_QUEUE_PRICE_FILL,
                message="报价单已加入补价队列",
            )
        return {
            "runtimeId": self.task_id,
            "backendTaskNo": self._report_task_id(),
            "taskId": self._report_task_id(),
            "taskNo": self._report_task_id(),
            "status": self.status().get("status"),
            "enqueuedCount": enqueued,
            "queue2Size": self.store.queue_size(self.store.keys.queue2_key),
        }

    def _build_queue_key_meta(self) -> Dict[str, str]:
        # 把运行时涉及到的 Redis key 名统一写入 meta，方便前端和人工排查直接查看。
        return {
            "queue1Key": self.store.keys.queue1_key,
            "queue2Key": self.store.keys.queue2_key,
            "queue3Key": self.store.keys.queue3_key,
            "quotationSetKey": self.store.keys.quotation_set_key,
            "unclaimedFilterKey": OnlineOrderUnclaimedFilterKeys(task_id=self.task_id).filtered_hash_key,
        }

    def enqueue_submit(self, quotations: List[Dict[str, Any]]) -> Dict[str, Any]:
        # 提交队列同样只按报价单维度入队。
        enqueued = 0
        for row in quotations or []:
            quotation_id = str(row.get("quotationId") or "").strip()
            store_id = str(row.get("storeId") or "").strip()
            if not quotation_id or not store_id:
                continue
            self.store.enqueue_queue3(quotation_id, store_id)
            enqueued += 1
            self._emit_status(
                quotation_id=quotation_id,
                store_id=store_id,
                report_task_id=self._register_quotation_task_context(quotation_id, store_id, row),
                flow_status="WAIT_SUBMIT",
                process_status="PROCESSING",
                current_node_code="QUEUE_SUBMIT",
                current_node_name=NODE_NAME_QUEUE_SUBMIT,
                message="报价单已加入提交队列",
            )
        return {
            "runtimeId": self.task_id,
            "backendTaskNo": self._report_task_id(),
            "taskId": self._report_task_id(),
            "taskNo": self._report_task_id(),
            "status": self.status().get("status"),
            "enqueuedCount": enqueued,
            "queue3Size": self.store.queue_size(self.store.keys.queue3_key),
        }

    def _spawn(self, name: str, target) -> None:
        # 后台线程统一用 daemon 方式启动。
        thread = threading.Thread(target=target, daemon=True, name=name)
        thread.start()
        self.threads.append(thread)

    def _start_lifecycle_monitor(self) -> None:
        # 生命周期监控线程不计入工作线程数量，避免影响停止判定。
        if self.lifecycle_thread is not None and self.lifecycle_thread.is_alive():
            return
        self.lifecycle_thread = threading.Thread(
            target=self._lifecycle_monitor_loop,
            daemon=True,
            name="online-order-lifecycle-monitor",
        )
        self.lifecycle_thread.start()

    def _lifecycle_monitor_loop(self) -> None:
        # 循环等待所有工作线程退出，然后补发主任务结束事件。
        while True:
            # 未收到停止信号前不做收口，避免误判运行结束。
            if not self.stop_event.is_set():
                time.sleep(0.5)
                continue
            # 只统计真正的工作线程，不把监控线程自己算进去。
            alive_worker_count = sum(1 for thread in self.threads if thread.is_alive())
            # 还有线程在执行时继续等待，直到工作线程全部退出。
            if alive_worker_count > 0:
                time.sleep(0.5)
                continue
            # 读取最新运行态元数据，用于决定结束状态和结束文案。
            meta = self.store.load_meta()
            # 运行时失败场景已经在失败入口单独上报结束事件，这里直接退出。
            if str(meta.get("status") or "").strip().upper() == "FAILED":
                return
            # 把本地运行态写成已停止，前端状态接口和缓存都能及时看到。
            self._save_meta({"status": "STOPPED"})
            # 同步更新本地任务队列记录，便于状态接口返回 stopped。
            update_task(self.task_id, status="stopped", error=meta.get("stopReason"))
            # 向后端 sync_task 补发主线程结束事件，让主任务从 terminating 落成 terminated。
            self._report_runtime_done(
                success_count=1,
                fail_count=0,
                total_count=1,
                message=str(meta.get("stopReason") or "在线接单已停止"),
            )
            return

    def _poller_loop(self) -> None:
        # 轮询线程负责不断发现新的未接单报价单。
        browser = None
        try:
            browser = Browser(channel="msedge", headless=True, image=False)
            context = KaisiAuthManager().get_context(
                browser,
                # 轮询线程内部复用登录态时不再向 sync_task_log 写上下文日志，主线程日志只记录轮询结果。
                log_fn=lambda *_args, **_kwargs: None,
            )
            crawler = KaisiOnlineOrderCrawler(
                context=context,
                task_id=self._report_task_id(),
                params=self.params,
            )
            while not self.stop_event.is_set():
                # 主线程只有在队列1待处理数量小于等于 5 时才继续查询新的报价单。
                if self.store.queue_size(self.store.keys.queue1_key) > self.queue1_poll_threshold:
                    time.sleep(1)
                    continue
                rows = crawler.poll_unclaimed_quotations() or []
                if not rows:
                    time.sleep(self.poll_interval_seconds)
                    continue
                count = 0
                for row in rows:
                    if self.stop_event.is_set():
                        break
                    seed = normalize_seed(row)
                    quotation_id = str(seed.get("quotationId") or "").strip()
                    store_id = str(seed.get("storeId") or "").strip()
                    if not quotation_id or not store_id:
                        continue
                    if not self.store.add_quotation_once(quotation_id, store_id):
                        continue
                    self.store.enqueue_queue1(seed)
                    count += 1
                    if count >= self.max_accept_per_round:
                        break
                if rows:
                    report_log(
                        self._report_task_id(),
                        f"主线程查询待接单列表完成，本轮发现 {len(rows)} 条，加入同步队列 {count} 条",
                    )
                time.sleep(self.poll_interval_seconds)
        except Exception as exc:
            self._mark_runtime_failed(f"在线接单轮询线程异常：{exc}")
        finally:
            if browser is not None:
                try:
                    browser.stop()
                except Exception:
                    pass

    def _queue1_loop(self) -> None:
        # 详情采集线程负责接单并同步完整报价详情。
        browser = None
        try:
            browser = Browser(channel="msedge", headless=True, image=False)
            context = KaisiAuthManager().get_context(
                browser,
                log_fn=lambda *_args, **_kwargs: None,
            )
            crawler = KaisiOnlineOrderCrawler(
                context=context,
                task_id=self._report_task_id(),
                params=self.params,
            )
            while not self.stop_event.is_set():
                seed = self.store.pop_queue1(timeout=1)
                if not seed:
                    continue
                quotation_id = str(seed.get("quotationId") or "").strip()
                store_id = str(seed.get("storeId") or "").strip()
                if not quotation_id or not store_id:
                    continue
                try:
                    # 先真正执行接单，避免超时场景提前推送处理中状态并落库存档。
                    accepted = crawler.accept_inquiry(seed, skip_on_timeout=True)
                    if not accepted:
                        continue
                    # 接单成功后优先使用接口校验返回的最新报价单标识，避免状态仍然绑定旧种子数据。
                    accepted_quotation_id = str(accepted.get("quotationId") or accepted.get("id") or quotation_id).strip()
                    accepted_store_id = str(accepted.get("storeId") or store_id).strip()
                    # 只有接单成功后才推送“开始抓取详情”状态，保证后端状态与实际执行一致。
                    self._emit_status(
                        quotation_id=accepted_quotation_id,
                        store_id=accepted_store_id,
                        flow_status="WAIT_PRICE_FILL" if self.manual_price_fill_enabled else "PRICE_FILLING",
                        process_status="PROCESSING",
                        current_node_code="RECEIVE_QUOTATION",
                        current_node_name=NODE_NAME_RECEIVE_QUOTATION,
                        message="报价单已接单，开始抓取详情",
                        seed=accepted,
                    )
                    detail = crawler.collect_quotation_records(accepted) or {}
                    quote_records = detail.get("quoteRecords") or []
                    if not quote_records:
                        report_log(
                            self._report_task_id(),
                            f"Skip quotation detail push because quoteRecords is empty: quotationId={accepted_quotation_id}, storeId={accepted_store_id}",
                        )
                        continue
                    payload = build_quotation_payload(
                        manual_price_fill_enabled=self.manual_price_fill_enabled,
                        auto_submit_enabled=self.auto_submit_enabled,
                        quotation=accepted,
                        detail=detail,
                    )
                    payload["quotationId"] = str(payload.get("quotationId") or accepted_quotation_id).strip()
                    payload["storeId"] = str(payload.get("storeId") or accepted_store_id).strip()
                    self.store.save_context(payload)
                    quotation_task_id = self._register_quotation_task_context(
                        payload["quotationId"],
                        payload["storeId"],
                        payload,
                    )
                    report_online_order_quotation(quotation_task_id, payload)
                    if self.manual_price_fill_enabled:
                        self._emit_status(
                            quotation_id=payload["quotationId"],
                            store_id=payload["storeId"],
                            flow_status="WAIT_PRICE_FILL",
                            process_status="PROCESSING",
                            current_node_code="WAIT_PRICE_FILL",
                            current_node_name=NODE_NAME_WAIT_PRICE_FILL,
                            message="报价单详情已同步，等待人工补价",
                            seed=payload,
                        )
                    else:
                        self.store.enqueue_queue2(payload["quotationId"], payload["storeId"])
                        self._emit_status(
                            quotation_id=payload["quotationId"],
                            store_id=payload["storeId"],
                            flow_status="PRICE_FILLING",
                            process_status="PROCESSING",
                            current_node_code="QUEUE_PRICE_FILL",
                            current_node_name=NODE_NAME_QUEUE_PRICE_FILL,
                            message="报价单详情已同步，已加入自动补价队列",
                            seed=payload,
                        )
                except AcceptInquiryTimeoutSkipError:
                    # 接单超时后已由采集器调用 confirmTimeOut，这里直接跳过当前报价单且不落库。
                    continue
                except Exception as exc:
                    self._emit_status(
                        quotation_id=quotation_id,
                        store_id=store_id,
                        flow_status="WAIT_PRICE_FILL",
                        process_status="FAILED",
                        current_node_code="RECEIVE_QUOTATION",
                        current_node_name=NODE_NAME_RECEIVE_QUOTATION,
                        message=f"报价单详情同步失败：{exc}",
                        error_message=str(exc),
                        seed=seed,
                    )
        except Exception as exc:
            self._mark_runtime_failed(f"报价单详情线程异常：{exc}")
        finally:
            if browser is not None:
                try:
                    browser.stop()
                except Exception:
                    pass

    def _queue2_loop(self) -> None:
        # 补价线程负责调用奔奔查询并自动回写推荐价格。
        browser = None
        try:
            browser = Browser(channel="msedge", headless=True, image=False)
            benben_crawler: Optional[BenbenCrawler] = None
            robot_crawler: Optional[RobotCrawler] = None

            def _ensure_price_fill_crawler(platform_name: str, quotation_task_id: str):
                nonlocal benben_crawler, robot_crawler
                if platform_name == "benben":
                    if benben_crawler is None:
                        context = BenbenAuthManager().get_context(
                            browser,
                            log_fn=lambda *_args, **_kwargs: None,
                        )
                        benben_crawler = BenbenCrawler(
                            context=context,
                            task_id=self._report_task_id(),
                            city=str(self.benben_config.get("defaultCity") or ""),
                            suppliers=self.benben_config.get("supplierNames") or [],
                            supplier_ids=",".join([str(item) for item in self.benben_config.get("supplierOriginIds") or [] if str(item).strip()]),
                            brand_names=",".join([str(item) for item in self.benben_config.get("brandNames") or [] if str(item).strip()]),
                            single_sku_max_crawl_count=int(self.benben_config.get("singleSkuMaxCrawlCount") or 0),
                        )
                    benben_crawler.set_log_task_id(quotation_task_id)
                    return benben_crawler
                if platform_name == "robot":
                    if robot_crawler is None:
                        context = RobotAuthManager().get_context(
                            browser,
                            log_fn=lambda *_args, **_kwargs: None,
                        )
                        robot_crawler = RobotCrawler(
                            context=context,
                            task_id=self._report_task_id(),
                            city=str(self.robot_config.get("defaultCity") or ""),
                            suppliers=self.robot_config.get("supplierNames") or [],
                            quality_origin_ids=",".join([str(item) for item in self.robot_config.get("qualityOriginIds") or [] if str(item).strip()]),
                            supplier_ids=",".join([str(item) for item in self.robot_config.get("supplierOriginIds") or [] if str(item).strip()]),
                            brand_names=",".join([str(item) for item in self.robot_config.get("brandNames") or [] if str(item).strip()]),
                            single_sku_max_crawl_count=int(self.robot_config.get("singleSkuMaxCrawlCount") or 0),
                        )
                    robot_crawler.set_log_task_id(quotation_task_id)
                    return robot_crawler
                return None
            while not self.stop_event.is_set():
                quotation_id, store_id = self.store.pop_quotation_key(self.store.keys.queue2_key, timeout=1)
                if not quotation_id or not store_id:
                    continue
                context_row = self.store.load_context(quotation_id, store_id)
                if not context_row:
                    # Queue2 should be able to reconstruct the latest quotation items from backend even without Redis context.
                    context_row = {
                        "quotationId": quotation_id,
                        "storeId": store_id,
                        "items": [],
                    }
                quotation_task_id = self._register_quotation_task_context(quotation_id, store_id, context_row)
                try:
                    # Reload latest backend crawler strategy/config for each quotation,
                    # so runtime picks up strategy changes without restart.
                    self._load_backend_benben_config()
                    context_row = self._load_runtime_context(context_row, quotation_id, store_id)
                    self._emit_status(
                        quotation_id=quotation_id,
                        store_id=store_id,
                        report_task_id=quotation_task_id,
                        flow_status="PRICE_FILLING",
                        process_status="PROCESSING",
                        current_node_code="PRICE_FILLING",
                        current_node_name=NODE_NAME_PRICE_FILLING,
                        message="开始自动补价",
                        seed=context_row,
                    )
                    items = context_row.get("items") or []
                    target_items = [
                        item
                        for item in items
                        if str(item.get("source") or "").strip().upper() != "AUTO"
                        and not item.get("btPrice")
                        and not item.get("price")
                    ]
                    if not target_items:
                        self._emit_status(
                            quotation_id=quotation_id,
                            store_id=store_id,
                            report_task_id=quotation_task_id,
                            flow_status="WAIT_SUBMIT",
                            process_status="PROCESSING",
                            current_node_code="WAIT_SUBMIT",
                            current_node_name=NODE_NAME_WAIT_SUBMIT,
                            message="没有待补价明细，跳过自动补价",
                            seed=context_row,
                        )
                        if self.auto_submit_enabled:
                            self.store.enqueue_queue3(quotation_id, store_id)
                        continue
                    sku_to_items: Dict[str, List[Dict[str, Any]]] = {}
                    for item in target_items:
                        sku = str(item.get("partsNum") or "").replace(" ", "")
                        if sku:
                            sku_to_items.setdefault(sku, []).append(item)
                    shared_skus = list(sku_to_items.keys())
                    if not shared_skus:
                        raise RuntimeError("没有可用于补价的零件号")
                    # 解析当前运行时的全局平台策略（无 sku 级参数时走全局配置）。
                    global_platform_plan = resolve_crawl_platform_plan({}, self.benben_config)
                    # 拿到全局平台执行顺序。
                    platform_sequence = global_platform_plan.get("platformSequence") or ["benben"]
                    # 拿到命中即停标记（优先策略通常为 true）。
                    stop_on_hit = bool(global_platform_plan.get("stopOnHit"))
                    # 过滤出当前运行时支持的平台（benben/robot）。
                    required_platforms = [item for item in platform_sequence if item in {"benben", "robot"}]
                    # 若过滤后为空，兜底为 benben。
                    if not required_platforms:
                        required_platforms = ["benben"]
                    # 对每个平台做共享查询预热，减少后续 SKU 循环里的重复初始化。
                    for platform_name in required_platforms:
                        crawler = _ensure_price_fill_crawler(platform_name, quotation_task_id)
                        if crawler is None:
                            continue
                        if not crawler.prepare_shared_query(shared_skus):
                            raise RuntimeError(f"初始化{platform_name}共享查询失败")
                    for sku, sku_items in sku_to_items.items():
                        quality_origin_ids = collect_quality_origin_ids(sku_items)
                        if not quality_origin_ids:
                            quality_origin_ids = [
                                str(item).strip()
                                for item in self.benben_config.get("qualityOriginIds") or []
                                if str(item).strip()
                            ]
                        # 当前 SKU 在多平台下聚合后的总记录。
                        sku_records: List[Dict[str, Any]] = []
                        # 按 required_platforms 的顺序依次抓取。
                        for platform_name in required_platforms:
                            crawler = _ensure_price_fill_crawler(platform_name, quotation_task_id)
                            if crawler is None:
                                continue
                            # 执行平台抓取：robot 未配置平台过滤时不传 benben 质量过滤参数。
                            if platform_name == "robot":
                                current_records = crawler.crawl_sku(sku)
                            else:
                                current_records = crawler.crawl_sku(
                                    sku,
                                    quality_origin_ids=",".join(quality_origin_ids),
                                )
                            # 合并当前平台命中记录。
                            sku_records.extend(current_records)
                            report_log(
                                quotation_task_id,
                                f"[price-fill] sku={sku} platform={platform_name} matched={len(current_records)}",
                            )
                            # 若命中即停且当前平台命中，提前结束后续平台抓取。
                            if stop_on_hit and current_records:
                                break
                        report_payloads = build_report_payloads(
                            sku=sku,
                            scene=AUTO_FILL_SCENE,
                            sku_records=sku_records,
                            online_order_item_ids=[],
                            online_order_item_metas=sku_items,
                            match_strategy=self.match_strategy,
                        )
                        for payload in report_payloads:
                            payload.setdefault("quotationId", quotation_id)
                            payload.setdefault("storeId", store_id)
                            apply_auto_fill_result(context_row, payload)
                    context_row["message"] = "自动补价完成"
                    report_online_order_quotation(quotation_task_id, context_row)
                    self.store.save_context(context_row)
                    self._emit_status(
                        quotation_id=quotation_id,
                        store_id=store_id,
                        report_task_id=quotation_task_id,
                        flow_status="WAIT_SUBMIT",
                        process_status="PROCESSING",
                        current_node_code="WAIT_SUBMIT",
                        current_node_name=NODE_NAME_WAIT_SUBMIT,
                        message="自动补价完成",
                        seed=context_row,
                    )
                    if self.auto_submit_enabled:
                        self.store.enqueue_queue3(quotation_id, store_id)
                except Exception as exc:
                    self._emit_status(
                        quotation_id=quotation_id,
                        store_id=store_id,
                        report_task_id=quotation_task_id,
                        flow_status="WAIT_PRICE_FILL",
                        process_status="FAILED",
                        current_node_code="PRICE_FILLING",
                        current_node_name=NODE_NAME_PRICE_FILLING,
                        message=f"自动补价失败：{exc}",
                        error_message=str(exc),
                        seed=context_row,
                    )
        except Exception as exc:
            self._mark_runtime_failed(f"补价线程异常：{exc}")
        finally:
            if browser is not None:
                try:
                    browser.stop()
                except Exception:
                    pass

    def _queue3_loop(self) -> None:
        # 提交前优先读后端最新明细，避免人工改价后 Redis 仍是旧值。
        browser = None
        try:
            browser = Browser(channel="msedge", headless=True, image=False)
            context = KaisiAuthManager().get_context(
                browser,
                log_fn=lambda *_args, **_kwargs: None,
            )
            while not self.stop_event.is_set():
                quotation_id, store_id = self.store.pop_quotation_key(self.store.keys.queue3_key, timeout=1)
                if not quotation_id or not store_id:
                    continue
                context_row = self.store.load_context(quotation_id, store_id)
                if not context_row:
                    continue
                quotation_task_id = self._register_quotation_task_context(quotation_id, store_id, context_row)
                try:
                    submit_context = self._load_submit_context(context_row, quotation_id, store_id)
                    items = submit_context.get("items") or []
                    if not items:
                        raise RuntimeError("没有可提交的报价明细")
                    self._emit_status(
                        quotation_id=quotation_id,
                        store_id=store_id,
                        report_task_id=quotation_task_id,
                        flow_status="WAIT_SUBMIT",
                        process_status="PROCESSING",
                        current_node_code="SUBMIT_QUOTATION",
                        current_node_name=NODE_NAME_SUBMIT_QUOTATION,
                        message="开始提交报价单",
                        seed=submit_context,
                    )
                    submit_result = save_online_order_quotation(
                        context=context,
                        quotation=submit_context,
                        items=items,
                        quotation_source="PC",
                        save_status="DRAFT",
                        back_url="",
                    )
                    process_status = "SUCCESS" if submit_result.get("success") else "FAILED"
                    payload = build_submit_payload(
                        quotation_id=quotation_id,
                        store_id=store_id,
                        process_status=process_status,
                        submit_results=submit_result.get("submitResults") or [],
                        message=str(submit_result.get("message") or ""),
                    )
                    report_custom_event(quotation_task_id, EVENT_ONLINE_ORDER_SUBMIT, payload)
                    if process_status == "SUCCESS":
                        self._emit_status(
                            quotation_id=quotation_id,
                            store_id=store_id,
                            report_task_id=quotation_task_id,
                            flow_status="COMPLETED",
                            process_status="SUCCESS",
                            current_node_code="COMPLETED",
                            current_node_name=NODE_NAME_COMPLETED,
                            message=payload["message"],
                            seed=submit_context,
                        )
                        try:
                            self.store.delete_context(quotation_id, store_id)
                            clear_task_context(quotation_task_id)
                        except RedisError:
                            pass
                    else:
                        self.store.save_context(submit_context)
                        self._emit_status(
                            quotation_id=quotation_id,
                            store_id=store_id,
                            report_task_id=quotation_task_id,
                            flow_status="WAIT_SUBMIT",
                            process_status="FAILED",
                            current_node_code="WAIT_SUBMIT",
                            current_node_name=NODE_NAME_WAIT_SUBMIT,
                            message=payload["message"],
                            error_message=str(submit_result.get("message") or "提交校验未通过"),
                            seed=submit_context,
                        )
                except Exception as exc:
                    self.store.save_context(context_row)
                    self._emit_status(
                        quotation_id=quotation_id,
                        store_id=store_id,
                        report_task_id=quotation_task_id,
                        flow_status="WAIT_SUBMIT",
                        process_status="FAILED",
                        current_node_code="SUBMIT_QUOTATION",
                        current_node_name=NODE_NAME_SUBMIT_QUOTATION,
                        message=f"报价单提交失败：{exc}",
                        error_message=str(exc),
                        seed=context_row,
                    )
        except Exception as exc:
            self._mark_runtime_failed(f"提交线程异常：{exc}")
        finally:
            if browser is not None:
                try:
                    browser.stop()
                except Exception:
                    pass

    def _ensure_report_task(self) -> None:
        # 在线接单运行时优先复用启动入口已经创建好的 sync_task，缺失时再兜底补建。
        if not self.report_task_id:
            self.report_task_id = create_backend_task(
                task_type=str(self.params.get("taskType") or "single"),
                trigger_by=str(self.params.get("triggerBy") or "online-order"),
                total_count=max(1, to_int(self.params.get("totalCount"), 1)),
                biz_type=str(self.params.get("bizType") or "KAISI_ONLINE_ORDER"),
                task_params=self.params,
            )
        # 把后端主任务号写到 Redis 元数据，页面和接口都能看到。
        self._save_meta({"backendTaskNo": self.report_task_id})
        # 后端 sync_task 需要挂上在线接单上下文，后续日志和推送复用。
        register_task_context(
            self.report_task_id,
            {
                **build_runtime_task_context(
                    manual_price_fill_enabled=self.manual_price_fill_enabled,
                    auto_submit_enabled=self.auto_submit_enabled,
                ),
                "taskType": str(self.params.get("taskType") or "single"),
                "triggerBy": str(self.params.get("triggerBy") or "online-order"),
                "totalCount": max(1, to_int(self.params.get("totalCount"), 1)),
                "bizType": str(self.params.get("bizType") or "KAISI_ONLINE_ORDER"),
                "platform": "kaisi",
                "mode": str(self.params.get("mode") or "single"),
                "scene": "online_order",
                "kaisiScene": "online_order",
                "onlineOrderScene": "online_order",
            },
        )
        # 本地 task_queue 也补一份同名记录，便于 should_terminate 及时生效。
        update_task(self.report_task_id, status="running", error=None)

    def _report_runtime_start(self) -> None:
        # 已经上报过启动事件时直接返回，避免重复写入 sync_task_log。
        if self.task_started_reported:
            return
        # 把主任务启动事件写入后端 sync_task 和 sync_task_log。
        report_task_start(
            self._report_task_id(),
            task_type=str(self.params.get("taskType") or "single"),
            trigger_by=str(self.params.get("triggerBy") or "online-order"),
            total_count=max(1, to_int(self.params.get("totalCount"), 1)),
        )
        # 标记启动事件已经发出，后续不再重复发送。
        self.task_started_reported = True

    def _prepare_platform_sessions(self) -> None:
        # 启动前先写入当前节点，前端能实时看到“登录检查中”。
        self._save_meta({
            "currentNodeCode": "RUNTIME_PREPARE_LOGIN",
            "currentNodeName": "平台登录检查中",
            "lastMessage": "正在检查开思和犇犇登录状态",
        })
        # 先检查开思平台，接单入口依赖它提供报价单抓取和接单能力。
        self._ensure_platform_session("开思平台", KaisiAuthManager())
        global_plan = resolve_crawl_platform_plan({}, self.benben_config)
        platform_sequence = global_plan.get("platformSequence") or []
        if "benben" in platform_sequence:
            self._ensure_platform_session("犇犇平台", BenbenAuthManager())
        if "robot" in platform_sequence:
            self._ensure_platform_session("机器人平台", RobotAuthManager())

    def _ensure_platform_session(self, platform_name: str, auth_manager: Any) -> None:
        # 先尝试用本地缓存认证做一次静默校验，避免重复弹登录窗口。
        if self._check_platform_login(auth_manager):
            # 静默校验通过时记录已登录日志，启动流程继续向下执行。
            # report_log(self._report_task_id(), f"{platform_name} 已登录，无需重新登录")
            return
        # 调用原有交互登录能力，允许用户在浏览器中完成扫码或账号登录。
        auth_manager.do_login(log_fn=lambda *_args, **_kwargs: None)
        # 交互登录结束后再次做静默校验，确保认证结果真的已经可用。
        if not self._check_platform_login(auth_manager):
            # 二次校验失败时抛出异常，由启动入口统一标记为 FAILED。
            raise RuntimeError(f"{platform_name} 登录失败，登录校验未通过")

    def _check_platform_login(self, auth_manager: Any) -> bool:
        # 创建一个无头浏览器上下文，只用于快速校验当前认证文件是否有效。
        browser = Browser(channel="msedge", headless=True, image=False)
        try:
            # 取出浏览器上下文，后续把本地 cookies 注入到这里。
            context = browser.context
            # 把平台认证文件加载到当前临时上下文中。
            auth_manager.load_auth(context)
            # 直接调用平台鉴权接口确认当前 cookies 是否仍然有效。
            return bool(auth_manager.check_login_valid(context))
        finally:
            # 校验结束后立即释放临时浏览器，避免占用本地资源。
            browser.stop()

    def _report_task_id(self) -> str:
        # 所有推送、日志、crawler 内部日志都统一走后端 sync_task.task_no。
        return str(self.report_task_id or self.task_id).strip()

    def _quotation_report_task_id(self, quotation_id: str) -> str:
        return quotation_task_no(quotation_id, fallback=self._report_task_id())

    def _register_quotation_task_context(
        self,
        quotation_id: str,
        store_id: str,
        seed: Optional[Dict[str, Any]] = None,
    ) -> str:
        normalized_seed = normalize_seed(seed or {})
        normalized_quotation_id = str(quotation_id or normalized_seed.get("quotationId") or "").strip()
        normalized_store_id = str(store_id or normalized_seed.get("storeId") or "").strip()
        quotation_task_id = self._quotation_report_task_id(normalized_quotation_id)
        register_task_context(
            quotation_task_id,
            build_quotation_task_context(
                quotation_id=normalized_quotation_id,
                store_id=normalized_store_id,
                manual_price_fill_enabled=self.manual_price_fill_enabled,
                auto_submit_enabled=self.auto_submit_enabled,
                backend_task_no=self._report_task_id(),
                runtime_id=self.task_id,
                extra_context={
                    "platform": "kaisi",
                    "inquiryId": str(normalized_seed.get("inquiryId") or "").strip(),
                    "statusId": str(normalized_seed.get("statusId") or "").strip(),
                    "statusIdDesc": str(normalized_seed.get("statusIdDesc") or "").strip(),
                    "displayModelName": str(normalized_seed.get("displayModelName") or "").strip(),
                    "supplierCompanyId": str(normalized_seed.get("supplierCompanyId") or "").strip(),
                },
            ),
        )
        return quotation_task_id

    def _load_backend_benben_config(self) -> None:
        # 奔奔配置直接从后端读取并标准化。
        raw_crawler_config = get_backend_kaisi_crawler_config()
        self.benben_config = normalize_benben_config(raw_crawler_config)
        self.robot_config = normalize_robot_config(raw_crawler_config)
        self.match_strategy = normalize_match_strategy(self.params.get("pricingMatchStrategy"), self.benben_config)
        self.quality_maps = build_quality_maps(get_backend_kaisi_quality_dicts())
        self.params["benbenConfig"] = self.benben_config
        self.params["robotConfig"] = self.robot_config
        self._save_meta({"crawlerConfigLoadedAt": now_iso(), "lastMessage": "后端爬虫配置已加载"})

    def _load_submit_context(self, context_row: Dict[str, Any], quotation_id: str, store_id: str) -> Dict[str, Any]:
        # 提交阶段沿用统一上下文加载逻辑，保证和补价阶段一致。
        return self._load_runtime_context(context_row, quotation_id, store_id)

    def _load_runtime_context(self, context_row: Dict[str, Any], quotation_id: str, store_id: str) -> Dict[str, Any]:
        merged_context = dict(context_row or {})
        merged_context["quotationId"] = quotation_id
        merged_context["storeId"] = store_id
        fallback_items = [self._enrich_quote_item_quality(item) for item in (context_row.get("items") or [])]
        try:
            latest_items = get_backend_online_order_quotation_items(quotation_id, store_id)
        except Exception:
            merged_context["items"] = fallback_items
            merged_context["itemCount"] = len(fallback_items)
            return merged_context
        if not latest_items:
            merged_context["items"] = fallback_items
            merged_context["itemCount"] = len(fallback_items)
            return merged_context
        context_item_map = {
            self._resolve_item_key(item): dict(item)
            for item in (context_row.get("items") or [])
            if self._resolve_item_key(item)
        }
        merged_items: List[Dict[str, Any]] = []
        for latest_item in latest_items:
            item_key = self._resolve_item_key(latest_item)
            merged_item = dict(context_item_map.get(item_key) or {})
            merged_item.update(latest_item)
            merged_item["quotationId"] = str(merged_item.get("quotationId") or quotation_id).strip()
            merged_item["storeId"] = str(merged_item.get("storeId") or store_id).strip()
            merged_items.append(self._enrich_quote_item_quality(merged_item))
        merged_context["items"] = merged_items
        merged_context["itemCount"] = len(merged_items)
        return merged_context

    def _enrich_quote_item_quality(self, item: Dict[str, Any]) -> Dict[str, Any]:
        return resolve_item_quality(item, self.quality_maps)

    def _resolve_item_key(self, item: Dict[str, Any]) -> str:
        item_id = str(item.get("onlineOrderItemId") or item.get("itemId") or item.get("id") or "").strip()
        if item_id:
            return f"id::{item_id}"

        quoted_price_item_id = str(item.get("quotedPriceItemId") or "").strip()
        if quoted_price_item_id:
            return f"quoted::{quoted_price_item_id}"

        user_needs_item_id = str(item.get("userNeedsItemId") or "").strip()
        if user_needs_item_id:
            return f"needs::{user_needs_item_id}"

        # 优先 resolveResultId，没有时回退到去空格后的 partsNum。
        resolve_result_id = str(item.get("resolveResultId") or "").strip()
        parts_num = str(item.get("partsNum") or "").replace(" ", "")
        if resolve_result_id:
            return f"resolve::{resolve_result_id}"
        if parts_num:
            return f"parts::{parts_num}"
        return ""

    def _emit_status(
        self,
        *,
        quotation_id: str,
        store_id: str,
        flow_status: str,
        process_status: str,
        current_node_code: str,
        current_node_name: str,
        message: str,
        seed: Optional[Dict[str, Any]] = None,
        error_message: str = "",
        report_task_id: str = "",
    ) -> None:
        # 状态事件和 Redis 元数据共用同一套字段。
        payload = build_status_payload(
            manual_price_fill_enabled=self.manual_price_fill_enabled,
            auto_submit_enabled=self.auto_submit_enabled,
            quotation_id=quotation_id,
            store_id=store_id,
            flow_status=flow_status,
            process_status=process_status,
            current_node_code=current_node_code,
            current_node_name=current_node_name,
            message=message,
            seed=seed,
            error_message=error_message,
        )
        self._save_meta({
            "status": "STOPPING" if self.stop_event.is_set() else "RUNNING",
            "quotationId": quotation_id,
            "storeId": store_id,
            "flowStatus": flow_status,
            "processStatus": process_status,
            "currentNodeCode": current_node_code,
            "currentNodeName": current_node_name,
            "lastMessage": message,
            "errorMessage": error_message,
        })
        event_task_id = str(report_task_id or "").strip()
        if event_task_id:
            self._register_quotation_task_context(quotation_id, store_id, seed or payload)
        report_custom_event(event_task_id or self._report_task_id(), EVENT_ONLINE_ORDER_STATUS, payload)

    def _save_meta(self, mapping: Dict[str, Any]) -> None:
        # 统一补 updatedAt，减少状态写入重复代码。
        payload = {key: value for key, value in (mapping or {}).items() if value is not None}
        payload.setdefault("updatedAt", now_iso())
        self.store.save_meta(payload)

    def _mark_runtime_failed(self, error_message: str) -> None:
        # 致命异常时停止整个运行时并标记 FAILED。
        self.stop_event.set()
        try:
            self._save_meta({
                "status": "FAILED",
                "currentNodeCode": "RUNTIME_FAILED",
                "currentNodeName": "运行时失败",
                "lastMessage": error_message,
                "error": error_message,
                "errorMessage": error_message,
            })
        except RedisError:
            pass
        update_task(self.task_id, status="failed", error=error_message)
        if self.report_task_id:
            report_log(self._report_task_id(), error_message, level="ERROR")
            report_error(self._report_task_id(), error_message, supplier_name="开思在线接单")
            self._report_runtime_done(
                success_count=0,
                fail_count=1,
                total_count=1,
                message=error_message,
            )
            update_task(self.report_task_id, status="failed", error=error_message)

    def _report_runtime_done(self, success_count: int, fail_count: int, total_count: int, message: str) -> None:
        # 没有后端主任务号时无法上报，直接返回避免抛出二次异常。
        if not self.report_task_id:
            return
        # 结束事件只允许发送一次，防止 monitor 和失败入口重复写日志。
        if self.task_finished_reported:
            return
        # 先标记已发送，确保即使上报过程中出现异常也不会无限重试。
        self.task_finished_reported = True
        # 把运行时结束结果写入后端 sync_task 和 sync_task_log。
        report_done(
            self._report_task_id(),
            success_count=success_count,
            fail_count=fail_count,
            total_count=total_count,
            message=message,
        )
