# -*- coding: utf-8 -*-
import random
import time
from datetime import datetime
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from core.task_queue import is_task_paused, is_task_terminate_requested
from service.reporter import report_log

LIST_QUOTATION_URL = "https://www.cassmall.com/inquiry/seller/quote/list/v1"
QUOTING_ITEMS_URL_TEMPLATE = "https://www.cassmall.com/inquiryWeb/quotation/{quotation_id}/quoting/items"
RESOLVE_DETAIL_URL = "https://www.cassmall.com/inquiryWeb/quotation/resolveitems/detail"
CURRENT_USER_URL = "https://www.cassmall.com/seller/_current"

# 规范化partsnum。
def normalize_parts_num(value: Any) -> str:
    if value is None:
        return ""
    return "".join(ch for ch in str(value).strip().upper() if ch.isalnum())

# 处理int。
def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default

# 处理float。
def _to_float(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None

# 处理intornone。
def _to_int_or_none(value: Any) -> Optional[int]:
    try:
        if value is None or value == "":
            return None
        return int(float(value))
    except Exception:
        return None

# 处理_chunked的相关逻辑。
def _chunked(values: List[str], size: int) -> Iterable[List[str]]:
    chunk_size = max(1, size)
    for idx in range(0, len(values), chunk_size):
        yield values[idx: idx + chunk_size]

# 解析timestampms。
def _parse_timestamp_ms(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None

    if isinstance(value, (int, float)):
        numeric = int(value)
    else:
        text = str(value).strip()
        if not text:
            return None
        if text.isdigit():
            numeric = int(text)
        else:
            dt = None
            try:
                dt = datetime.fromisoformat(text)
            except Exception:
                pass
            if dt is None:
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                    try:
                        dt = datetime.strptime(text, fmt)
                        break
                    except Exception:
                        continue
            if dt is None:
                return None
            return int(dt.timestamp() * 1000)

    # 兼容秒级时间戳输入
    if abs(numeric) < 100000000000:
        return numeric * 1000
    return numeric

# 规范化场景。
def _normalize_scene(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in {"online", "online-order", "online_order", "接单", "在线接单", "unclaimed"}:
        return "online_order"
    return "history"

# 规范化decimalkey。
def _normalize_decimal_key(value: Any) -> str:
    if value is None or value == "":
        return ""
    return str(value).strip()

# 处理present。
def _first_present(params: Dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key not in params:
            continue
        value = params.get(key)
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return value
    return None


class KaisiCrawler:

    # 处理__init__的相关逻辑。
    def __init__(
        self,
        context,
        task_id: str,
        params: Optional[Dict[str, Any]] = None,
        item_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        self.context = context
        self.task_id = task_id
        self.control_task_id = str(task_id or "").strip()
        self.log_task_id = self.control_task_id
        self.params = params or {}
        self.item_callback = item_callback
        self.retry_count = max(1, _to_int(self.params.get("retryCount"), 5))

        self.quote_page_size = max(1, _to_int(self.params.get("quotePageSize"), 20))
        self.item_page_size = max(1, _to_int(self.params.get("itemPageSize"), 50))
        self.max_quote_pages = max(1, _to_int(self.params.get("maxQuotePages"), 1000))
        self.max_item_pages = max(1, _to_int(self.params.get("maxItemPages"), 1000))
        self.resolve_chunk_size = max(1, _to_int(self.params.get("resolveChunkSize"), 100))

        now_ms = int(time.time() * 1000)
        default_range_ms = 180 * 24 * 60 * 60 * 1000
        self.end_date_ms = _parse_timestamp_ms(self.params.get("endDate")) or now_ms
        self.start_date_ms = _parse_timestamp_ms(self.params.get("startDate")) or (self.end_date_ms - default_range_ms)
        if self.start_date_ms > self.end_date_ms:
            self.start_date_ms, self.end_date_ms = self.end_date_ms, self.start_date_ms

        self.scene = _normalize_scene(
            _first_present(self.params, "scene", "kaisiScene", "kaisiJobType", "bizType")
        )
        default_nav_tab = "UNCLAIMED" if self.scene == "online_order" else "QUOTE"
        default_status_id = "UNQUOTE" if self.scene == "online_order" else "QUOTE"
        self.nav_tab = str(_first_present(self.params, "navTab", "navtab") or default_nav_tab).strip().upper() or default_nav_tab
        self.status_id = str(_first_present(self.params, "statusId", "statusid") or default_status_id).strip().upper() or default_status_id
        if self.scene == "online_order":
            # Enforce online-order fetch rules regardless of inbound params.
            self.nav_tab = "UNCLAIMED"
            self.status_id = "ALL"
            self.max_quote_pages = 1

        self.store_id = str(_first_present(self.params, "storeId", "storeid") or "ALL")
        self.quote_user = str(_first_present(self.params, "quoteUser", "quoteuser") or "")
        self._headers = {
            "Content-Type": "application/json;charset=UTF-8",
        }
        scene_label = (self.scene or "crawler").replace("_", "-")
        report_log(
            self._report_task_id(),
            f"[kaisi-{scene_label}] init scene={self.scene}, navTab={self.nav_tab}, statusId={self.status_id}, storeId={self.store_id}",
        )

    def set_log_task_id(self, task_id: str) -> None:
        normalized_task_id = str(task_id or "").strip()
        self.log_task_id = normalized_task_id or self.control_task_id
        self.task_id = self.log_task_id

    def _report_task_id(self) -> str:
        return str(self.log_task_id or self.control_task_id or self.task_id).strip()

    def _control_task_id(self) -> str:
        return str(self.control_task_id or self.task_id).strip()

    # 发送明细。
    def _emit_item(self, record: Dict[str, Any]) -> None:
        if self.item_callback is None:
            return
        try:
            self.item_callback(record)
        except Exception as exc:
            report_log(self.task_id, f"[开思] 实时回调失败: {exc}", level="WARNING")

    # 判断success响应。
    def _is_success_response(self, body: Dict[str, Any]) -> bool:
        if not isinstance(body, dict):
            return False
        code = body.get("code")
        if code is not None and str(code) not in ("0", "200"):
            return False
        error_code = body.get("errorCode")
        if error_code is not None and str(error_code) not in ("0", "200"):
            return False
        return True

    # 构建请求url。
    def _build_request_url(self, url: str, fresh: bool = False) -> str:
        target = str(url or "").strip()
        if not target or not fresh:
            return target
        separator = "&" if "?" in target else "?"
        return f"{target}{separator}_ts={int(time.time() * 1000)}"

    # 构建请求headers。
    def _build_request_headers(self, extra_headers: Optional[Dict[str, Any]] = None, fresh: bool = False) -> Dict[str, str]:
        headers = dict(self._headers)
        if fresh:
            headers.update({
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            })
        for key, value in (extra_headers or {}).items():
            if key and value is not None:
                headers[str(key)] = str(value)
        return headers

    # 请求json。
    def _request_json(
        self,
        method: str,
        url: str,
        payload: Optional[Dict[str, Any]] = None,
        allow_unexpected: bool = False,
        fresh: bool = False,
        extra_headers: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        last_body: Dict[str, Any] = {}
        for attempt in range(1, self.retry_count + 1):
            _wait_if_paused(self._control_task_id())
            if _should_terminate(self._control_task_id()):
                return {}

            try:
                request_url = self._build_request_url(url, fresh=fresh)
                request_headers = self._build_request_headers(extra_headers=extra_headers, fresh=fresh)
                if method.upper() == "GET":
                    response = self.context.request.get(url=request_url, headers=request_headers, timeout=15000)
                else:
                    if payload is None:
                        response = self.context.request.post(url=request_url, headers=request_headers, timeout=15000)
                    else:
                        response = self.context.request.post(url=request_url, data=payload, headers=request_headers, timeout=15000)
                body = response.json()
                if isinstance(body, dict):
                    last_body = body
                if self._is_success_response(body):
                    return body or {}
                if allow_unexpected:
                    return body or {}
                raise RuntimeError(f"unexpected response payload: {body}")
            except Exception as exc:
                if attempt >= self.retry_count:
                    report_log(self.task_id, f"[开思] 请求失败: {method} {url}，错误: {exc}", level="ERROR")
                    break
                report_log(
                    self.task_id,
                    f"[开思] 请求失败，开始重试 {attempt + 1}/{self.retry_count}: {method} {url}",
                    level="WARNING",
                )
                time.sleep(0.5 + random.random())
        return last_body if allow_unexpected and last_body else {}

    # 加载当前user。
    def _load_current_user(self) -> None:
        body = self._request_json("GET", CURRENT_USER_URL)
        data = (body or {}).get("data") or {}
        if not self.quote_user:
            self.quote_user = str(data.get("userLoginId") or "")
        report_log(
            self.task_id,
            f"[开思] 已加载当前用户，报价用户ID={self.quote_user or '-'}，门店ID={self.store_id}",
        )

    # 查询报价单列表。
    def list_quotations(self, page_num: int) -> Tuple[List[Dict[str, Any]], int]:
        payload = {
            "inquiryType": "ALL",
            "navTab": self.nav_tab,
            "onlyViewOwner": False,
            "storeId": self.store_id,
            "inquiryId": "",
            "statusId": self.status_id,
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
            "pageSize": self.quote_page_size,
            "isHighQualityLargeOrder": "",
        }
        # payload = {"inquiryType":"ALL","navTab":"QUOTE","onlyViewOwner":False,"storeId":"ALL","inquiryId":"","statusId":"QUOTE","garageCompanyId":"","quoteUser":"5cbd21fa43cd690001de1091","quoteType":"ALL","systemQuoteReportStatus":"","quoteScope":"ALL","limitQuoteRange":False,"saasGroupLabels":["ALL"],"startDate":1771924926958,"endDate":1772529726958,"pageNum":1,"pageSize":20,"isHighQualityLargeOrder":""}
        body = self._request_json("POST", LIST_QUOTATION_URL, payload)
        data = (body or {}).get("data") or {}
        rows = data.get("quotationList") or []
        total_elements = _to_int(data.get("totalElements"), 0)
        return rows, total_elements

    # 获取all报价单。
    def fetch_all_quotations(self) -> List[Dict[str, Any]]:
        page_num = 1
        quotations: List[Dict[str, Any]] = []
        total = 0
        while page_num <= self.max_quote_pages:
            _wait_if_paused(self._control_task_id())
            if _should_terminate(self._control_task_id()):
                break

            rows, total = self.list_quotations(page_num)
            if not rows:
                break
            quotations.extend(rows)
            report_log(self.task_id, f"[开思] 报价单第 {page_num} 页抓取完成，记录数={len(rows)}")

            if page_num * self.quote_page_size >= total:
                break
            page_num += 1

        # report_log(self.task_id, f"[开思] 报价单列表抓取完成，总数={len(quotations)}")
        return quotations

    # 查询quoting明细列表。
    def list_quoting_items(self, quotation_id: str, page: int, size: int) -> Tuple[List[Dict[str, Any]], int]:
        url = QUOTING_ITEMS_URL_TEMPLATE.format(quotation_id=quotation_id)
        payload = {
            "isViewPage": True,
            "listHistoryQuoteResult": False,
            "onlyUnquote": False,
            "userNeedsItemPositiveOrder": False,
            "page": page,
            "size": size,
        }
        body = self._request_json("POST", url, payload)
        data = (body or {}).get("data") or {}
        rows = data.get("content") or []
        total = _to_int(data.get("total"), 0)
        return rows, total

    # 获取all报价单明细。
    def fetch_all_quotation_items(self, quotation_id: str) -> List[Dict[str, Any]]:
        page_num = 1
        max_pages = self.max_item_pages
        rows_all: List[Dict[str, Any]] = []
        total = 0

        while page_num <= max_pages:
            _wait_if_paused(self._control_task_id())
            if _should_terminate(self._control_task_id()):
                break

            rows, total = self.list_quoting_items(quotation_id=quotation_id, page=page_num, size=self.item_page_size)
            if not rows:
                break
            rows_all.extend(rows)

            if page_num * self.item_page_size >= total:
                break
            page_num += 1

        return rows_all

    # 获取resolvedetails。
    def fetch_resolve_details(self, inquiry_id: str, store_id: str, resolve_result_ids: List[str]) -> List[Dict[str, Any]]:
        if not resolve_result_ids:
            return []
        payload = {
            "inquiryId": inquiry_id,
            "storeId": store_id,
            "resolveResultIds": resolve_result_ids,
        }
        body = self._request_json("POST", RESOLVE_DETAIL_URL, payload)
        data = (body or {}).get("data") or []
        return data if isinstance(data, list) else []

    # 构建报价记录。
    def _build_quote_record(
        self,
        quote_item: Dict[str, Any],
        quotation_id: str,
        inquiry_id: str,
        store_id: str,
        resolve_result_id: str,
        resolve_status: str,
        status_id_desc: str = "",
        created_stamp: Any = None,
        quotation_created_stamp: Any = None,
    ) -> Dict[str, Any]:
        source = str(quote_item.get("source") or "").strip()
        return {
            "recordType": "QUOTE",
            "quotationId": str(quotation_id or ""),
            "quotationCreatedStamp": _to_int_or_none(quotation_created_stamp),
            "createdStamp": _to_int_or_none(created_stamp),
            "inquiryId": str(quote_item.get("inquiryId") or inquiry_id or ""),
            "storeId": str(quote_item.get("storeId") or store_id or ""),
            "resolveResultId": str(quote_item.get("resolveResultId") or resolve_result_id or ""),
            "resolveStatus": str(resolve_status or ""),
            "statusIdDesc": str(status_id_desc or ""),
            "oldPartsNum": str(quote_item.get("oldPartsNum") or ""),
            "partsNum": str(quote_item.get("partsNum") or ""),
            "partsName": str(quote_item.get("partsName") or ""),
            "brandId": str(quote_item.get("brandId") or ""),
            "brandName": str(quote_item.get("brandName") or ""),
            "source": source,
            "partsBrandQuality": str(quote_item.get("partsBrandQuality") or ""),
            "quantity": _to_int(quote_item.get("quantity"), 0),
            "price": _to_float(quote_item.get("price")),
            "btPrice": _to_float(quote_item.get("btPrice")),
            "arrivalTime": _to_int_or_none(quote_item.get("arrivalTime")),
            "remark": str(quote_item.get("remark") or ""),
            "rawPayload": quote_item,
            "productType": str(quote_item.get("productType") or ""),
            "partType": str(quote_item.get("partType") or ""),
        }

    # 处理记录key。
    def _quote_record_key(self, record: Dict[str, Any]) -> Tuple[str, ...]:
        return (
            str(record.get("recordType") or ""),
            str(record.get("quotationId") or ""),
            str(record.get("inquiryId") or ""),
            str(record.get("storeId") or ""),
            str(record.get("resolveResultId") or ""),
            str(record.get("partsNum") or ""),
            str(record.get("source") or ""),
            str(_to_int_or_none(record.get("quantity")) or 0),
            _normalize_decimal_key(record.get("price")),
            _normalize_decimal_key(record.get("btPrice")),
            str(_to_int_or_none(record.get("createdStamp")) or 0),
        )

    # 构建outofstock记录。
    def _build_out_of_stock_record(
        self,
        detail: Dict[str, Any],
        quotation_id: str,
        inquiry_id: str,
        store_id: str,
        status_id_desc: str = "",
        created_stamp: Any = None,
        quotation_created_stamp: Any = None,
    ) -> Dict[str, Any]:
        return {
            "recordType": "OUT_OF_STOCK",
            "quotationId": str(quotation_id or ""),
            "quotationCreatedStamp": _to_int_or_none(quotation_created_stamp),
            "createdStamp": _to_int_or_none(created_stamp),
            "inquiryId": str(detail.get("inquiryId") or inquiry_id or ""),
            "storeId": str(store_id or ""),
            "resolveResultId": str(detail.get("resolveResultId") or ""),
            "resolveStatus": str(detail.get("statusId") or "OUT_OF_STOCK"),
            "statusIdDesc": str(status_id_desc or ""),
            "partsNum": str(detail.get("partsNum") or ""),
            "partsName": str(detail.get("partsName") or ""),
            "brandId": "",
            "brandName": "",
            "partsBrandQuality": "",
            "quantity": _to_int(detail.get("quantity"), 0),
            "price": None,
            "btPrice": None,
            "productType": "",
            "partType": "",
        }

    # 处理ofstock记录key。
    def _out_of_stock_record_key(self, record: Dict[str, Any]) -> Tuple[str, ...]:
        return (
            str(record.get("recordType") or ""),
            str(record.get("quotationId") or ""),
            str(record.get("inquiryId") or ""),
            str(record.get("storeId") or ""),
            str(record.get("resolveResultId") or ""),
            str(record.get("partsNum") or ""),
            str(_to_int_or_none(record.get("quantity")) or 0),
            str(_to_int_or_none(record.get("createdStamp")) or 0),
        )

    # 注册demandmarker。
    def _register_demand_marker(self, marker_map: Dict[str, Dict[str, Any]], record: Dict[str, Any]) -> None:
        resolve_result_id = str(record.get("resolveResultId") or "")
        parts_num = str(record.get("partsNum") or "")
        inquiry_id = str(record.get("inquiryId") or "")
        store_id = str(record.get("storeId") or "")
        key = resolve_result_id or f"{inquiry_id}:{store_id}:{parts_num}:{len(marker_map)}"

        marker = marker_map.get(key)
        is_out_of_stock = str(record.get("recordType") or "").upper() == "OUT_OF_STOCK"
        quantity = _to_int(record.get("quantity"), 0)
        if marker is None:
            marker_map[key] = {
                "resolveResultId": resolve_result_id,
                "inquiryId": inquiry_id,
                "storeId": store_id,
                "partsNum": parts_num,
                "partsName": str(record.get("partsName") or ""),
                "quantity": quantity,
                "isOutOfStock": is_out_of_stock,
            }
            return

        if not marker.get("partsNum") and parts_num:
            marker["partsNum"] = parts_num
        if not marker.get("partsName") and record.get("partsName"):
            marker["partsName"] = str(record.get("partsName") or "")
        if marker.get("quantity", 0) <= 0 and quantity > 0:
            marker["quantity"] = quantity
        marker["isOutOfStock"] = bool(marker.get("isOutOfStock", False) and is_out_of_stock)

    # 构建demandsummary。
    def _build_demand_summary(self, marker_map: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        summary_by_key: Dict[str, Dict[str, Any]] = {}
        for marker in marker_map.values():
            parts_num = str(marker.get("partsNum") or "")
            normalized = normalize_parts_num(parts_num)
            if not normalized:
                continue

            summary = summary_by_key.get(normalized)
            if summary is None:
                summary = {
                    "partsNum": parts_num,
                    "partsNumKey": normalized,
                    "partsName": str(marker.get("partsName") or ""),
                    "demandTimes": 0,
                    "totalQuantity": 0,
                    "outOfStockTimes": 0,
                    "quotedTimes": 0,
                }
                summary_by_key[normalized] = summary

            summary["demandTimes"] += 1
            summary["totalQuantity"] += _to_int(marker.get("quantity"), 0)
            if marker.get("isOutOfStock"):
                summary["outOfStockTimes"] += 1
            else:
                summary["quotedTimes"] += 1

            if not summary.get("partsName") and marker.get("partsName"):
                summary["partsName"] = str(marker.get("partsName") or "")

        return list(summary_by_key.values())

    # 处理历史。
    def crawl_history(self) -> Dict[str, Any]:
        self._load_current_user()
        quotations = self.fetch_all_quotations()

        quote_records: List[Dict[str, Any]] = []
        out_of_stock_records: List[Dict[str, Any]] = []

        unmatched_resolve_ids: set = set()
        unresolved_scope_map: Dict[Tuple[str, str], set] = {}
        demand_markers: Dict[str, Dict[str, Any]] = {}
        resolve_meta_map: Dict[str, Dict[str, Any]] = {}
        seen_quote_keys: set = set()
        seen_out_of_stock_keys: set = set()

        for idx, quotation in enumerate(quotations, start=1):
            _wait_if_paused(self._control_task_id())
            if _should_terminate(self._control_task_id()):
                break

            quotation_id = str(quotation.get("id") or "")
            inquiry_id = str(quotation.get("inquiryId") or "")
            store_id = str(quotation.get("storeId") or "")
            quotation_status_id_desc = str(quotation.get("statusIdDesc") or "")
            quotation_created_stamp = quotation.get("createdStamp")
            if not quotation_id:
                continue

            if idx % 10 == 1:
                report_log(
                    self.task_id,
                    f"[开思] 正在抓取报价单明细 {idx}/{len(quotations)}，报价单ID={quotation_id}",
                )

            rows = self.fetch_all_quotation_items(quotation_id=quotation_id)
            for row in rows:
                store_resolve_item = row.get("storeResolveItem") or {}
                resolve_result_id = str(store_resolve_item.get("resolveResultId") or "")
                resolve_status = str(store_resolve_item.get("status") or "")
                quote_items = row.get("storeQuoteItemResults") or []

                if quote_items:
                    for quote_item in quote_items:
                        record = self._build_quote_record(
                            quote_item=quote_item,
                            quotation_id=quotation_id,
                            inquiry_id=inquiry_id,
                            store_id=store_id,
                            resolve_result_id=resolve_result_id,
                            resolve_status=resolve_status,
                            status_id_desc=quotation_status_id_desc,
                            created_stamp=quotation_created_stamp,
                            quotation_created_stamp=quotation_created_stamp,
                        )
                        record_key = self._quote_record_key(record)
                        if record_key in seen_quote_keys:
                            continue
                        seen_quote_keys.add(record_key)
                        quote_records.append(record)
                        self._register_demand_marker(demand_markers, record)
                        self._emit_item(record)
                        report_log(self.task_id, f"[开思] 抓取报价记录: {record}")

                # 娌℃湁鍖归厤鍒版姤浠风粨鏋滐紝鎴栨樉寮忔爣璁颁负缂鸿揣锛岀粺涓€鍔犲叆寰呭洖鏌ラ泦鍚?
                if resolve_result_id and (not quote_items or resolve_status.upper() == "OUT_OF_STOCK"):
                    resolve_meta_map.setdefault(resolve_result_id, {
                        "quotationId": quotation_id,
                        "statusIdDesc": quotation_status_id_desc,
                        "createdStamp": _to_int_or_none(quotation_created_stamp),
                        "quotationCreatedStamp": _to_int_or_none(quotation_created_stamp),
                    })
                    unmatched_resolve_ids.add(resolve_result_id)
                    scope_key = (inquiry_id, store_id)
                    unresolved_scope_map.setdefault(scope_key, set()).add(resolve_result_id)

        # 閫氳繃 resolve detail 鎺ュ彛琛ラ綈鏈尮閰嶇殑闆朵欢淇℃伅
        resolved_seen: set = set()
        for (inquiry_id, store_id), resolve_ids in unresolved_scope_map.items():
            clean_ids = [rid for rid in resolve_ids if rid]
            if not inquiry_id or not store_id or not clean_ids:
                continue

            for chunk in _chunked(clean_ids, self.resolve_chunk_size):
                _wait_if_paused(self._control_task_id())
                if _should_terminate(self._control_task_id()):
                    break
                details = self.fetch_resolve_details(inquiry_id=inquiry_id, store_id=store_id, resolve_result_ids=chunk)
                returned_ids = set()
                for detail in details:
                    resolve_result_id = str(detail.get("resolveResultId") or "")
                    if not resolve_result_id:
                        continue
                    returned_ids.add(resolve_result_id)
                    if resolve_result_id in resolved_seen:
                        continue
                    resolved_seen.add(resolve_result_id)
                    resolve_meta = resolve_meta_map.get(resolve_result_id) or {}

                    record = self._build_out_of_stock_record(
                        detail=detail,
                        quotation_id=resolve_meta.get("quotationId") or "",
                        inquiry_id=inquiry_id,
                        store_id=store_id,
                        status_id_desc=resolve_meta.get("statusIdDesc") or "",
                        created_stamp=resolve_meta.get("createdStamp"),
                        quotation_created_stamp=resolve_meta.get("quotationCreatedStamp"),
                    )
                    record_key = self._out_of_stock_record_key(record)
                    if record_key in seen_out_of_stock_keys:
                        continue
                    seen_out_of_stock_keys.add(record_key)
                    out_of_stock_records.append(record)
                    self._register_demand_marker(demand_markers, record)
                    self._emit_item(record)

                # 鎺ュ彛鏈繑鍥炵殑鏁版嵁淇濈暀鍏滃簳璁板綍锛岀‘淇濈己璐ч摼璺彲杩借釜
                missing_ids = set(chunk) - returned_ids
                for rid in missing_ids:
                    if rid in resolved_seen:
                        continue
                    resolved_seen.add(rid)
                    resolve_meta = resolve_meta_map.get(rid) or {}
                    fallback_record = {
                        "recordType": "OUT_OF_STOCK",
                        "quotationId": resolve_meta.get("quotationId") or "",
                        "quotationCreatedStamp": resolve_meta.get("quotationCreatedStamp"),
                        "createdStamp": resolve_meta.get("createdStamp"),
                        "inquiryId": inquiry_id,
                        "storeId": store_id,
                        "resolveResultId": rid,
                        "resolveStatus": "OUT_OF_STOCK",
                        "statusIdDesc": resolve_meta.get("statusIdDesc") or "",
                        "partsNum": "",
                        "partsName": "",
                        "brandId": "",
                        "brandName": "",
                        "partsBrandQuality": "",
                        "quantity": 0,
                        "price": None,
                        "btPrice": None,
                        "productType": "",
                        "partType": "",
                    }
                    fallback_key = self._out_of_stock_record_key(fallback_record)
                    if fallback_key in seen_out_of_stock_keys:
                        continue
                    seen_out_of_stock_keys.add(fallback_key)
                    out_of_stock_records.append(fallback_record)
                    self._emit_item(fallback_record)

        demand_summary = self._build_demand_summary(demand_markers)
        report_log(
            self.task_id,
            (
                f"[开思] 历史抓取完成: 报价单={len(quotations)}, ",
                f"报价记录={len(quote_records)}, 缺货记录={len(out_of_stock_records)}, ",
                f"需求汇总={len(demand_summary)}"
            ),
        )

        return {
            "quotationCount": len(quotations),
            "quoteRecords": quote_records,
            "outOfStockRecords": out_of_stock_records,
            "demandSummary": demand_summary,
            "unmatchedResolveResultIds": sorted(unmatched_resolve_ids),
            "terminated": _should_terminate(self._control_task_id()),
            "startDate": self.start_date_ms,
            "endDate": self.end_date_ms,
            "quoteUser": self.quote_user,
            "storeId": self.store_id,
        }

# 处理ifpaused。
def _wait_if_paused(task_id: str) -> None:
    paused_logged = False
    while is_task_paused(task_id) and not is_task_terminate_requested(task_id):
        if not paused_logged:
            report_log(task_id, "任务已暂停，等待继续执行", level="WARNING")
            paused_logged = True
        time.sleep(1)
    if paused_logged and not is_task_terminate_requested(task_id):
        report_log(task_id, "任务已继续执行")

# 判断terminate。
def _should_terminate(task_id: str) -> bool:
    return is_task_terminate_requested(task_id)










