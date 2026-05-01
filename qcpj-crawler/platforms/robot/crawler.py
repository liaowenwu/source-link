import math
import time
from typing import Any, Dict, List, Optional, Set

from core.task_queue import is_task_paused, is_task_terminate_requested
from service.reporter import report_log


class RobotCrawler:


    SEARCH_URL = "https://www.jiqirenai.com/proxy/v1/es/search/product/by_oe"
    DEFAULT_PAGE_SIZE = 2000

    def __init__(
        self,
        context,
        task_id: str,
        city: str = "",
        suppliers: Optional[List[str]] = None,
        quality_codes: str = "",
        quality_origin_ids: str = "",
        supplier_ids: str = "",
        brand_names: str = "",
        single_sku_max_crawl_count: int = 0,
    ):
        self.context = context
        self.task_id = str(task_id or "").strip()
        self.control_task_id = self.task_id
        self.log_task_id = self.task_id
        self.city = city or ""
        self.suppliers = suppliers or []
        self.quality_codes = quality_codes or ""
        self.quality_origin_ids = quality_origin_ids or ""
        self.supplier_ids = supplier_ids or ""
        self.brand_names = brand_names or ""
        try:
            self.single_sku_max_crawl_count = max(int(single_sku_max_crawl_count or 0), 0)
        except Exception:
            self.single_sku_max_crawl_count = 0
        self.retry_count = 4
        self.sku_query_context: Dict[str, Dict[str, str]] = {}

    def set_log_task_id(self, task_id: str) -> None:
        normalized_task_id = str(task_id or "").strip()
        self.log_task_id = normalized_task_id or self.control_task_id
        self.task_id = self.log_task_id

    def _control_task_id(self) -> str:
        return str(self.control_task_id or self.task_id).strip()

    def prepare_shared_query(self, skus: List[str]) -> bool:
        cleaned = [normalize_sku(item) for item in (skus or [])]
        cleaned = [item for item in cleaned if item]
        if not cleaned:
            return False
        self.sku_query_context = {sku: {} for sku in dict.fromkeys(cleaned)}
        report_log(self.task_id, f"[robot] 查询上下文准备完成，SKU 数量={len(self.sku_query_context)}")
        return True

    def _search_by_oe(
        self,
        sku: str,
        page_number: int,
        quality_origin_ids: str = "",
        supplier_ids: str = "",
        region_origin_ids: str = "",
    ) -> Dict[str, Any]:
        payload = {
            "keyword": "",
            "make_ids": [],
            "city_codes": self._to_int_list(region_origin_ids or self.city),
            "quality_ids": self._to_int_list(quality_origin_ids or self.quality_origin_ids or self.quality_codes),
            "brand_ids": [],
            "product_company_ids": self._to_int_list(supplier_ids or self.supplier_ids),
            "sort_city_code": str(self.city or "440300"),
            "has_stock": True,
            "has_price": False,
            "use_default_order": True,
            "sort_field": "",
            "sort_order": "",
            "page_size": self._resolve_page_size(page_number),
            "is_current_city": False,
            "oe": sku,
            "is_enquiry": False,
            "is_local_city": None,
            "seller_id": [],
            "insert_history": True,
            "company_id": 9394,
            "not_seller_id": [-1],
            "page_number": max(int(page_number or 1), 1),
        }

        last_error: Optional[Exception] = None
        for attempt in range(1, self.retry_count + 1):
            _wait_if_paused(self._control_task_id())
            if _should_terminate(self._control_task_id()):
                return {"data": [], "total": 0}
            try:
                response = self.context.request.post(
                    url=self.SEARCH_URL,
                    data=payload,
                    headers={"Content-Type": "application/json;charset=UTF-8"},
                    timeout=6000,
                )
                return response.json() or {}
            except Exception as exc:
                last_error = exc
                if attempt < self.retry_count:
                    report_log(
                        self.task_id,
                        f"[robot] 查询失败，开始重试 {attempt + 1}/{self.retry_count}，sku={sku}，页码={page_number}",
                        level="WARNING",
                    )
                    time.sleep(1)
                else:
                    report_log(
                        self.task_id,
                        f"[robot] 查询失败已达最大重试次数，sku={sku}，页码={page_number}，错误={exc}",
                        level="ERROR",
                    )
        raise RuntimeError(last_error or "robot search request failed")

    def _resolve_page_size(self, page_number: int) -> int:
        if self.single_sku_max_crawl_count <= 0:
            return self.DEFAULT_PAGE_SIZE
        if page_number <= 1:
            return max(1, min(self.DEFAULT_PAGE_SIZE, self.single_sku_max_crawl_count))
        return self.DEFAULT_PAGE_SIZE

    def _to_int_list(self, csv_text: str) -> List[int]:
        result: List[int] = []
        for item in str(csv_text or "").split(","):
            text = item.strip()
            if not text:
                continue
            try:
                result.append(int(text))
            except Exception:
                continue
        return result

    def _allowed_supplier_name_set(self) -> Set[str]:
        return {str(item).strip() for item in (self.suppliers or []) if str(item).strip()}

    def _allowed_brand_name_set(self, brand_names: str) -> Set[str]:
        source = brand_names or self.brand_names
        return {item.strip() for item in str(source or "").split(",") if item and item.strip()}

    def _allowed_quality_set(self, quality_origin_ids: str) -> Set[str]:
        source = quality_origin_ids or self.quality_origin_ids
        return {item.strip() for item in str(source or "").split(",") if item and item.strip()}

    def crawl_sku(
        self,
        sku: str,
        quality_origin_ids: str = "",
        supplier_ids: str = "",
        brand_names: str = "",
        region_origin_ids: str = "",
    ) -> List[Dict[str, Any]]:
        normalized_sku = normalize_sku(sku)
        if not normalized_sku:
            return []
        if normalized_sku not in self.sku_query_context:
            report_log(self.task_id, f"[robot] 未找到 SKU 查询上下文，SKU={normalized_sku}", level="WARNING")
            return []

        page_number = 1
        all_records: List[Dict[str, Any]] = []
        supplier_name_set = self._allowed_supplier_name_set()
        brand_name_set = self._allowed_brand_name_set(brand_names)
        quality_set = self._allowed_quality_set(quality_origin_ids)
        max_limit = self.single_sku_max_crawl_count
        max_page = 1

        while page_number <= max_page:
            _wait_if_paused(self._control_task_id())
            if _should_terminate(self._control_task_id()):
                break

            body = self._search_by_oe(
                sku=normalized_sku,
                page_number=page_number,
                quality_origin_ids=quality_origin_ids,
                supplier_ids=supplier_ids,
                region_origin_ids=region_origin_ids,
            )
            rows = body.get("data") or []
            total = max(int(body.get("total") or 0), 0)
            page_size = max(int(self._resolve_page_size(page_number)), 1)
            max_page = max(1, int(math.ceil(total / page_size))) if total > 0 else 1

            for item in rows:
                if not isinstance(item, dict):
                    continue
                supplier_name = first_non_empty(item.get("seller_name"), item.get("sellerName"))
                supplier_id_value = first_non_empty(
                    item.get("seller_id"),
                    item.get("sellerId"),
                    item.get("product_company_id"),
                    item.get("company_id"),
                )
                brand_name = first_non_empty(item.get("custom_brand_name"), item.get("brand_name"), item.get("brandName"))
                quality_name = first_non_empty(item.get("quality_name"), item.get("qualityName"))
                region_name = first_non_empty(item.get("city_name"), item.get("cityName"))
                region_origin_id = first_non_empty(item.get("city_code"), item.get("cityCode"), region_name)
                brand_origin_id = first_non_empty(item.get("brand_id"), item.get("brandId"), brand_name)
                quality_origin_id = first_non_empty(item.get("quality_id"), item.get("qualityId"), quality_name)
                product_name = first_non_empty(item.get("product_name"), item.get("oe_epc_name"), item.get("productName"))

                if supplier_name_set and supplier_name not in supplier_name_set:
                    continue
                if brand_name_set and brand_name not in brand_name_set:
                    continue
                if quality_set and quality_origin_id not in quality_set and quality_name not in quality_set:
                    continue

                record = {
                    "sku": normalized_sku,
                    "crawlPlatform": "ROBOT",
                    "platformCode": "JIQIREN",
                    "productName": product_name,
                    "brand": brand_name,
                    "brandName": brand_name,
                    "brandOriginId": brand_origin_id,
                    "region": region_name,
                    "regionName": region_name,
                    "regionOriginId": region_origin_id,
                    "qualityName": quality_name,
                    "qualityOriginId": quality_origin_id,
                    "companyName": supplier_name,
                    "supplierName": supplier_name,
                    "supplierId": supplier_id_value,
                    "stock": first_non_empty(item.get("quantity"), item.get("stock"), "0"),
                    "price": item.get("price"),
                    "rawPayload": item,
                }
                all_records.append(record)
                if max_limit > 0 and len(all_records) >= max_limit:
                    return all_records[:max_limit]

            if page_number >= max_page:
                break
            page_number += 1
            time.sleep(0.5)

        return all_records


def normalize_supplier_filters(params: Dict[str, Any]) -> List[str]:
    suppliers = params.get("suppliers")
    if isinstance(suppliers, list):
        return [str(item).strip() for item in suppliers if str(item).strip()]
    if isinstance(suppliers, str):
        return [item.strip() for item in suppliers.split(",") if item.strip()]
    return []


def normalize_sku(value: str) -> str:
    text = str(value or "")
    return "".join(text.split())


def first_non_empty(*values: object) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def _wait_if_paused(task_id: str) -> None:
    paused_logged = False
    while is_task_paused(task_id) and not is_task_terminate_requested(task_id):
        if not paused_logged:
            report_log(task_id, "任务已暂停，等待继续执行", level="WARNING")
            paused_logged = True
        time.sleep(1)
    if paused_logged and not is_task_terminate_requested(task_id):
        report_log(task_id, "任务已继续执行")


def _should_terminate(task_id: str) -> bool:
    return is_task_terminate_requested(task_id)
