import random
import time
from typing import Dict, Any, List, Tuple, Optional

from core.task_queue import is_task_paused, is_task_terminate_requested
from service.reporter import report_log


class BenbenCrawler:
    QUERY_ID_URL = "https://api.apbenben.com/benben-dubbo-web/auth/search/getQueryId"
    LOAD_PARTS_URL = "https://api.apbenben.com/benben-dubbo-web/auth/search/loadPartsByPage"
    DEFAULT_LEIDS = ",6,8,9,14,15,16,19,21,24,26,27,52,92,"
    MAX_REMARK_SKU_COUNT = 10

    # 处理__init__的相关逻辑。
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
        self.retry_count = 5
        self.sku_query_context: Dict[str, Dict[str, str]] = {}

    def set_log_task_id(self, task_id: str) -> None:
        normalized_task_id = str(task_id or "").strip()
        self.log_task_id = normalized_task_id or self.control_task_id
        self.task_id = self.log_task_id

    def _control_task_id(self) -> str:
        return str(self.control_task_id or self.task_id).strip()

    # 查询标识。
    def _query_id(self) -> str:
        params = {}
        headers = {"Content-Type": "application/json;charset=UTF-8"}
        response = self.context.request.post(url=self.QUERY_ID_URL, data=params, headers=headers).json()
        return (response or {}).get("data", "") or ""

    # 处理sharedquery。
    def prepare_shared_query(self, skus: List[str]) -> bool:
        cleaned = [normalize_sku(item) for item in (skus or [])]
        cleaned = [item for item in cleaned if item]
        if not cleaned:
            return False

        unique_skus = list(dict.fromkeys(cleaned))
        self.sku_query_context = {}
        chunks = [
            unique_skus[index:index + self.MAX_REMARK_SKU_COUNT]
            for index in range(0, len(unique_skus), self.MAX_REMARK_SKU_COUNT)
        ]

        if len(chunks) > 1:
            report_log(
                self.task_id,
                f"SKU数量超过{self.MAX_REMARK_SKU_COUNT}，将分{len(chunks)}批查询",
            )

        for batch_no, batch_skus in enumerate(chunks, start=1):
            query_id = self._query_id()
            if not query_id:
                report_log(
                    self.task_id,
                    f"第{batch_no}批未查询到共享query_id，批次SKU数={len(batch_skus)}",
                    level="WARNING",
                )
                return False

            remark = ",".join(batch_skus)
            for sku in batch_skus:
                self.sku_query_context[sku] = {
                    "query_id": query_id,
                    "remark": remark,
                }
            report_log(
                self.task_id,
                f"第{batch_no}批共享query_id已生成，批次SKU数={len(batch_skus)}",
            )

        report_log(self.task_id, f"共享query_id准备完成，总SKU数={len(unique_skus)}")
        return True

    # 加载partsbypage。
    def _load_parts_by_page(
        self,
        sku: str,
        query_id: str,
        remark: str,
        page: int,
        quality_origin_ids: str = "",
        supplier_ids: str = "",
        brand_names: str = "",
        region_origin_ids: str = "",
        page_size: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        _wait_if_paused(self._control_task_id())
        if _should_terminate(self._control_task_id()):
            return [], 1

        params = {
            "key": sku,
            "leids": self.DEFAULT_LEIDS,
            "cityDft": "420100",
            "cityOthers":  "",
            "remark": remark,
            "queryCityType": 1,
            "queryType": 1,
            "reKey": "",
            "queryId": query_id,
            "proOtherCityCodes": "420200,420300,420500,420600,420700,420800,420900,421000,421100,421200,421300,422800,429000",
            "carTypeName": "",
            "isOems": self._resolve_quality_origin_ids(quality_origin_ids),
            "brandNames": brand_names or self.brand_names,
            "city": "",
            "supplierId": supplier_ids or self.supplier_ids,
            "categoryFirst": "",
            "categorySecond": "",
            "isMargin": "",
            "isAttention": "",
            "isPayOnline": "",
            "stockStatus": 1,
            "isPrice": "",
            "isYx": "",
            "isPromotion": "",
            "isSearchSwap": "",
            "page": page,
            "pageSize": page_size,
        }
        headers = {"Content-Type": "application/json;charset=UTF-8"}

        for attempt in range(1, self.retry_count + 1):
            try:
                response = self.context.request.post(
                    url=self.LOAD_PARTS_URL,
                    data=params,
                    headers=headers,
                    timeout=3000,
                ).json()
                payload = (response or {}).get("data", {}) or {}
                max_page = payload.get("maxPage", 1) or 1
                rows = payload.get("items", []) or []

                records: List[Dict[str, Any]] = []
                for item in rows:
                    supplier_abbr = (item.get("supplierAbbreviation") or "").strip()
                    supplier_name = (item.get("supplierName") or "").strip()
                    supplier_id = first_non_empty(
                        item.get("supplierId"),
                        item.get("supplierID"),
                        item.get("supplier_id"),
                        item.get("supplierNo"),
                        item.get("sellerId"),
                        item.get("companyId"),
                    )

                    if self.suppliers and supplier_abbr not in self.suppliers and supplier_name not in self.suppliers:
                        continue

                    price = first_non_empty(
                        item.get("finalBatchPrice"),
                        item.get("batchPrice"),
                        item.get("salePrice"),
                        item.get("price"),
                    )
                    stock = item.get("stock", 0)
                    brand_name = _extract_brand_name(item)
                    brand_origin_id = _extract_brand_origin_id(item)
                    quality_name = _extract_quality_name(item)
                    quality_origin_id = _extract_quality_origin_id(item)
                    region_name = _extract_region_name(item)
                    region_origin_id = _extract_region_origin_id(item)
                    record = {
                        "sku": sku,
                        "crawlPlatform": "BENBEN",
                        "platformCode": "BENBEN",
                        "productName": item.get("cname"),
                        "brand": brand_name,
                        "brandName": brand_name,
                        "brandOriginId": brand_origin_id,
                        "region": region_name,
                        "regionName": region_name,
                        "regionOriginId": region_origin_id,
                        "qualityName": quality_name,
                        "qualityOriginId": quality_origin_id,
                        "companyName": supplier_name,
                        "supplierName": supplier_abbr or supplier_name,
                        "supplierId": supplier_id,
                        "stock": stock if stock is not None else 0,
                        "price": price,
                        "rawPayload": item,
                    }
                    records.append(record)
                    report_log(self.task_id, f"抓取记录: {record}")

                # 保持历史节奏，避免请求过于频繁触发限流。
                time.sleep(random.randint(1, 5))
                return records, int(max_page)
            except Exception as exc:
                if attempt < self.retry_count:
                    report_log(
                        self.task_id,
                        f"请求超时，开始第 {attempt + 1} 次重试，sku={sku}，页码={page}",
                        level="WARNING",
                    )
                else:
                    report_log(
                        self.task_id,
                        f"达到最大重试次数（{self.retry_count}），sku={sku}，页码={page}，错误={exc}",
                        level="ERROR",
                    )

        return [], 1

    # 处理SKU。
    def crawl_sku(
        self,
        sku: str,
        quality_origin_ids: str = "",
        supplier_ids: str = "",
        brand_names: str = "",
        region_origin_ids: str = "",
    ) -> List[Dict[str, Any]]:
        _wait_if_paused(self._control_task_id())
        if _should_terminate(self._control_task_id()):
            return []

        query_context = self.sku_query_context.get(sku)
        if not query_context:
            report_log(self.task_id, f"未找到SKU对应的查询上下文，SKU={sku}", level="WARNING")
            return []
        query_id = query_context.get("query_id", "")
        remark = query_context.get("remark", "")

        page = 1
        all_records: List[Dict[str, Any]] = []
        max_crawl_count = self.single_sku_max_crawl_count

        report_log(self.task_id, f"开始抓取 SKU={sku}，页码={page}")
        records, max_page = self._load_parts_by_page(
            sku=sku,
            query_id=query_id,
            remark=remark,
            page=page,
            quality_origin_ids=quality_origin_ids,
            supplier_ids=supplier_ids,
            brand_names=brand_names,
            region_origin_ids=region_origin_ids,
            page_size=self._resolve_page_size(len(all_records)),
        )
        all_records.extend(records)

        if max_crawl_count > 0 and len(all_records) >= max_crawl_count:
            limited = all_records[:max_crawl_count]
            preview = [
                {
                    "supplierId": item.get("supplierId"),
                    "brandOriginId": item.get("brandOriginId"),
                    "qualityOriginId": item.get("qualityOriginId"),
                    "regionOriginId": item.get("regionOriginId"),
                    "price": item.get("price"),
                }
                for item in limited[:3]
            ]
            print(
                f"[crawl_sku] result sku={sku}, count={len(limited)}, preview={preview}",
                flush=True,
            )
            return limited

        while max_page > 1 and page < max_page:
            _wait_if_paused(self._control_task_id())
            if _should_terminate(self._control_task_id()):
                break
            page += 1
            report_log(self.task_id, f"继续抓取 SKU={sku}，页码={page}")
            records, _ = self._load_parts_by_page(
                sku=sku,
                query_id=query_id,
                remark=remark,
                page=page,
                quality_origin_ids=quality_origin_ids,
                supplier_ids=supplier_ids,
                brand_names=brand_names,
                region_origin_ids=region_origin_ids,
                page_size=self._resolve_page_size(len(all_records)),
            )
            all_records.extend(records)

            if max_crawl_count > 0 and len(all_records) >= max_crawl_count:
                report_log(
                    self.task_id,
                    f"Hit single SKU crawl limit, sku={sku}, limit={max_crawl_count}",
                )
                limited = all_records[:max_crawl_count]
                preview = [
                    {
                        "supplierId": item.get("supplierId"),
                        "brandOriginId": item.get("brandOriginId"),
                        "qualityOriginId": item.get("qualityOriginId"),
                        "regionOriginId": item.get("regionOriginId"),
                        "price": item.get("price"),
                    }
                    for item in limited[:3]
                ]
                print(
                    f"[crawl_sku] result sku={sku}, count={len(limited)}, preview={preview}",
                    flush=True,
                )
                return limited

        preview = [
            {
                "supplierId": item.get("supplierId"),
                "brandOriginId": item.get("brandOriginId"),
                "qualityOriginId": item.get("qualityOriginId"),
                "regionOriginId": item.get("regionOriginId"),
                "price": item.get("price"),
            }
            for item in all_records[:3]
        ]
        print(
            f"[crawl_sku] result sku={sku}, count={len(all_records)}, preview={preview}",
            flush=True,
        )
        return all_records

    # 解析leids。
    def _resolve_leids(self) -> str:
        if not self.quality_codes:
            return self.DEFAULT_LEIDS
        parts = [item.strip() for item in self.quality_codes.split(",") if item and item.strip()]
        if not parts:
            return self.DEFAULT_LEIDS
        joined = ",".join(parts)
        if not joined.startswith(","):
            joined = f",{joined}"
        if not joined.endswith(","):
            joined = f"{joined},"
        return joined

    def _resolve_page_size(self, current_count: int) -> int:
        if self.single_sku_max_crawl_count <= 0:
            return 20
        remaining = self.single_sku_max_crawl_count - max(int(current_count or 0), 0)
        if remaining <= 0:
            return 1
        return max(1, min(20, remaining))

    def _resolve_quality_origin_ids(self, quality_origin_ids: str) -> str:
        source = quality_origin_ids or self.quality_origin_ids
        parts = [item.strip() for item in str(source or "").split(",") if item and item.strip()]
        if not parts:
            return ""
        unique_parts = list(dict.fromkeys(parts))
        return ",".join(unique_parts)

# 规范化供应商filters。
def normalize_supplier_filters(params: Dict[str, Any]) -> List[str]:
    suppliers = params.get("suppliers")
    if isinstance(suppliers, list):
        return [str(item).strip() for item in suppliers if str(item).strip()]
    if isinstance(suppliers, str):
        return [item.strip() for item in suppliers.split(",") if item.strip()]
    return []

# 规范化SKU。
def normalize_sku(value: str) -> str:
    text = str(value or "")
    return "".join(text.split())

# 处理nonempty。
def first_non_empty(*values: object) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""

# 处理品牌name。
def _extract_brand_name(item: Dict[str, Any]) -> str:
    return first_non_empty(
        item.get("standardManufacturerCname"),
        item.get("brandName"),
        item.get("manufacturerName"),
        item.get("manufacturerCname"),
        item.get("standardBrandName"),
    )

# 处理品牌origin标识。
def _extract_brand_origin_id(item: Dict[str, Any]) -> str:
    return first_non_empty(
        item.get("standardManufacturerId"),
        item.get("standardManufacturerCid"),
        item.get("brandId"),
        item.get("brandID"),
        item.get("manufacturerId"),
        item.get("manufacturerID"),
    )

# 处理qualityname。
def _extract_quality_name(item: Dict[str, Any]) -> str:
    return first_non_empty(
        item.get("qualityName"),
        item.get("partsQualityName"),
        item.get("levelName"),
        item.get("levName"),
        item.get("leiName"),
        item.get("leidName"),
    )

# 处理qualityorigin标识。
def _extract_quality_origin_id(item: Dict[str, Any]) -> str:
    return first_non_empty(
        item.get("qualityOriginId"),
        item.get("qualityId"),
        item.get("leid"),
        item.get("leId"),
        item.get("leiId"),
        item.get("levelId"),
        item.get("levId"),
    )

# 处理区域name。
def _extract_region_name(item: Dict[str, Any]) -> str:
    return first_non_empty(
        item.get("city"),
        item.get("cityName"),
        item.get("regionName"),
        item.get("storeCity"),
    )

# 处理区域origin标识。
def _extract_region_origin_id(item: Dict[str, Any]) -> str:
    return first_non_empty(
        item.get("cityId"),
        item.get("cityCode"),
        item.get("regionId"),
        item.get("regionOriginId"),
        item.get("storeCityId"),
    )

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
