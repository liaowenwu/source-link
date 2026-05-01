from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional, Sequence, Tuple

from platforms.kaisi.auth import CURRENT_USER_URL

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


def merge_if_present(target: Dict[str, Any], key: str, value: Any) -> None:
    if value is None:
        return
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return
    target[str(key)] = to_builtin(value)


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


def prune_none(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): prune_none(item) for key, item in value.items() if item is not None}
    if isinstance(value, list):
        return [prune_none(item) for item in value]
    return to_builtin(value)


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


def normalize_match_key(value: Any) -> str:
    return "".join(ch for ch in text_value(value).upper() if ch.isalnum())


def to_object_map(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    text = text_value(value)
    if not text:
        return {}
    try:
        import json

        payload = json.loads(text)
    except Exception:
        return {}
    return dict(payload) if isinstance(payload, dict) else {}


def request_json(context, method: str, url: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    headers = {"Content-Type": "application/json;charset=UTF-8"}
    try:
        if method.upper() == "GET":
            response = context.request.get(url, headers=headers, timeout=15000)
        else:
            response = context.request.post(url, data=payload, headers=headers, timeout=15000)
        body = response.json() or {}
        return body if isinstance(body, dict) else {}
    except Exception:
        return {}


def fetch_current_user_id(context) -> str:
    body = request_json(context, "GET", CURRENT_USER_URL)
    data = (body or {}).get("data") or {}
    return text_value(data.get("userLoginId"))


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


def extract_response_message(body: Dict[str, Any]) -> str:
    if not isinstance(body, dict):
        return ""
    for key in ("errorMessage", "message", "msg"):
        value = body.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    data = body.get("data")
    if isinstance(data, dict):
        for key in ("errorMessage", "message", "msg"):
            value = data.get(key)
            if value is not None and str(value).strip():
                return str(value).strip()
    return ""


def post_save_request(context, payload: Dict[str, Any]) -> Dict[str, Any]:
    headers = {"Content-Type": "application/json;charset=UTF-8"}
    try:
        response = context.request.post(
            SAVE_URL,
            data=payload,
            headers=headers,
            timeout=15000,
        )
        try:
            body = response.json() or {}
            return body if isinstance(body, dict) else {"status": response.status, "text": response.text()}
        except Exception:
            return {"status": response.status, "text": response.text()}
    except Exception as exc:
        return {"exception": True, "errorMessage": str(exc)}


def fetch_live_quotation_item_rows(
    context,
    quotation_id: str,
    page_size: int = 50,
    max_pages: int = 100,
) -> List[Dict[str, Any]]:
    rows_all: List[Dict[str, Any]] = []
    total = 0
    normalized_quotation_id = text_value(quotation_id)
    if not normalized_quotation_id:
        return rows_all
    for page in range(1, max(1, int(max_pages)) + 1):
        body = request_json(
            context,
            "POST",
            QUOTING_ITEMS_URL_TEMPLATE.format(quotation_id=normalized_quotation_id),
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
        rows_all.extend([row for row in rows if isinstance(row, dict)])
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
    seen = set()
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


def normalize_runtime_item(item: Dict[str, Any]) -> Dict[str, Any]:
    raw = to_object_map(item.get("rawPayload"))
    data = dict(raw)
    for key, value in item.items():
        merge_if_present(data, key, value)
    merge_if_present(data, "partsBrandId", first_present_value(item.get("partsBrandId"), item.get("brandId")))
    merge_if_present(data, "partsBrandName", first_present_value(item.get("partsBrandName"), item.get("brandName")))
    merge_if_present(data, "sellStatus", first_present_value(item.get("sellStatus"), item.get("sellerStatus")))
    merge_if_present(data, "boxFee", first_present_value(item.get("boxFee"), item.get("atBoxFee"), item.get("btBoxFee")))
    return data


def score_live_item_match(item: Dict[str, Any], live_item: Dict[str, Any]) -> int:
    score = 0
    current = normalize_runtime_item(item)
    current_user_needs_item_id = text_value(first_present_value(current.get("userNeedsItemId"), current.get("user_needs_item_id")))
    current_product_id = text_value(first_present_value(current.get("productId"), current.get("product_id")))
    current_quoted_price_item_id = text_value(first_present_value(current.get("quotedPriceItemId"), current.get("quoted_price_item_id")))
    current_resolve_result_id = text_value(first_present_value(current.get("resolveResultId"), current.get("resolve_result_id")))
    current_brand_id = text_value(first_present_value(current.get("partsBrandId"), current.get("brandId"), current.get("brand_id")))
    current_quality = text_value(first_present_value(current.get("partsBrandQuality"), current.get("parts_brand_quality")))
    current_old_parts_num = text_value(first_present_value(current.get("oldPartsNum"), current.get("old_parts_num")))
    current_parts_num = text_value(first_present_value(current.get("partsNum"), current.get("parts_num")))
    current_part_type = text_value(first_present_value(current.get("partType"), current.get("part_type")))

    if current_user_needs_item_id and current_user_needs_item_id == text_value(live_item.get("userNeedsItemId")):
        score += 200
    if current_product_id and current_product_id == text_value(live_item.get("productId")):
        score += 160
    if current_quoted_price_item_id and current_quoted_price_item_id == text_value(live_item.get("quotedPriceItemId")):
        score += 120
    if current_resolve_result_id and current_resolve_result_id == text_value(live_item.get("resolveResultId")):
        score += 60
    if current_brand_id and current_brand_id == text_value(first_present_value(live_item.get("partsBrandId"), live_item.get("brandId"))):
        score += 20
    if current_quality and current_quality == text_value(live_item.get("partsBrandQuality")):
        score += 18
    if normalize_match_key(current_old_parts_num) and normalize_match_key(current_old_parts_num) == normalize_match_key(live_item.get("oldPartsNum")):
        score += 12
    if normalize_match_key(current_parts_num) and normalize_match_key(current_parts_num) == normalize_match_key(live_item.get("partsNum")):
        score += 10
    if current_part_type and current_part_type == text_value(live_item.get("partType")):
        score += 6
    return score


def pick_live_item(
    item: Dict[str, Any],
    live_items: Sequence[Dict[str, Any]],
    used_indices: set[int],
) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
    for allow_used in (False, True):
        best_index: Optional[int] = None
        best_score = 0
        for index, live_item in enumerate(live_items):
            if not allow_used and index in used_indices:
                continue
            score = score_live_item_match(item, live_item)
            if score > best_score:
                best_index = index
                best_score = score
        if best_index is not None and best_score > 0:
            return best_index, live_items[best_index]
    return None, None


def build_item_request(
    item: Dict[str, Any],
    live_item: Optional[Dict[str, Any]] = None,
    save_status: str = "DRAFT",
) -> Optional[Dict[str, Any]]:
    data = normalize_runtime_item(item)
    if isinstance(live_item, dict):
        merged = dict(data)
        # Keep the current live item identity and fulfillment fields from Kaisi,
        # while still allowing runtime quote fields like price/brand/arrivalTime to override.
        apply_live_item_overrides(merged, live_item)
        data = merged
    arrival_time_value = to_int_or_default(first_present_value(data.get("arrivalTime"), 0), 0)
    product_type_value = text_value(data.get("productType"))
    if arrival_time_value > 0:
        product_type_value = "DISPATCH_GOODS"
    price_value = to_float_or_default(
        first_present_value(
            data.get("btPrice"),
            data.get("bt_price"),
            data.get("price"),
            data.get("sellerBtPrice"),
            data.get("sellerPrice"),
        ),
        0.0,
    )
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
    identity = (
        payload.get("quotedPriceItemId")
        or payload.get("userNeedsItemId")
        or payload.get("resolveResultId")
        or payload.get("partsNum")
    )
    return payload if identity else None


def build_save_request(
    quotation: Dict[str, Any],
    item_requests: Sequence[Dict[str, Any]],
    quote_user: str,
    quotation_source: str = "PC",
    save_status: str = "DRAFT",
    back_url: str = "",
) -> Dict[str, Any]:
    return prune_none(
        {
            "inquiryId": text_value(quotation.get("inquiryId")),
            "quoteSupplierHeaderId": text_value(first_present_value(quotation.get("quoteSupplierHeaderId"), quotation.get("quotationId"), quotation.get("id"))),
            "quotationSource": text_value(quotation_source or "PC"),
            "supplierCompanyId": text_value(quotation.get("supplierCompanyId")),
            "storeId": text_value(quotation.get("storeId")),
            "quoteUser": text_value(quote_user),
            "saveStatus": text_value(save_status or "DRAFT"),
            "backUrl": back_url if back_url is not None else "",
            "supplierQuoteItemVoRequests": list(item_requests or []),
        }
    )


def build_submit_results(
    *,
    quotation_id: str,
    store_id: str,
    items: Sequence[Dict[str, Any]],
    request_items: Sequence[Optional[Dict[str, Any]]],
    response: Dict[str, Any],
    success: bool,
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    response_message = extract_response_message(response)
    for index, item in enumerate(items or []):
        request_item = request_items[index] if index < len(request_items) else None
        submit_status = "SUCCESS" if success and request_item else "FAILED"
        error_message = None
        if request_item is None:
            error_message = "Quotation item request build failed"
        elif not success:
            error_message = response_message or "Quotation save failed"
        results.append(
            {
                "quotationId": quotation_id,
                "storeId": store_id,
                "resolveResultId": item.get("resolveResultId"),
                "partsNum": item.get("partsNum"),
                "partsName": item.get("partsName"),
                "submitStatus": submit_status,
                "submitRequest": request_item,
                "submitResponse": response,
                "errorMessage": error_message,
            }
        )
    return results


def save_online_order_quotation(
    *,
    context,
    quotation: Dict[str, Any],
    items: Sequence[Dict[str, Any]],
    quote_user: str = "",
    quotation_source: str = "PC",
    save_status: str = "DRAFT",
    back_url: str = "",
) -> Dict[str, Any]:
    normalized_quotation = dict(quotation or {})
    quotation_id = text_value(first_present_value(normalized_quotation.get("quotationId"), normalized_quotation.get("id")))
    store_id = text_value(normalized_quotation.get("storeId"))
    inquiry_id = text_value(normalized_quotation.get("inquiryId"))
    normalized_items = [dict(item) for item in (items or []) if isinstance(item, dict)]
    if not quotation_id:
        raise RuntimeError("Quotation id is required")
    if not normalized_items:
        raise RuntimeError("Quotation items are empty")

    live_rows = fetch_live_quotation_item_rows(context, quotation_id=quotation_id)
    live_resolve_detail_map = fetch_live_resolve_detail_map(
        context,
        inquiry_id=inquiry_id,
        store_id=store_id,
        quotation_rows=live_rows,
    )
    live_items = build_live_item_sources(live_rows, live_resolve_detail_map)
    used_live_indices: set[int] = set()
    request_items: List[Optional[Dict[str, Any]]] = []
    valid_request_items: List[Dict[str, Any]] = []
    for item in normalized_items:
        live_index, live_item = pick_live_item(item, live_items, used_live_indices)
        if live_index is not None:
            used_live_indices.add(live_index)
        request_item = build_item_request(item=item, live_item=live_item, save_status=save_status)
        request_items.append(request_item)
        if request_item is not None:
            valid_request_items.append(request_item)

    if not valid_request_items:
        raise RuntimeError("Quotation save request items are empty")

    resolved_quote_user = text_value(quote_user) or fetch_current_user_id(context)
    payload = build_save_request(
        quotation=normalized_quotation,
        item_requests=valid_request_items,
        quote_user=resolved_quote_user,
        quotation_source=quotation_source,
        save_status=save_status,
        back_url=back_url,
    )
    response = post_save_request(context, payload)
    success = is_success_response(response) and all(item is not None for item in request_items)
    submit_results = build_submit_results(
        quotation_id=quotation_id,
        store_id=store_id,
        items=normalized_items,
        request_items=request_items,
        response=response,
        success=success,
    )
    success_count = sum(1 for row in submit_results if row.get("submitStatus") == "SUCCESS")
    fail_count = len(submit_results) - success_count
    response_message = extract_response_message(response)
    message = (
        f"Quotation save finished: success={success_count}, failed={fail_count}"
        if success
        else f"Quotation save failed: {response_message or 'unknown error'}"
    )
    return {
        "quotationId": quotation_id,
        "storeId": store_id,
        "quoteUser": resolved_quote_user,
        "request": payload,
        "response": response,
        "success": success,
        "message": message,
        "submitResults": submit_results,
        "successCount": success_count,
        "failCount": fail_count,
        "liveRowCount": len(live_rows),
        "liveItemCount": len(live_items),
        "resolveDetailCount": len(live_resolve_detail_map),
    }
