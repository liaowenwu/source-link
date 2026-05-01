"""在线接单执行服务。"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple

from core.browser import Browser
from core.task_queue import set_task_paused
from platforms.kaisi.auth import KaisiAuthManager
from platforms.kaisi.common.record_mapper import build_realtime_payload
from platforms.kaisi.common.task_state import should_terminate, wait_if_paused
from platforms.kaisi.online_order.crawler import KaisiOnlineOrderCrawler
from service.reporter import (
    report_control,
    report_done,
    report_error,
    report_item,
    report_log,
    report_online_order_quotation,
    report_progress,
    report_result,
    report_task_start,
)

from .execution_support import (
    PLATFORM_NAME,
    build_payload,
    flush_payloads,
    join_quotation_ids,
    normalize_sync_quotations,
    pause_before_next_round,
    quotation_id,
    sleep_poll,
    to_bool,
    to_int,
    to_str_list,
    waiting_after_accept_message,
)


# 把旧 executor 的状态收拢到服务对象里，便于按职责拆分方法。
class OnlineOrderExecutionService:
    def __init__(self, task_id: str, params: Dict[str, Any]) -> None:
        self.task_id = task_id
        self.params = dict(params or {})
        self.task_type = (self.params.get("taskType") or self.params.get("mode") or "single").strip().lower()
        self.trigger_by = self.params.get("triggerBy") or "online-order"
        self.poll_interval_seconds = max(1, to_int(self.params.get("pollIntervalSeconds") or self.params.get("pollInterval"), 1))
        self.max_accept_per_round = min(5, max(1, to_int(self.params.get("maxAcceptPerRound"), 5)))
        self.enable_benben_price_fill = to_bool(self.params.get("enableBenbenPriceFill"), True)
        self.sync_quoting_only = to_bool(self.params.get("syncQuotingOnly"), False)
        self.sync_nav_tab = str(self.params.get("navTab") or "UNQUOTE").strip().upper() or "UNQUOTE"
        self.sync_status_id = str(self.params.get("statusId") or "UNQUOTE").strip().upper() or "UNQUOTE"
        self.sync_max_quote_pages = max(1, to_int(self.params.get("syncMaxQuotePages"), 200))
        self.sync_inquiry_ids = to_str_list(self.params.get("inquiryIds") or self.params.get("inquiryIdList"))
        self.initial_sync_quotations = normalize_sync_quotations(
            self.params.get("initialSyncQuotations") or self.params.get("syncQuotations")
        )
        self.detail_push_batch_size = min(20, max(1, to_int(self.params.get("detailPushBatchSize"), 5)))
        self.accept_verify_attempts = max(1, to_int(self.params.get("acceptVerifyAttempts"), 5))
        self.accept_verify_interval_seconds = max(1, to_int(self.params.get("acceptVerifyIntervalSeconds"), 1))
        self.success_count = 0
        self.fail_count = 0
        self.processed_count = 0
        self.empty_poll_count = 0
        self.pushed_item_count = 0
        self.uploaded_quotation_count = 0
        self.last_error = ""
        self.start_ts = time.time()
        self.browser: Optional[Browser] = None
        self.crawler: Optional[KaisiOnlineOrderCrawler] = None

    # 执行在线接单流程。
    def execute(self) -> Dict[str, Any]:
        report_task_start(
            self.task_id,
            task_type=self.task_type,
            trigger_by=self.trigger_by,
            total_count=max(len(self.initial_sync_quotations), len(self.sync_inquiry_ids)),
        )
        try:
            self.browser = Browser(channel="msedge", headless=True, image=False)
            context = KaisiAuthManager().get_context(
                self.browser,
                log_fn=lambda msg: report_log(self.task_id, str(msg)),
            )
            self.crawler = KaisiOnlineOrderCrawler(
                context=context,
                task_id=self.task_id,
                params=self.params,
                item_callback=self._on_record,
            )
            if self.initial_sync_quotations and not self.sync_quoting_only:
                self._run_initial_sync()
            if self.sync_quoting_only:
                self._run_sync_only()
            else:
                self._run_online_loop()
        except Exception as exc:
            self.last_error = str(exc)
            report_log(self.task_id, f"在线接单执行异常：{exc}", level="ERROR")
            report_error(self.task_id, str(exc), supplier_name=PLATFORM_NAME)
        finally:
            if self.browser is not None:
                try:
                    self.browser.stop()
                    report_log(self.task_id, "在线接单浏览器已关闭")
                except Exception as exc:
                    report_log(self.task_id, f"在线接单浏览器关闭告警：{exc}", level="WARNING")
        return self._build_result()

    # 更新任务进度。
    def _progress(self, phase: str) -> None:
        report_progress(
            self.task_id,
            self.success_count,
            self.fail_count,
            self.success_count + self.fail_count,
            f"{phase}进度：已处理={self.processed_count}，成功={self.success_count}，失败={self.fail_count}",
        )

    # 实时把采集到的配件明细往前端推送。
    def _on_record(self, record: Dict[str, Any]) -> None:
        payload = build_realtime_payload(
            record=record,
            task_id=self.task_id,
            platform=PLATFORM_NAME,
            message="在线接单实时明细已推送",
        )
        payload["scene"] = "online_order"
        report_item(self.task_id, payload)
        self.pushed_item_count += 1

    # 按 inquiryId 查询并解析最新报价。
    def _resolve_latest(self, quotation: Dict[str, Any]) -> Dict[str, Any]:
        if self.crawler is None:
            raise RuntimeError("采集器尚未初始化")
        inquiry_id = str(quotation.get("inquiryId") or "").strip()
        if not inquiry_id:
            raise RuntimeError("缺少 inquiryId")
        latest = self.crawler.query_quotations_by_inquiry_id(
            inquiry_id,
            max_pages=self.sync_max_quote_pages,
            store_id=str(quotation.get("storeId") or "").strip(),
            prefer_quotation_id=quotation_id(quotation),
        ) or quotation
        if not quotation_id(latest) or not str(latest.get("storeId") or quotation.get("storeId") or "").strip():
            raise RuntimeError(f"inquiryId={inquiry_id} 缺少 quotationId 或 storeId")
        return latest

    # 构造只含主信息的报价 payload。
    def _build_master(self, source: Dict[str, Any], latest: Dict[str, Any], step: str, message: str) -> Dict[str, Any]:
        payload = build_payload(
            self.task_id,
            latest,
            {
                "quotationId": quotation_id(latest) or quotation_id(source),
                "inquiryId": str(latest.get("inquiryId") or source.get("inquiryId") or ""),
                "storeId": str(latest.get("storeId") or source.get("storeId") or ""),
                "statusId": str(latest.get("statusId") or source.get("statusId") or ""),
                "statusIdDesc": str(latest.get("statusIdDesc") or source.get("statusIdDesc") or ""),
                "quoteRecords": [],
            },
            self.enable_benben_price_fill,
        )
        payload["onlineOrderStep"] = step
        payload["items"] = []
        payload["message"] = message
        return payload

    # 采集详情并生成完整详情 payload。
    def _build_detail(self, latest: Dict[str, Any], step: str, prefix: str) -> Tuple[Dict[str, Any], int]:
        if self.crawler is None:
            raise RuntimeError("采集器尚未初始化")
        detail = self.crawler.collect_quotation_records(latest)
        item_count = len(detail.get("quoteRecords") or [])
        payload = build_payload(self.task_id, latest, detail, self.enable_benben_price_fill)
        payload["onlineOrderStep"] = step
        payload["message"] = f"{prefix}：quotationId={detail.get('quotationId') or quotation_id(latest) or '-'}，明细数={item_count}"
        return payload, item_count

    # 把详情缓存批量上传，并更新统一统计。
    def _flush_detail_buffer(self, phase: str, buffer_rows: List[Dict[str, Any]]) -> List[str]:
        if not buffer_rows:
            return []
        waiting_ids: List[str] = []
        try:
            self.uploaded_quotation_count += flush_payloads(self.task_id, [row["payload"] for row in buffer_rows])
            for row in buffer_rows:
                self.processed_count += 1
                self.success_count += 1
                quotation_id_text = str(row.get("quotationId") or "-")
                report_log(
                    self.task_id,
                    f"{phase}详情已同步：quotationId={quotation_id_text}，明细数={int(row.get('itemCount') or 0)}",
                )
                waiting_message = str(row.get("waitingMessage") or "").strip()
                if waiting_message:
                    waiting_ids.append(quotation_id_text)
                    report_log(self.task_id, waiting_message)
                self._progress(phase)
        except Exception as exc:
            self.last_error = str(exc)
            for row in buffer_rows:
                self.processed_count += 1
                self.fail_count += 1
                quotation_id_text = str(row.get("quotationId") or "-")
                report_log(
                    self.task_id,
                    f"{phase}详情推送失败：quotationId={quotation_id_text}，错误={exc}",
                    level="ERROR",
                )
                report_error(self.task_id, str(exc), sku=quotation_id_text, supplier_name=PLATFORM_NAME)
                self._progress(phase)
        finally:
            buffer_rows.clear()
        return waiting_ids

    # 同步指定报价的主信息和详情。
    def _sync_existing(self, quotation: Dict[str, Any], phase: str, step: str, buffer_rows: List[Dict[str, Any]]) -> None:
        quotation_id_text = quotation_id(quotation)
        try:
            latest = self._resolve_latest(quotation)
            report_online_order_quotation(
                self.task_id,
                self._build_master(
                    quotation,
                    latest,
                    step,
                    f"{phase}主信息已同步：quotationId={quotation_id(latest) or quotation_id_text or '-'}",
                ),
            )
            self.uploaded_quotation_count += 1
            detail_payload, item_count = self._build_detail(latest, step, f"{phase}详情已准备")
            buffer_rows.append(
                {
                    "payload": detail_payload,
                    "quotationId": quotation_id(latest) or quotation_id_text or "-",
                    "itemCount": item_count,
                }
            )
            if len(buffer_rows) >= self.detail_push_batch_size:
                self._flush_detail_buffer(phase, buffer_rows)
        except Exception as exc:
            self.processed_count += 1
            self.fail_count += 1
            self.last_error = str(exc)
            report_log(self.task_id, f"{phase}失败：quotationId={quotation_id_text or '-'}，错误={exc}", level="ERROR")
            report_error(self.task_id, str(exc), sku=quotation_id_text, supplier_name=PLATFORM_NAME)
            self._progress(phase)

    # 执行前端传入的初始同步阶段。
    def _run_initial_sync(self) -> None:
        report_log(self.task_id, f"初始同步开始：报价单数量={len(self.initial_sync_quotations)}")
        initial_buffer: List[Dict[str, Any]] = []
        for quotation in self.initial_sync_quotations:
            wait_if_paused(self.task_id)
            if should_terminate(self.task_id):
                break
            self._sync_existing(quotation, "初始同步", "FETCH_QUOTATIONS", initial_buffer)
        self._flush_detail_buffer("初始同步", initial_buffer)

    # 执行纯同步报价模式。
    def _run_sync_only(self) -> None:
        sync_sources = list(self.initial_sync_quotations)
        if not sync_sources:
            seen = set()
            for inquiry in self.sync_inquiry_ids:
                inquiry = str(inquiry or "").strip()
                if inquiry and inquiry not in seen:
                    seen.add(inquiry)
                    sync_sources.append({"inquiryId": inquiry})
        report_log(
            self.task_id,
            f"同步模式开始：显式来源数量={len(sync_sources)}，导航页签={self.sync_nav_tab}，状态编码={self.sync_status_id}",
        )
        sync_buffer: List[Dict[str, Any]] = []
        for quotation in sync_sources:
            wait_if_paused(self.task_id)
            if should_terminate(self.task_id):
                break
            self._sync_existing(quotation, "报价同步", "FETCH_QUOTATIONS", sync_buffer)
        self._flush_detail_buffer("报价同步", sync_buffer)

    # 执行持续轮询接单模式。
    def _run_online_loop(self) -> None:
        if self.crawler is None:
            raise RuntimeError("采集器尚未初始化")
        while not should_terminate(self.task_id):
            wait_if_paused(self.task_id)
            if should_terminate(self.task_id):
                break
            quotations = self.crawler.poll_unclaimed_quotations()
            if not quotations:
                self.empty_poll_count += 1
                if self.empty_poll_count == 1 or self.empty_poll_count % 10 == 0:
                    report_log(self.task_id, f"未发现待接单报价单，空轮询次数={self.empty_poll_count}")
                sleep_poll(self.task_id, self.poll_interval_seconds)
                continue

            self.empty_poll_count = 0
            batch_quotations = quotations[: self.max_accept_per_round]
            report_log(self.task_id, f"本轮拉取报价单数量={len(quotations)}，实际处理数量={len(batch_quotations)}")
            report_log(self.task_id, f"本轮报价单号={join_quotation_ids(batch_quotations)}")

            accepted_rows: List[Dict[str, Any]] = []
            for quotation in batch_quotations:
                wait_if_paused(self.task_id)
                if should_terminate(self.task_id):
                    break
                quotation_id_text = quotation_id(quotation)
                try:
                    accepted = self.crawler.accept_inquiry(
                        quotation,
                        verify_attempts=self.accept_verify_attempts,
                        verify_interval_seconds=self.accept_verify_interval_seconds,
                    )
                    if not accepted:
                        self.processed_count += 1
                        self.fail_count += 1
                        self.last_error = "接单失败"
                        report_log(self.task_id, f"接单失败：quotationId={quotation_id_text or '-'}", level="WARNING")
                        report_error(self.task_id, self.last_error, sku=quotation_id_text, supplier_name=PLATFORM_NAME)
                        self._progress("接单")
                        continue
                    accepted_quotation = accepted if isinstance(accepted, dict) else quotation
                    resolved_quotation_id = quotation_id(accepted_quotation) or quotation_id_text
                    report_online_order_quotation(
                        self.task_id,
                        self._build_master(
                            quotation,
                            accepted_quotation,
                            "RECEIVE_QUOTATION",
                            f"报价单已接单，详情同步已入队：quotationId={resolved_quotation_id or '-'}",
                        ),
                    )
                    self.uploaded_quotation_count += 1
                    accepted_rows.append(
                        {
                            "quotation": accepted_quotation,
                            "quotationId": resolved_quotation_id or "-",
                            "waitingMessage": waiting_after_accept_message(
                                resolved_quotation_id,
                                self.enable_benben_price_fill,
                            ),
                        }
                    )
                except Exception as exc:
                    self.processed_count += 1
                    self.fail_count += 1
                    self.last_error = str(exc)
                    report_log(
                        self.task_id,
                        f"接单或主信息上报失败：quotationId={quotation_id_text or '-'}，错误={exc}",
                        level="ERROR",
                    )
                    report_error(self.task_id, str(exc), sku=quotation_id_text, supplier_name=PLATFORM_NAME)
                    self._progress("接单")

            detail_buffer: List[Dict[str, Any]] = []
            accepted_waiting_ids: List[str] = []
            for row in accepted_rows:
                wait_if_paused(self.task_id)
                if should_terminate(self.task_id):
                    break
                quotation_id_text = str(row.get("quotationId") or "-")
                try:
                    detail_payload, item_count = self._build_detail(
                        row["quotation"],
                        "RECEIVE_QUOTATION_DETAIL",
                        "已接单报价详情已准备",
                    )
                    detail_buffer.append(
                        {
                            "payload": detail_payload,
                            "quotationId": quotation_id_text,
                            "itemCount": item_count,
                            "waitingMessage": row.get("waitingMessage"),
                        }
                    )
                    if len(detail_buffer) >= self.detail_push_batch_size:
                        accepted_waiting_ids.extend(self._flush_detail_buffer("接单详情同步", detail_buffer))
                except Exception as exc:
                    self.processed_count += 1
                    self.fail_count += 1
                    self.last_error = str(exc)
                    report_log(self.task_id, f"详情采集失败：quotationId={quotation_id_text}，错误={exc}", level="ERROR")
                    report_error(self.task_id, str(exc), sku=quotation_id_text, supplier_name=PLATFORM_NAME)
                    self._progress("接单详情同步")
            accepted_waiting_ids.extend(self._flush_detail_buffer("接单详情同步", detail_buffer))

            if should_terminate(self.task_id):
                break
            if accepted_waiting_ids:
                report_log(
                    self.task_id,
                    f"当前轮报价单处理完成：数量={len(accepted_waiting_ids)}，quotationIds={','.join(accepted_waiting_ids)}",
                )
                set_task_paused(self.task_id, True)
                report_control(self.task_id, "PAUSE", "当前轮处理完成，等待下一轮补价和提交")
                pause_before_next_round(self.task_id, accepted_waiting_ids)
                if should_terminate(self.task_id):
                    break
                continue
            sleep_poll(self.task_id, self.poll_interval_seconds)

    # 统一生成任务结果并上报。
    def _build_result(self) -> Dict[str, Any]:
        terminated = should_terminate(self.task_id)
        total_count = self.success_count + self.fail_count
        result_status = "SUCCESS" if self.fail_count == 0 else ("PARTIAL_SUCCESS" if self.success_count > 0 else "FAILED")
        result_item = {
            "sku": "KAISI_ONLINE_ORDER_LOOP" if not self.sync_quoting_only else "KAISI_ONLINE_QUOTING_SYNC",
            "productId": None,
            "productName": "凯思在线接单循环任务" if not self.sync_quoting_only else "凯思在线报价同步任务",
            "supplierName": PLATFORM_NAME,
            "resultStatus": result_status,
            "message": (
                f"同步任务{'已终止' if terminated else '已完成'}：已处理={self.processed_count}，成功={self.success_count}，失败={self.fail_count}"
                if self.sync_quoting_only
                else f"在线接单循环{'已终止' if terminated else '已完成'}：已处理={self.processed_count}，成功={self.success_count}，失败={self.fail_count}"
            ),
            "errorMessage": self.last_error or None,
            "skuRecords": [],
            "raw": {
                "taskType": self.task_type,
                "platform": PLATFORM_NAME,
                "scene": "online_order",
                "syncQuotingOnly": self.sync_quoting_only,
                "navTab": self.sync_nav_tab,
                "statusId": self.sync_status_id,
                "syncInquiryCount": len(self.sync_inquiry_ids),
                "initialSyncQuotationCount": len(self.initial_sync_quotations),
                "detailPushBatchSize": self.detail_push_batch_size,
                "pollIntervalSeconds": self.poll_interval_seconds,
                "maxAcceptPerRound": self.max_accept_per_round,
                "enableBenbenPriceFill": self.enable_benben_price_fill,
                "acceptVerifyAttempts": self.accept_verify_attempts,
                "acceptVerifyIntervalSeconds": self.accept_verify_interval_seconds,
                "terminated": terminated,
                "stats": {
                    "processedQuotationCount": self.processed_count,
                    "uploadedQuotationCount": self.uploaded_quotation_count,
                    "successCount": self.success_count,
                    "failCount": self.fail_count,
                    "emptyPollCount": self.empty_poll_count,
                    "realtimePushedItemCount": self.pushed_item_count,
                },
            },
        }
        report_result(self.task_id, result_item)
        report_done(
            self.task_id,
            success_count=self.success_count,
            fail_count=self.fail_count,
            total_count=total_count,
            message="任务已终止" if terminated else "任务已完成",
        )
        report_log(self.task_id, f"任务结束，耗时秒数={round(time.time() - self.start_ts, 2)}")
        return {
            "taskId": self.task_id,
            "platform": PLATFORM_NAME,
            "taskType": self.task_type,
            "scene": "online_order",
            "syncQuotingOnly": self.sync_quoting_only,
            "successCount": self.success_count,
            "failCount": self.fail_count,
            "totalCount": total_count,
            "processedQuotationCount": self.processed_count,
            "uploadedQuotationCount": self.uploaded_quotation_count,
            "terminated": terminated,
            "items": [result_item],
        }
