from datetime import datetime
import time
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import urlencode

from platforms.kaisi.common.task_state import should_terminate
from platforms.kaisi.history.crawler import KaisiCrawler, LIST_QUOTATION_URL
from service.reporter import report_log

from .unclaimed_filter_store import OnlineOrderUnclaimedFilterStore

RECEIVE_INQUIRY_URL = "https://www.cassmall.com/agentBuy/seller/admin/supplierquotes/receiveinquiry"
CONFIRM_TIMEOUT_URL = "https://www.cassmall.com/agentBuy/seller/admin/confirmTimeOut"
WRITE_CLAIMED_URL_TEMPLATE = "https://www.cassmall.com/inquiryWeb/quote/write/claimed/{quotation_id}/{store_id}/{inquiry_id}"
SKIP_CLAIMED_ERROR_CODES = {"10020108"}
SKIP_CLAIMED_MESSAGE_KEYWORDS = ("来晚一步", "别家下单", "错失")


class AcceptInquiryTimeoutSkipError(TimeoutError):
    """Raised when accept inquiry timed out and current quotation should be skipped."""


class KaisiOnlineOrderCrawler(KaisiCrawler):
    """Crawler for Kaisi online-order workflows."""

    # 处理__init__的相关逻辑。
    def __init__(
        self,
        context,
        task_id: str,
        params: Optional[Dict[str, Any]] = None,
        item_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        normalized_task_id = str(task_id or "").strip()
        merged_params = {
            **(params or {}),
            "scene": "online_order",
            "kaisiScene": "online_order",
            "navTab": "UNCLAIMED",
            "statusId": "UNQUOTE",
            "maxQuotePages": 1,
        }
        super().__init__(
            context=context,
            task_id=normalized_task_id,
            params=merged_params,
            item_callback=item_callback,
        )
        self.unclaimed_filter_store = OnlineOrderUnclaimedFilterStore(
            task_id=normalized_task_id,
            log_fn=lambda message: report_log(normalized_task_id, message, level="WARNING"),
        )

    # 刷新todayrange。
    def _refresh_today_range(self) -> None:
        now = datetime.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        self.start_date_ms = int(start_of_month.timestamp() * 1000)
        self.end_date_ms = int(now.timestamp() * 1000)

    # 处理unclaimed报价单。
    def poll_unclaimed_quotations(self) -> List[Dict[str, Any]]:
        rows = self.poll_quotations(nav_tab="UNCLAIMED", status_id="UNQUOTE", max_pages=1)
        filtered_rows, owner_filtered_count, cache_filtered_count = self._filter_unclaimed_rows(rows)
        skipped_count = owner_filtered_count + cache_filtered_count
        if skipped_count > 0:
            report_log(
                self.task_id,
                (
                    f"查询报价单，本轮共跳过 {skipped_count} 条，"
                    f"其中已有报价人 {owner_filtered_count} 条"
                ),
                level="WARNING",
            )
            return filtered_rows
        return filtered_rows

    # 处理报价单。
    def poll_quotations(self, nav_tab: str, status_id: str, max_pages: int = 1) -> List[Dict[str, Any]]:
        self._refresh_today_range()
        original_nav_tab = self.nav_tab
        original_status_id = self.status_id
        original_max_quote_pages = self.max_quote_pages
        try:
            self.nav_tab = str(nav_tab or original_nav_tab or "UNCLAIMED").strip().upper()
            self.status_id = str(status_id or original_status_id or "ALL").strip().upper()
            self.max_quote_pages = max(1, int(max_pages or 1))
            return self.fetch_all_quotations()
        finally:
            self.nav_tab = original_nav_tab
            self.status_id = original_status_id
            self.max_quote_pages = original_max_quote_pages

    # 查询报价单by询价单标识。
    def query_quotations_by_inquiry_id(
        self,
        inquiry_id: str,
        max_pages: int = 1,
        store_id: str = "",
        force_refresh: bool = False,
        prefer_quotation_id: str = "",
    ) -> Dict[str, Any]:
        inquiry = str(inquiry_id or "").strip()
        if not inquiry:
            return {}

        self._refresh_today_range()
        page_size = max(1, min(int(self.quote_page_size or 20), 50))
        normalized_store_id = str(store_id or self.store_id or "ALL").strip() or "ALL"
        rows: List[Dict[str, Any]] = []
        total_elements = 0

        for page_num in range(1, max(1, int(max_pages or 1)) + 1):
            payload = {
                "inquiryType": "ALL",
                "navTab": "ALL",
                "onlyViewOwner": False,
                "storeId": normalized_store_id,
                "inquiryId": inquiry,
                "statusId": "ALL",
                "garageCompanyId": "",
                "quoteUser": self.quote_user,
                "quoteType": "ALL",
                "systemQuoteReportStatus": "",
                "quoteScope": "ALL",
                "limitQuoteRange": False,
                "saasGroupLabels": ["ALL"],
                "startDate": self.start_date_ms,
                "endDate": self.end_date_ms,
                "pageNum": page_num,
                "pageSize": page_size,
                "isHighQualityLargeOrder": "",
            }
            body = self._request_json("POST", LIST_QUOTATION_URL, payload, fresh=force_refresh)
            data = (body or {}).get("data") or {}
            page_rows = data.get("quotationList") or []
            rows.extend(page_rows)
            try:
                total_elements = int(float(data.get("totalElements") or 0))
            except Exception:
                total_elements = 0
            if not page_rows or page_num * page_size >= total_elements:
                break

        exact_rows = [row for row in rows if str(row.get("inquiryId") or "").strip() == inquiry]
        candidates = exact_rows or rows
        if len(candidates) > 1:
            report_log(
                self.task_id,
                (
                    "query_quotations_by_inquiry_id returned multiple rows, "
                    f"inquiryId={inquiry}, storeId={normalized_store_id}, "
                    f"preferQuotationId={prefer_quotation_id or '-'}, count={len(candidates)}"
                ),
                level="WARNING",
            )
        return self._pick_latest_by_inquiry(candidates, prefer_quotation_id=prefer_quotation_id)

    # 解析报价单标识。
    def _resolve_quotation_id(self, quotation: Dict[str, Any]) -> str:
        return str(quotation.get("id") or quotation.get("quotationId") or "")

    # 处理响应code。
    def _extract_response_code(self, body: Dict[str, Any]) -> str:
        if not isinstance(body, dict):
            return ""
        for key in ("code", "errorCode", "status"):
            value = body.get(key)
            if value is not None and value != "":
                return str(value).strip()
        return ""

    # 处理error消息。
    def _extract_error_message(self, body: Dict[str, Any]) -> str:
        if not isinstance(body, dict):
            return ""
        for key in ("errorMessage", "message", "msg"):
            value = body.get(key)
            if value is not None and value != "":
                return str(value).strip()
        data = body.get("data")
        if isinstance(data, dict):
            for key in ("errorMessage", "message", "msg"):
                value = data.get(key)
                if value is not None and value != "":
                    return str(value).strip()
        return ""

    # 处理状态。
    def _extract_status(self, body: Dict[str, Any]) -> str:
        if not isinstance(body, dict):
            return ""
        data = body.get("data")
        if isinstance(data, dict):
            status = data.get("status")
            if status is not None:
                return str(status).strip().upper()
        status = body.get("status")
        if status is not None:
            return str(status).strip().upper()
        return ""

    # 判断timeout状态。
    def _is_timeout_status(self, status: str) -> bool:
        text = str(status or "").strip().upper()
        if not text:
            return False
        return text in {"TIMEOUT", "RECEIVE_TIMEOUT", "GATEWAY_TIMEOUT"} or "TIMEOUT" in text

    # 判断quoting状态。
    def _is_quoting_status(self, quotation: Dict[str, Any]) -> bool:
        status_id = str(quotation.get("statusId") or "").strip().upper()
        status_desc = str(quotation.get("statusIdDesc") or "").strip()
        current_tab = str(quotation.get("currentTab") or quotation.get("navTab") or "").strip().upper()
        if "待接单" in status_desc or current_tab == "UNCLAIMED":
            return False
        if "报价中" in status_desc:
            return True
        if status_id == "UNQUOTE" and current_tab in {"QUOTE", "QUOTING"}:
            return True
        return False

    # 判断quoted状态。
    def _is_quoted_status(self, quotation: Dict[str, Any]) -> bool:
        status_id = str(quotation.get("statusId") or "").strip().upper()
        status_desc = str(quotation.get("statusIdDesc") or "").strip()
        return status_id == "QUOTE" or ("已报价" in status_desc)

    # 判断acceptready状态。
    def _is_accept_ready_status(self, quotation: Dict[str, Any]) -> bool:
        return self._is_quoting_status(quotation) or self._is_quoted_status(quotation)

    # 处理latestby询价单。
    def _pick_latest_by_inquiry(self, rows: List[Dict[str, Any]], prefer_quotation_id: str = "") -> Dict[str, Any]:
        candidates = [row for row in (rows or []) if isinstance(row, dict)]
        if not candidates:
            return {}

        preferred = str(prefer_quotation_id or "").strip()
        if preferred:
            filtered = [row for row in candidates if self._resolve_quotation_id(row) == preferred]
            if filtered:
                candidates = filtered

        # 处理millis。
        def _to_millis(value: Any) -> int:
            try:
                if value is None or value == "":
                    return 0
                number = int(float(value))
                return number * 1000 if abs(number) < 100000000000 else number
            except Exception:
                return 0

        candidates.sort(
            key=lambda row: (
                _to_millis(row.get("lastUpdatedStamp")),
                _to_millis(row.get("createdStamp")),
                self._resolve_quotation_id(row),
            ),
            reverse=True,
        )
        return candidates[0]

    # 查询latest报价单by询价单。
    def _query_latest_quotation_by_inquiry(
        self,
        inquiry_id: str,
        prefer_quotation_id: str = "",
        max_pages: int = 3,
        store_id: str = "",
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        return self.query_quotations_by_inquiry_id(
            inquiry_id,
            max_pages=max_pages,
            store_id=store_id,
            force_refresh=force_refresh,
            prefer_quotation_id=prefer_quotation_id,
        )

    # 判断skipclaimed响应。
    def _is_skip_claimed_response(self, body: Dict[str, Any]) -> bool:
        code = self._extract_response_code(body)
        if code in SKIP_CLAIMED_ERROR_CODES:
            return True
        message = self._extract_error_message(body)
        return any(keyword in message for keyword in SKIP_CLAIMED_MESSAGE_KEYWORDS)

    # 处理quotingby询价单。
    def _verify_quoting_by_inquiry(
        self,
        inquiry_id: str,
        prefer_quotation_id: str = "",
        max_attempts: int = 5,
        interval_seconds: int = 1,
        store_id: str = "",
        force_refresh_first: bool = False,
    ) -> Dict[str, Any]:
        inquiry = str(inquiry_id or "").strip()
        if not inquiry:
            return {}

        attempts = max(1, int(max_attempts or 1))
        sleep_seconds = max(1, int(interval_seconds or 1))
        for attempt in range(1, attempts + 1):
            if should_terminate(self.task_id):
                return {}
            latest = self._query_latest_quotation_by_inquiry(
                inquiry,
                prefer_quotation_id=prefer_quotation_id,
                max_pages=3,
                store_id=store_id,
                force_refresh=force_refresh_first and attempt == 1,
            )
            if latest and self._is_accept_ready_status(latest):
                report_log(
                    self.task_id,
                    (
                        f"accept verify success: inquiryId={inquiry}, "
                        f"statusId={latest.get('statusId') or '-'}, statusIdDesc={latest.get('statusIdDesc') or '-'}"
                    ),
                )
                return latest

            status_id = str((latest or {}).get("statusId") or "").strip() or "-"
            status_desc = str((latest or {}).get("statusIdDesc") or "").strip() or "-"
            current_tab = str((latest or {}).get("currentTab") or (latest or {}).get("navTab") or "").strip() or "-"
            report_log(
                self.task_id,
                (
                    f"accept verify not ready ({attempt}/{attempts}): inquiryId={inquiry}, "
                    f"statusId={status_id}, statusIdDesc={status_desc}, tab={current_tab}"
                ),
                level="WARNING",
            )
            if attempt < attempts:
                if should_terminate(self.task_id):
                    return {}
                time.sleep(sleep_seconds)
        return {}

    # 处理unclaimedrows。
    def _filter_unclaimed_rows(self, rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int, int]:
        # owner_filtered_rows 保存本轮已经带报价人的报价单，这些数据会写入 Redis 过滤缓存。
        owner_filtered_rows: List[Dict[str, Any]] = []
        # candidates 保存当前看起来仍可处理、但还需要再经过 Redis 缓存过滤的报价单。
        candidates: List[Dict[str, Any]] = []
        for row in rows or []:
            # quoteUserName 有值说明该报价单已经被别人处理，本轮直接过滤。
            quote_user_name = str((row or {}).get("quoteUserName") or "").strip()
            if quote_user_name:
                owner_filtered_rows.append(row)
                continue
            candidates.append(row)

        # 把本轮因已有报价人而被过滤的报价单直接写入 Redis，供后续轮询直接跳过。
        self.unclaimed_filter_store.remember_rows(owner_filtered_rows)
        # 一次性加载当前任务下所有过滤缓存键，避免循环里反复访问 Redis。
        cached_keys = self.unclaimed_filter_store.load_keys()
        if not cached_keys:
            return candidates, len(owner_filtered_rows), 0

        # filtered 保存最终仍需要继续处理的报价单。
        filtered: List[Dict[str, Any]] = []
        # cache_filtered_count 统计本轮因命中 Redis 过滤缓存而被跳过的数量。
        cache_filtered_count = 0
        for row in candidates:
            # 只要报价单唯一键已经存在于 Redis 缓存里，就说明之前已经被过滤过。
            if self.unclaimed_filter_store.contains_row(row, cached_keys=cached_keys):
                cache_filtered_count += 1
                continue
            filtered.append(row)
        return filtered, len(owner_filtered_rows), cache_filtered_count

    def _load_resolve_detail_map(
        self,
        inquiry_id: str,
        store_id: str,
        rows: List[Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        normalized_inquiry_id = str(inquiry_id or "").strip()
        normalized_store_id = str(store_id or "").strip()
        if not normalized_inquiry_id or not normalized_store_id:
            return {}

        resolve_result_ids: List[str] = []
        seen_ids = set()
        for row in rows or []:
            store_resolve_item = row.get("storeResolveItem") or {}
            resolve_result_id = str(store_resolve_item.get("resolveResultId") or "").strip()
            if not resolve_result_id or resolve_result_id in seen_ids:
                continue
            seen_ids.add(resolve_result_id)
            resolve_result_ids.append(resolve_result_id)

        if not resolve_result_ids:
            return {}

        resolve_detail_map: Dict[str, Dict[str, Any]] = {}
        for start in range(0, len(resolve_result_ids), self.resolve_chunk_size):
            if should_terminate(self.task_id):
                break
            chunk = resolve_result_ids[start: start + self.resolve_chunk_size]
            details = self.fetch_resolve_details(
                inquiry_id=normalized_inquiry_id,
                store_id=normalized_store_id,
                resolve_result_ids=chunk,
            )
            for detail in details or []:
                if not isinstance(detail, dict):
                    continue
                resolve_result_id = str(detail.get("resolveResultId") or "").strip()
                if not resolve_result_id:
                    continue
                resolve_detail_map[resolve_result_id] = detail
        return resolve_detail_map

    def _build_corrected_quote_item(
        self,
        quote_item: Dict[str, Any],
        resolve_detail: Optional[Dict[str, Any]],
    ) -> Tuple[Dict[str, Any], bool]:
        corrected_item = dict(quote_item or {})
        detail = resolve_detail if isinstance(resolve_detail, dict) else {}
        detail_parts_num = str(detail.get("partsNum") or "").strip()
        original_parts_num = str(corrected_item.get("partsNum") or "").strip()
        corrected = False

        if detail_parts_num and detail_parts_num != original_parts_num:
            if original_parts_num:
                corrected_item["quotingItemsPartsNum"] = original_parts_num
            corrected_item["partsNum"] = detail_parts_num
            corrected = True

        detail_parts_name = str(detail.get("partsName") or "").strip()
        if detail_parts_name and not str(corrected_item.get("partsName") or "").strip():
            corrected_item["partsName"] = detail_parts_name

        if detail:
            corrected_item["resolveDetail"] = detail
        return corrected_item, corrected

    # 处理timeout。
    def confirm_timeout(self, store_id: str) -> Dict[str, Any]:
        normalized_store_id = str(store_id or "").strip()
        if not normalized_store_id or should_terminate(self.task_id):
            return {}
        url = f"{CONFIRM_TIMEOUT_URL}?{urlencode({'storeId': normalized_store_id})}"
        body = self._request_json("POST", url, payload=None, allow_unexpected=True)
        report_log(
            self.task_id,
            f"confirmTimeOut POST called for storeId={normalized_store_id}, response={body}",
        )
        return body or {}

    # 写入claimed。
    def _write_claimed(self, quotation: Dict[str, Any]) -> bool:
        inquiry_id = str(quotation.get("inquiryId") or "").strip()
        store_id = str(quotation.get("storeId") or "").strip()
        quotation_id = self._resolve_quotation_id(quotation).strip()
        if not inquiry_id or not store_id or not quotation_id:
            report_log(
                self.task_id,
                (
                    "认领回写已跳过，缺少必要参数，"
                    f"quotationId={quotation_id or '-'}，storeId={store_id or '-'}，inquiryId={inquiry_id or '-'}"
                ),
                level="WARNING",
            )
            return False

        url = WRITE_CLAIMED_URL_TEMPLATE.format(
            quotation_id=quotation_id,
            store_id=store_id,
            inquiry_id=inquiry_id,
        )
        body = self._request_json("POST", url, payload=None, allow_unexpected=True)
        status = self._extract_status(body)
        ok = bool(body) and (status in {"SUCCESS", "OK"} or self._is_success_response(body))
        if not ok and self._is_skip_claimed_response(body):
            report_log(
                self.task_id,
                f"认领回写被远端跳过，quotationId={quotation_id}，inquiryId={inquiry_id}，response={body}",
                level="WARNING",
            )
            return False
        if not ok:
            body = self._request_json("POST", url, payload=None, allow_unexpected=True)
            status = self._extract_status(body)
            ok = bool(body) and (status in {"SUCCESS", "OK"} or self._is_success_response(body))
            if not ok and self._is_skip_claimed_response(body):
                report_log(
                    self.task_id,
                    f"认领回写在兜底后仍被远端跳过，quotationId={quotation_id}，inquiryId={inquiry_id}，response={body}",
                    level="WARNING",
                )
                return False

        if ok:
            report_log(self.task_id, f"认领回写成功，quotationId={quotation_id}，inquiryId={inquiry_id}")
            return True

        report_log(
            self.task_id,
            f"认领回写失败，quotationId={quotation_id}，status={status or '-'}，response={body}",
            level="WARNING",
        )
        return False

    # 处理询价单。
    def accept_inquiry(
        self,
        quotation: Dict[str, Any],
        verify_attempts: int = 5,
        verify_interval_seconds: int = 1,
        skip_on_timeout: bool = True,
    ) -> Optional[Dict[str, Any]]:
        inquiry_id = str(quotation.get("inquiryId") or "")
        store_id = str(quotation.get("storeId") or "")
        supplier_company_id = str(quotation.get("supplierCompanyId") or "")
        quotation_id = self._resolve_quotation_id(quotation)

        if not inquiry_id or not store_id or not supplier_company_id:
            report_log(
                self.task_id,
                f"接单已跳过，缺少必要参数，quotationId={quotation_id or '-'}",
                level="WARNING",
            )
            return None

        query = {
            "inquiryId": inquiry_id,
            "storeId": store_id,
            "supplierCompanyId": supplier_company_id,
            "neededClock": "true",
            "acceptPlace": "QUOTE_LIST",
        }
        url = f"{RECEIVE_INQUIRY_URL}?{urlencode(query)}"
        body = self._request_json("GET", url, allow_unexpected=True)
        status = self._extract_status(body)
        receive_ok = bool(body) and (
            status in {"SUCCESS", "OK"} or (self._is_success_response(body) and not self._is_timeout_status(status))
        )
        claimed_ok = False

        if self._is_timeout_status(status):
            report_log(
                self.task_id,
                f"{quotation_id or '-'} 接单接口返回超时状态={status}，校验前先刷新缓存",
                level="WARNING",
            )
            self.confirm_timeout(store_id)
            if skip_on_timeout:
                report_log(
                    self.task_id,
                    (
                        f"接单超时已调用 confirmTimeOut，当前报价单跳过处理，"
                        f"quotationId={quotation_id or '-'}，inquiryId={inquiry_id or '-'}"
                    ),
                    level="WARNING",
                )
                raise AcceptInquiryTimeoutSkipError(
                    f"报价单接单超时，已调用 confirmTimeOut，quotationId={quotation_id or '-'}"
                )
            time.sleep(1)
            refreshed_row = self.query_quotations_by_inquiry_id(
                inquiry_id,
                max_pages=3,
                store_id=store_id,
                force_refresh=True,
                prefer_quotation_id=quotation_id,
            )
            refreshed_rows = [refreshed_row] if refreshed_row else []
            if refreshed_row:
                report_log(
                    self.task_id,
                    f"超时后已刷新报价单列表，inquiryId={inquiry_id}，rows={len(refreshed_rows)}",
                )
        elif receive_ok:
            report_log(
                self.task_id,
                f"接单成功，quotationId={quotation_id or '-'}，inquiryId={inquiry_id}",
            )
            claimed_ok = self._write_claimed(quotation)
        else:
            report_log(
                self.task_id,
                (
                    f"接单接口返回非成功状态，quotationId={quotation_id or '-'}，"
                    f"status={status or '-'}，response={body}"
                ),
                level="WARNING",
            )

        verified = self._verify_quoting_by_inquiry(
            inquiry_id=inquiry_id,
            prefer_quotation_id=quotation_id,
            max_attempts=verify_attempts,
            interval_seconds=verify_interval_seconds,
            store_id=store_id,
            force_refresh_first=self._is_timeout_status(status),
        )
        if verified:
            if not claimed_ok:
                self._write_claimed(verified if isinstance(verified, dict) else quotation)
            return verified
        #
        # report_log(
        #     self.task_id,
        #     f"接单状态校验失败，quotationId={quotation_id or '-'}，inquiryId={inquiry_id or '-'}",
        #     level="WARNING",
        # )
        return None

    # 采集报价详情页里的所有明细行，并实时推送到前端。
    def collect_quotation_records(self, quotation: Dict[str, Any]) -> Dict[str, Any]:
        # 先提取当前报价的基础标识字段。
        quotation_id = self._resolve_quotation_id(quotation)
        inquiry_id = str(quotation.get("inquiryId") or "")
        store_id = str(quotation.get("storeId") or "")
        status_id_desc = str(quotation.get("statusIdDesc") or "")
        quotation_created_stamp = quotation.get("createdStamp")

        # quote_records 保存最终有效明细，out_of_stock_records 先保留兼容结构。
        quote_records: List[Dict[str, Any]] = []
        out_of_stock_records: List[Dict[str, Any]] = []

        # 没有报价 id 无法继续请求详情页，直接返回空结果。
        if not quotation_id:
            return {
                "quotationId": quotation_id,
                "quoteRecords": quote_records,
                "outOfStockRecords": out_of_stock_records,
            }

        # 先把详情页所有行原始数据取回来。
        rows = self.fetch_all_quotation_items(quotation_id=quotation_id)
        resolve_detail_map = self._load_resolve_detail_map(
            inquiry_id=inquiry_id,
            store_id=store_id,
            rows=rows,
        )
        corrected_parts_num_count = 0
        for row in rows:
            # 任务被终止时立即停止后续采集。
            if should_terminate(self.task_id):
                break
            store_resolve_item = row.get("storeResolveItem") or {}
            resolve_result_id = str(store_resolve_item.get("resolveResultId") or "")
            resolve_status = str(store_resolve_item.get("status") or "")
            quote_items = row.get("storeQuoteItemResults") or []
            resolve_detail = resolve_detail_map.get(resolve_result_id) or {}

            for quote_item in quote_items:
                # 双层循环里同样保持终止感知。
                if should_terminate(self.task_id):
                    break
                corrected_quote_item, corrected = self._build_corrected_quote_item(quote_item, resolve_detail)
                if corrected:
                    corrected_parts_num_count += 1
                # 把凯思返回的明细行映射成统一结构。
                record = self._build_quote_record(
                    quote_item=corrected_quote_item,
                    quotation_id=quotation_id,
                    inquiry_id=inquiry_id,
                    store_id=store_id,
                    resolve_result_id=resolve_result_id,
                    resolve_status=resolve_status,
                    status_id_desc=status_id_desc,
                    created_stamp=quotation_created_stamp,
                    quotation_created_stamp=quotation_created_stamp,
                )
                # 同一条配件明细可能重复出现，先基于组合键去重。
                # 在线接单需要同步 storeQuoteItemResults 的全部明细，
                # 这里不再按去重键过滤，避免有效报价行被误删。
                quote_records.append(record)
                # 每采集一条就实时上报，前端可以即时看到细项。
                self._emit_item(record)

        report_log(
            self.task_id,
            (
                f"报价单详情采集完成，报价单ID={quotation_id}，明细数={len(quote_records)}，"
                f"partsNum修正数={corrected_parts_num_count}"
            ),
        )
        return {
            "quotationId": quotation_id,
            "inquiryId": inquiry_id,
            "storeId": store_id,
            "statusId": str(quotation.get("statusId") or ""),
            "statusIdDesc": status_id_desc,
            "createdStamp": quotation_created_stamp,
            "quoteRecords": quote_records,
            "outOfStockRecords": out_of_stock_records,
        }
