from __future__ import annotations

import copy
import json
import sys
import time
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
CRAWLER_ROOT = SCRIPT_DIR.parent
if str(CRAWLER_ROOT) not in sys.path:
    sys.path.insert(0, str(CRAWLER_ROOT))

from core.browser import Browser
from platforms.kaisi.auth import CURRENT_USER_URL, KaisiAuthManager
from online_order_debug_tool import (
    PostgresAccessor,
    json_dict,
    load_db_config,
    log,
    normalize_ids,
    normalize_quotation,
)

SAVE_URL = "https://www.cassmall.com/inquiryWeb/quote/write/supplier/quote/save"
QUOTING_ITEMS_URL_TEMPLATE = "https://www.cassmall.com/inquiryWeb/quotation/{quotation_id}/quoting/items"
RESOLVE_DETAIL_URL = "https://www.cassmall.com/inquiryWeb/quotation/resolveitems/detail"


def to_builtin(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {str(key): to_builtin(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_builtin(item) for item in value]
    if isinstance(value, tuple):
        return [to_builtin(item) for item in value]
    return value


def merge_if_present(target: Dict[str, Any], key: str, value: Any) -> None:
    if value is None:
        return
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return
    target[key] = to_builtin(value)


LIVE_ITEM_PREFERRED_FIELDS: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("resolveResultId", ("resolveResultId",)),
    ("quotedPriceItemId", ("quotedPriceItemId",)),
    ("userNeedsItemId", ("userNeedsItemId",)),
    ("productId", ("productId",)),
    ("productType", ("productType",)),
    ("oldPartsNum", ("oldPartsNum",)),
    ("partsNum", ("partsNum",)),
    ("partsName", ("partsName",)),
    ("quantity", ("quantity",)),
    ("needPackage", ("needPackage",)),
    ("standardName", ("standardName", "partsName")),
    ("categoryCode", ("categoryCode",)),
    ("standardNameCode", ("standardNameCode",)),
    ("decodeSource", ("decodeSource",)),
    ("bargainFlag", ("bargainFlag",)),
    ("attrValue", ("attrValue",)),
    ("location", ("location",)),
    ("locationName", ("locationName",)),
    ("distributorStoreId", ("distributorStoreId",)),
    ("locationCountryId", ("locationCountryId",)),
    ("villageGeoId", ("villageGeoId",)),
    ("afterSaleSnapshot", ("afterSaleSnapshot",)),
    ("recommend", ("recommend",)),
    ("originalAssort", ("originalAssort",)),
    ("appendQualityFlag", ("appendQualityFlag",)),
    ("whetherProductSet", ("whetherProductSet",)),
    ("productSetCode", ("productSetCode",)),
    ("productSetId", ("productSetId",)),
    ("partRecommendingSuites", ("partRecommendingSuites",)),
    ("quotationResourceWebRequests", ("quotationResourceWebRequests", "quotationResources")),
    ("quotationProductIdentifierList", ("quotationProductIdentifierList",)),
)


def apply_live_item_overrides(target: Dict[str, Any], live_item: Optional[Dict[str, Any]]) -> None:
    if not isinstance(live_item, dict):
        return
    for target_key, source_keys in LIVE_ITEM_PREFERRED_FIELDS:
        merge_if_present(
            target,
            target_key,
            first_present_value(*(live_item.get(source_key) for source_key in source_keys)),
        )


def compact_mapping(value: Dict[str, Any]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, item in value.items():
        if item is None:
            continue
        if isinstance(item, str):
            text = item.strip()
            if not text:
                continue
            result[key] = text
            continue
        if isinstance(item, dict):
            nested = compact_mapping(item)
            if nested:
                result[key] = nested
            continue
        if isinstance(item, list):
            result[key] = [to_builtin(entry) for entry in item]
            continue
        result[key] = to_builtin(item)
    return result


def text_value(value: Any) -> str:
    return "" if value is None else str(value).strip()


def first_present_value(*values: Any) -> Any:
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return value
    return None


def to_int_or_default(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def to_float_or_default(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def numeric_present(value: Any) -> bool:
    if value is None or value == "":
        return False
    try:
        float(value)
        return True
    except Exception:
        return False


def normalize_match_key(value: Any) -> str:
    return "".join(ch for ch in text_value(value).upper() if ch.isalnum())


def prune_none(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): prune_none(item) for key, item in value.items() if item is not None}
    if isinstance(value, list):
        return [prune_none(item) for item in value]
    return to_builtin(value)


def request_json(context, method: str, url: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    headers = {"Content-Type": "application/json;charset=UTF-8"}
    try:
        if method.upper() == "GET":
            response = context.request.get(url, headers=headers, timeout=15000)
        else:
            response = context.request.post(url, data=payload, headers=headers, timeout=15000)
        body = response.json() or {}
        return body if isinstance(body, dict) else {}
    except Exception as exc:
        log(f"[live] request failed method={method.upper()}, url={url}, error={exc}")
        return {}


def fetch_live_quotation_item_rows(
    context,
    quotation_id: str,
    page_size: int = 50,
    max_pages: int = 100,
) -> List[Dict[str, Any]]:
    rows_all: List[Dict[str, Any]] = []
    total = 0
    for page in range(1, max(1, int(max_pages)) + 1):
        body = request_json(
            context,
            "POST",
            QUOTING_ITEMS_URL_TEMPLATE.format(quotation_id=quotation_id),
            payload={
                "isViewPage": True,
                "listHistoryQuoteResult": False,
                "onlyUnquote": False,
                "userNeedsItemPositiveOrder": False,
                "page": page,
                "size": page_size,
            },
        )
        data = (body or {}).get("data") or {}
        rows = data.get("content") or []
        if not isinstance(rows, list) or not rows:
            break
        rows_all.extend(rows)
        try:
            total = int(float(data.get("total") or 0))
        except Exception:
            total = 0
        if total > 0 and page * page_size >= total:
            break
    return rows_all


def fetch_live_resolve_detail_map(
    context,
    inquiry_id: str,
    store_id: str,
    quotation_rows: Sequence[Dict[str, Any]],
    chunk_size: int = 100,
) -> Dict[str, Dict[str, Any]]:
    normalized_inquiry_id = text_value(inquiry_id)
    normalized_store_id = text_value(store_id)
    if not normalized_inquiry_id or not normalized_store_id:
        return {}

    resolve_result_ids: List[str] = []
    seen: set[str] = set()
    for row in quotation_rows or []:
        store_resolve_item = (row or {}).get("storeResolveItem") or {}
        candidate_ids = [store_resolve_item.get("resolveResultId")]
        for quote_item in (row or {}).get("storeQuoteItemResults") or []:
            if isinstance(quote_item, dict):
                candidate_ids.append(quote_item.get("resolveResultId"))
        for candidate in candidate_ids:
            resolve_result_id = text_value(candidate)
            if not resolve_result_id or resolve_result_id in seen:
                continue
            seen.add(resolve_result_id)
            resolve_result_ids.append(resolve_result_id)

    resolve_detail_map: Dict[str, Dict[str, Any]] = {}
    if not resolve_result_ids:
        return resolve_detail_map

    size = max(1, int(chunk_size))
    for start in range(0, len(resolve_result_ids), size):
        chunk = resolve_result_ids[start: start + size]
        body = request_json(
            context,
            "POST",
            RESOLVE_DETAIL_URL,
            payload={
                "inquiryId": normalized_inquiry_id,
                "storeId": normalized_store_id,
                "resolveResultIds": chunk,
            },
        )
        details = (body or {}).get("data") or []
        if not isinstance(details, list):
            continue
        for detail in details:
            if not isinstance(detail, dict):
                continue
            resolve_result_id = text_value(detail.get("resolveResultId"))
            if resolve_result_id:
                resolve_detail_map[resolve_result_id] = detail
    return resolve_detail_map


def build_live_item_sources(
    quotation_rows: Sequence[Dict[str, Any]],
    resolve_detail_map: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    live_items: List[Dict[str, Any]] = []
    for row in quotation_rows or []:
        if not isinstance(row, dict):
            continue
        store_resolve_item = row.get("storeResolveItem") or {}
        default_resolve_result_id = text_value(store_resolve_item.get("resolveResultId"))
        quote_items = row.get("storeQuoteItemResults") or []
        for quote_item in quote_items:
            if not isinstance(quote_item, dict):
                continue
            resolve_result_id = text_value(quote_item.get("resolveResultId") or default_resolve_result_id)
            resolve_detail = resolve_detail_map.get(resolve_result_id) or {}
            data = {str(key): to_builtin(value) for key, value in quote_item.items()}
            merge_if_present(data, "resolveResultId", resolve_result_id)
            merge_if_present(data, "quotedPriceItemId", store_resolve_item.get("quotedPriceItemId"))
            merge_if_present(data, "resolveStatus", store_resolve_item.get("status"))
            merge_if_present(data, "resolveSource", store_resolve_item.get("source"))
            merge_if_present(data, "partsNum", resolve_detail.get("partsNum"))
            merge_if_present(data, "partsName", first_present_value(data.get("partsName"), resolve_detail.get("partsName")))
            merge_if_present(data, "standardName", first_present_value(data.get("standardName"), resolve_detail.get("partsName")))
            merge_if_present(data, "quantity", first_present_value(data.get("quantity"), resolve_detail.get("quantity")))
            merge_if_present(data, "categoryCode", resolve_detail.get("categoryCode"))
            merge_if_present(data, "standardNameCode", resolve_detail.get("standardNameCode"))
            merge_if_present(data, "decodeSource", resolve_detail.get("decodeSource"))
            merge_if_present(data, "partsBrandId", first_present_value(data.get("partsBrandId"), data.get("brandId")))
            merge_if_present(data, "partsBrandName", first_present_value(data.get("partsBrandName"), data.get("brandName")))
            merge_if_present(data, "sellStatus", first_present_value(data.get("sellStatus"), data.get("sellerStatus")))
            merge_if_present(data, "boxFee", first_present_value(data.get("boxFee"), data.get("atBoxFee"), data.get("btBoxFee")))
            if "quotationResourceWebRequests" not in data and data.get("quotationResources") is not None:
                data["quotationResourceWebRequests"] = to_builtin(data.get("quotationResources"))
            live_items.append(data)
    return live_items


def score_live_item_match(row: Dict[str, Any], live_item: Dict[str, Any]) -> int:
    score = 0
    if text_value(row.get("user_needs_item_id")) and text_value(row.get("user_needs_item_id")) == text_value(live_item.get("userNeedsItemId")):
        score += 200
    if text_value(row.get("product_id")) and text_value(row.get("product_id")) == text_value(live_item.get("productId")):
        score += 160
    if text_value(row.get("quoted_price_item_id")) and text_value(row.get("quoted_price_item_id")) == text_value(live_item.get("quotedPriceItemId")):
        score += 120
    if text_value(row.get("resolve_result_id")) and text_value(row.get("resolve_result_id")) == text_value(live_item.get("resolveResultId")):
        score += 60
    if text_value(row.get("brand_id")) and text_value(row.get("brand_id")) == text_value(
        first_present_value(live_item.get("partsBrandId"), live_item.get("brandId"))
    ):
        score += 20
    if text_value(row.get("parts_brand_quality")) and text_value(row.get("parts_brand_quality")) == text_value(live_item.get("partsBrandQuality")):
        score += 18
    if normalize_match_key(row.get("old_parts_num")) and normalize_match_key(row.get("old_parts_num")) == normalize_match_key(live_item.get("oldPartsNum")):
        score += 12
    if normalize_match_key(row.get("parts_num")) and normalize_match_key(row.get("parts_num")) == normalize_match_key(live_item.get("partsNum")):
        score += 10
    if text_value(row.get("part_type")) and text_value(row.get("part_type")) == text_value(live_item.get("partType")):
        score += 6
    return score


def pick_live_item(
    row: Dict[str, Any],
    live_items: Sequence[Dict[str, Any]],
    used_indices: set[int],
) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
    for allow_used in (False, True):
        best_index: Optional[int] = None
        best_score = 0
        for index, live_item in enumerate(live_items):
            if not allow_used and index in used_indices:
                continue
            score = score_live_item_match(row, live_item)
            if score > best_score:
                best_index = index
                best_score = score
        if best_index is not None and best_score > 0:
            return best_index, live_items[best_index]
    return None, None


class SavePostgresAccessor(PostgresAccessor):
    def quote_items_for_save(self, quotation_ids: Sequence[str]) -> List[Dict[str, Any]]:
        return self.query(
            f"""
            select
              id, quotation_id, inquiry_id, store_id, resolve_result_id, quoted_price_item_id,
              resolve_status, resolve_source, user_needs_item_id, product_id, product_type,
              old_parts_num, parts_num, parts_name, part_type, brand_id, brand_name,
              parts_brand_quality, quantity, price, bt_price, seller_price, seller_bt_price,
              seller_status, source, arrival_time, remark, cast(raw_payload as text) as raw_payload_text
            from {self.table("online_order_kaisi_quote_item")}
            where quotation_id = any(%s)
            order by quotation_id asc, store_id asc, id asc
            """,
            (list(quotation_ids),),
        )


def group_rows(rows: Iterable[Dict[str, Any]]) -> Dict[Tuple[str, str], List[Dict[str, Any]]]:
    grouped: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    for row in rows:
        quotation_id = str(row.get("quotation_id") or "").strip()
        store_id = str(row.get("store_id") or "").strip()
        if not quotation_id:
            continue
        grouped.setdefault((quotation_id, store_id), []).append(row)
    return grouped


def build_item_source(row: Dict[str, Any], live_item: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    raw = json_dict(row.get("raw_payload_text"))
    data = dict(raw)
    merge_if_present(data, "resolveResultId", row.get("resolve_result_id"))
    merge_if_present(data, "quotedPriceItemId", row.get("quoted_price_item_id"))
    merge_if_present(data, "resolveStatus", row.get("resolve_status"))
    merge_if_present(data, "resolveSource", row.get("resolve_source"))
    merge_if_present(data, "userNeedsItemId", row.get("user_needs_item_id"))
    merge_if_present(data, "productId", row.get("product_id"))
    merge_if_present(data, "productType", row.get("product_type"))
    merge_if_present(data, "oldPartsNum", row.get("old_parts_num"))
    merge_if_present(data, "partsNum", row.get("parts_num"))
    merge_if_present(data, "partsName", row.get("parts_name"))
    merge_if_present(data, "partType", row.get("part_type"))
    merge_if_present(data, "partsBrandId", row.get("brand_id"))
    merge_if_present(data, "partsBrandName", row.get("brand_name"))
    merge_if_present(data, "brandId", row.get("brand_id"))
    merge_if_present(data, "brandName", row.get("brand_name"))
    merge_if_present(data, "partsBrandQuality", row.get("parts_brand_quality"))
    merge_if_present(data, "quantity", row.get("quantity"))
    merge_if_present(data, "price", row.get("bt_price"))
    # merge_if_present(data, "btPrice", row.get("bt_price"))
    merge_if_present(data, "sellerPrice", row.get("seller_price"))
    merge_if_present(data, "sellerBtPrice", row.get("seller_bt_price"))
    merge_if_present(data, "sellerStatus", row.get("seller_status"))
    merge_if_present(data, "sellStatus", row.get("seller_status"))
    merge_if_present(data, "source", row.get("source"))
    merge_if_present(data, "arrivalTime", row.get("arrival_time"))
    merge_if_present(data, "remark", "")
    # Keep the current live item identity and fulfillment fields from Kaisi,
    # while still using local row data for quote values like price/brand/arrivalTime.
    apply_live_item_overrides(data, live_item)
    return data


def build_item_request(
    row: Dict[str, Any],
    live_item: Optional[Dict[str, Any]] = None,
    save_status: str = "DRAFT",
) -> Optional[Dict[str, Any]]:
    data = build_item_source(row, live_item=live_item)
    arrival_time_value = to_int_or_default(first_present_value(data.get("arrivalTime"), 0), 0)
    product_type_value = text_value(data.get("productType"))
    if arrival_time_value > 0:
        product_type_value = "DISPATCH_GOODS"
    price_value = to_float_or_default(first_present_value(data.get("price"), data.get("sellerPrice"), data.get("btPrice")), 0.0)
    checked_value = data.get("checked")
    if isinstance(checked_value, bool):
        checked = checked_value
    else:
        checked = price_value > 0
    payload = prune_none(
        {
            "resolveResultId": text_value(data.get("resolveResultId")),
            "partsNum": text_value(data.get("partsNum")),
            "partsName": text_value(data.get("partsName")),
            "quantity": to_int_or_default(first_present_value(data.get("quantity"), 0), 0),
            "needPackage": text_value(data.get("needPackage")) or "N",
            "standardName": text_value(first_present_value(data.get("standardName"), data.get("partsName"))),
            "categoryCode": text_value(data.get("categoryCode")),
            "standardNameCode": text_value(data.get("standardNameCode")),
            "decodeSource": text_value(data.get("decodeSource")),
            "checked": checked,
            "quotedPriceItemId": text_value(data.get("quotedPriceItemId")),
            "userNeedsItemId": text_value(data.get("userNeedsItemId")),
            "bargainFlag": text_value(data.get("bargainFlag")) or "N",
            "oldPartsNum": text_value(first_present_value(data.get("oldPartsNum"), data.get("partsNum"))),
            "partsBrandId": text_value(first_present_value(data.get("partsBrandId"), data.get("brandId"))),
            "partsBrandName": text_value(first_present_value(data.get("partsBrandName"), data.get("brandName"))),
            "attrValue": text_value(data.get("attrValue")),
            "price": price_value,
            "boxFee": to_float_or_default(first_present_value(data.get("boxFee"), data.get("atBoxFee"), data.get("btBoxFee")), 0.0),
            "location": text_value(data.get("location")),
            "locationName": text_value(data.get("locationName")),
            "distributorStoreId": text_value(data.get("distributorStoreId")),
            "locationCountryId": text_value(data.get("locationCountryId")),
            "villageGeoId": text_value(data.get("villageGeoId")),
            "productType": product_type_value,
            "arrivalTime": arrival_time_value,
            "remark": "",
            "afterSaleSnapshot": text_value(data.get("afterSaleSnapshot")),
            "partsBrandQuality": text_value(data.get("partsBrandQuality")),
            "sellStatus": text_value(first_present_value(data.get("sellStatus"), save_status, data.get("sellerStatus"))),
            "productId": text_value(data.get("productId")),
            "recommend": to_int_or_default(first_present_value(data.get("recommend"), 0), 0),
            "originalAssort": to_int_or_default(first_present_value(data.get("originalAssort"), 0), 0),
            "appendQualityFlag": text_value(data.get("appendQualityFlag")),
            "saveType": text_value(data.get("saveType")) or "ADD",
            "whetherProductSet": text_value(data.get("whetherProductSet")),
            "productSetCode": text_value(data.get("productSetCode")),
            "productSetId": text_value(data.get("productSetId")),
            "partRecommendingSuites": list(data.get("partRecommendingSuites") or []),
            "quotationResourceWebRequests": list(
                data.get("quotationResourceWebRequests")
                or data.get("quotationResources")
                or []
            ),
            "quotationProductIdentifierList": list(data.get("quotationProductIdentifierList") or []),
        }
    )
    if not payload:
        return None
    identity = (
        payload.get("quotedPriceItemId")
        or payload.get("userNeedsItemId")
        or payload.get("resolveResultId")
        or payload.get("partsNum")
    )
    return payload if identity else None


def build_save_request(
    quotation: Dict[str, Any],
    item_rows: Sequence[Dict[str, Any]],
    live_items: Optional[Sequence[Dict[str, Any]]],
    quote_user: str,
    quotation_source: str,
    save_status: str,
    back_url: str,
) -> Dict[str, Any]:
    raw = json_dict(quotation.get("raw_payload_text"))
    used_live_indices: set[int] = set()
    live_item_list = list(live_items or [])
    item_payloads: List[Dict[str, Any]] = []
    for row in item_rows:
        live_index, live_item = pick_live_item(row, live_item_list, used_live_indices)
        if live_index is not None:
            used_live_indices.add(live_index)
        payload = build_item_request(row=row, live_item=live_item, save_status=save_status)
        if payload:
            item_payloads.append(payload)

    payload = prune_none(
        {
            "inquiryId": text_value(first_present_value(quotation.get("inquiryId"), raw.get("inquiryId"))),
            "quoteSupplierHeaderId": text_value(first_present_value(raw.get("quoteSupplierHeaderId"), quotation.get("quotationId"))),
            "quotationSource": text_value(first_present_value(quotation_source, raw.get("quotationSource"))),
            "supplierCompanyId": text_value(first_present_value(quotation.get("supplierCompanyId"), raw.get("supplierCompanyId"))),
            "storeId": text_value(first_present_value(quotation.get("storeId"), raw.get("storeId"))),
            "quoteUser": text_value(first_present_value(quote_user, raw.get("quoteUser"))),
            "saveStatus": text_value(first_present_value(save_status, raw.get("saveStatus"))),
            "backUrl": back_url if back_url is not None else text_value(raw.get("backUrl")),
            "supplierQuoteItemVoRequests": item_payloads,
        }
    )
    if "supplierQuoteItemVoRequests" not in payload:
        payload["supplierQuoteItemVoRequests"] = []
    return payload


def fetch_current_user_id(context) -> str:
    response = context.request.get(CURRENT_USER_URL, timeout=15000)
    body = response.json() or {}
    data = (body or {}).get("data") or {}
    return str(data.get("userLoginId") or "").strip()


def post_save_request(context, payload: Dict[str, Any]) -> Dict[str, Any]:
    response = context.request.post(
        SAVE_URL,
        data=payload,
        headers={"Content-Type": "application/json;charset=UTF-8"},
        timeout=15000,
    )
    try:
        return response.json() or {}
    except Exception:
        return {"status": response.status, "text": response.text()}


def is_success_response(body: Dict[str, Any]) -> bool:
    if not isinstance(body, dict):
        return False
    code = body.get("code")
    if code is not None and str(code) not in {"0", "200"}:
        return False
    error_code = body.get("errorCode")
    if error_code is not None and str(error_code) not in {"0", "200"}:
        return False
    status = body.get("status")
    if status is None or status == "":
        return True
    return str(status).strip().upper() in {"SUCCESS", "OK", "0", "200"}


def remove_top_level_field(payload: Dict[str, Any], field: str) -> Dict[str, Any]:
    cloned = copy.deepcopy(payload)
    cloned.pop(field, None)
    return cloned


def remove_item_field(payload: Dict[str, Any], field: str) -> Dict[str, Any]:
    cloned = copy.deepcopy(payload)
    items = cloned.get("supplierQuoteItemVoRequests") or []
    for item in items:
        if isinstance(item, dict):
            item.pop(field, None)
    return cloned


def probe_field_impact(
    context,
    payload: Dict[str, Any],
    top_level_fields: Sequence[str],
    item_fields: Sequence[str],
    pause_seconds: float,
) -> Dict[str, Any]:
    baseline_response = post_save_request(context, payload)
    baseline_success = is_success_response(baseline_response)
    results: List[Dict[str, Any]] = [
        {
            "scope": "baseline",
            "field": "",
            "requestExecuted": True,
            "success": baseline_success,
            "response": baseline_response,
        }
    ]

    if pause_seconds > 0:
        time.sleep(pause_seconds)

    for field in top_level_fields:
        exists = field in payload
        test_payload = remove_top_level_field(payload, field)
        response = post_save_request(context, test_payload) if exists else {"skipped": True, "reason": "field_not_present"}
        success = is_success_response(response) if exists else False
        results.append(
            {
                "scope": "top-level",
                "field": field,
                "requestExecuted": exists,
                "success": success,
                "noImpact": bool(baseline_success and success),
                "response": response,
            }
        )
        if exists and pause_seconds > 0:
            time.sleep(pause_seconds)

    item_list = payload.get("supplierQuoteItemVoRequests") or []
    for field in item_fields:
        exists = any(isinstance(item, dict) and field in item for item in item_list)
        test_payload = remove_item_field(payload, field)
        response = post_save_request(context, test_payload) if exists else {"skipped": True, "reason": "field_not_present"}
        success = is_success_response(response) if exists else False
        results.append(
            {
                "scope": "item",
                "field": field,
                "requestExecuted": exists,
                "success": success,
                "noImpact": bool(baseline_success and success),
                "response": response,
            }
        )
        if exists and pause_seconds > 0:
            time.sleep(pause_seconds)

    return {
        "baselineSuccess": baseline_success,
        "baselineResponse": baseline_response,
        "topLevelNoImpactFields": [
            result["field"]
            for result in results
            if result.get("scope") == "top-level" and result.get("noImpact")
        ],
        "itemNoImpactFields": [
            result["field"]
            for result in results
            if result.get("scope") == "item" and result.get("noImpact")
        ],
        "results": results,
    }


def write_output_file(
    output_dir: Path,
    quotation_id: str,
    payload: Dict[str, Any],
    response: Dict[str, Any],
    field_probe: Optional[Dict[str, Any]],
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    output_path = output_dir / f"{quotation_id or 'unknown'}-{timestamp}.json"
    output_path.write_text(
        json.dumps(
            {
                "quotationId": quotation_id,
                "request": payload,
                "response": response,
                "fieldProbe": field_probe,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return output_path


def main() -> int:
    quotation_ids = normalize_ids(
        [
            "2984511773",
        ]
    )
    execute_request = True
    show_browser = False
    quotation_source = "PC"
    save_status = "DRAFT"
    back_url = ""
    probe_field_impact_enabled = False
    probe_pause_seconds = 0.3
    probe_top_level_fields = [
        "inquiryId",
        "quoteSupplierHeaderId",
        "quotationSource",
        "supplierCompanyId",
        "storeId",
        "quoteUser",
        "saveStatus",
        "backUrl",
    ]
    probe_item_fields = [
        "resolveResultId",
        "partsNum",
        "partsName",
        "quantity",
        "needPackage",
        "standardName",
        "categoryCode",
        "standardNameCode",
        "decodeSource",
        "checked",
        "quotedPriceItemId",
        "userNeedsItemId",
        "bargainFlag",
        "oldPartsNum",
        "partsBrandId",
        "partsBrandName",
        "attrValue",
        "price",
        "boxFee",
        "location",
        "locationName",
        "distributorStoreId",
        "locationCountryId",
        "villageGeoId",
        "productType",
        "arrivalTime",
        "remark",
        "afterSaleSnapshot",
        "partsBrandQuality",
        "sellStatus",
        "productId",
        "recommend",
        "originalAssort",
        "appendQualityFlag",
        "saveType",
        "whetherProductSet",
        "productSetCode",
        "productSetId",
        "partRecommendingSuites",
        "quotationResourceWebRequests",
        "quotationProductIdentifierList",
    ]
    output_dir = SCRIPT_DIR / "output" / "online-order-save"

    if not quotation_ids:
        raise RuntimeError("No quotation ids configured in main()")

    db = load_db_config()
    log(
        f"[db] host={db.host}, port={db.port}, db={db.dbname}, schema={db.schema}, "
        f"quotationCount={len(quotation_ids)}"
    )

    with SavePostgresAccessor(db) as accessor:
        quotation_rows = accessor.quotations(quotation_ids)
        if not quotation_rows:
            raise RuntimeError(f"No quotation rows found for ids: {','.join(quotation_ids)}")
        quotations = [normalize_quotation(row) | {"raw_payload_text": row.get("raw_payload_text")} for row in quotation_rows]
        items_by_key = group_rows(accessor.quote_items_for_save(quotation_ids))

    browser = Browser(channel="msedge", headless=not show_browser, image=False)
    results: List[Dict[str, Any]] = []
    try:
        context = KaisiAuthManager().get_context(browser, log_fn=log)
        quote_user = fetch_current_user_id(context)
        log(f"[kaisi] quoteUser={quote_user or '-'}")

        for quotation in quotations:
            quotation_id = str(quotation.get("quotationId") or "").strip()
            store_id = str(quotation.get("storeId") or "").strip()
            item_rows = items_by_key.get((quotation_id, store_id), [])
            live_rows = fetch_live_quotation_item_rows(context, quotation_id=quotation_id)
            live_resolve_detail_map = fetch_live_resolve_detail_map(
                context,
                inquiry_id=quotation.get("inquiryId"),
                store_id=store_id,
                quotation_rows=live_rows,
            )
            live_items = build_live_item_sources(live_rows, live_resolve_detail_map)
            log(
                f"[live] quotationId={quotation_id}, storeId={store_id}, "
                f"rowCount={len(live_rows)}, itemCount={len(live_items)}, resolveDetailCount={len(live_resolve_detail_map)}"
            )
            payload = build_save_request(
                quotation=quotation,
                item_rows=item_rows,
                live_items=live_items,
                quote_user=quote_user,
                quotation_source=quotation_source,
                save_status=save_status,
                back_url=back_url,
            )
            log(
                f"[save] quotationId={quotation_id}, storeId={store_id}, "
                f"itemCount={len(payload.get('supplierQuoteItemVoRequests') or [])}"
            )
            log(json.dumps(payload, ensure_ascii=False, indent=2))

            if execute_request:
                response = post_save_request(context, payload)
                log(f"[save] response quotationId={quotation_id}: {json.dumps(response, ensure_ascii=False, indent=2)}")
            else:
                response = {"dryRun": True}
                log(f"[save] dry-run quotationId={quotation_id}")

            field_probe = None
            if execute_request and probe_field_impact_enabled:
                log(f"[probe] start quotationId={quotation_id}")
                field_probe = probe_field_impact(
                    context=context,
                    payload=payload,
                    top_level_fields=probe_top_level_fields,
                    item_fields=probe_item_fields,
                    pause_seconds=probe_pause_seconds,
                )
                log(
                    "[probe] summary quotationId="
                    f"{quotation_id}, topLevelNoImpactFields={field_probe.get('topLevelNoImpactFields') or []}, "
                    f"itemNoImpactFields={field_probe.get('itemNoImpactFields') or []}"
                )

            output_path = write_output_file(output_dir, quotation_id, payload, response, field_probe)
            log(f"[output] saved {output_path}")
            results.append(
                {
                    "quotationId": quotation_id,
                    "storeId": store_id,
                    "request": payload,
                    "response": response,
                    "fieldProbe": field_probe,
                    "output": str(output_path),
                }
            )
    finally:
        browser.stop()

    log(json.dumps({"results": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
