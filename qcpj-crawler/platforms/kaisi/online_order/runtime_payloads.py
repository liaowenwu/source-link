from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from .runtime_support import now_iso


def _slim_quote_item(record: Dict[str, Any]) -> Dict[str, Any]:
    raw_payload = _to_object_map(record.get("rawPayload"))
    old_parts_num = str(record.get("oldPartsNum") or "")
    parts_num = str(record.get("partsNum") or "")
    item_id = _to_int(
        record.get("itemId")
        or record.get("id")
        or raw_payload.get("itemId")
        or raw_payload.get("id")
    )
    quoted_price_item_id = str(
        record.get("quotedPriceItemId")
        or raw_payload.get("quotedPriceItemId")
        or ""
    ).strip()
    user_needs_item_id = str(
        record.get("userNeedsItemId")
        or raw_payload.get("userNeedsItemId")
        or ""
    ).strip()
    source = str(record.get("source") or raw_payload.get("source") or "").strip()
    # Do not trust the upstream quotation-item source flag for local AUTO/MANUALLY semantics.
    # Queue1/status sync should preserve the backend source that was already decided locally.
    slim_raw_payload = {
        "oldPartsNum": old_parts_num,
        "partsNum": parts_num,
        "id": item_id,
        "itemId": item_id,
        "quotedPriceItemId": quoted_price_item_id,
        "userNeedsItemId": user_needs_item_id,
        "source": source,
    }
    slim_raw_payload = {
        key: value for key, value in slim_raw_payload.items()
        if value not in ("", None)
    }
    if not slim_raw_payload:
        slim_raw_payload = None

    return {
        "id": item_id,
        "itemId": item_id,
        "recordType": str(record.get("recordType") or ""),
        "quotationId": str(record.get("quotationId") or ""),
        "quotationCreatedStamp": record.get("quotationCreatedStamp"),
        "createdStamp": record.get("createdStamp"),
        "inquiryId": str(record.get("inquiryId") or ""),
        "storeId": str(record.get("storeId") or ""),
        "resolveResultId": str(record.get("resolveResultId") or ""),
        "quotedPriceItemId": quoted_price_item_id,
        "userNeedsItemId": user_needs_item_id,
        "resolveStatus": str(record.get("resolveStatus") or ""),
        "statusIdDesc": str(record.get("statusIdDesc") or ""),
        "oldPartsNum": old_parts_num,
        "partsNum": parts_num,
        "partsName": str(record.get("partsName") or ""),
        "brandId": str(record.get("brandId") or ""),
        "brandName": str(record.get("brandName") or ""),
        "source": source,
        "partsBrandQuality": str(record.get("partsBrandQuality") or ""),
        "quantity": record.get("quantity"),
        "price": record.get("price"),
        "btPrice": record.get("btPrice"),
        "platformPrice": record.get("platformPrice"),
        "arrivalTime": record.get("arrivalTime"),
        "remark": str(record.get("remark") or ""),
        "productType": str(record.get("productType") or ""),
        "partType": str(record.get("partType") or ""),
        # Keep the backend fallback fields, but avoid shipping the full Kaisi raw item.
        "rawPayload": slim_raw_payload,
    }


def build_quotation_payload(
    *,
    manual_price_fill_enabled: bool,
    auto_submit_enabled: bool,
    quotation: Dict[str, Any],
    detail: Dict[str, Any],
) -> Dict[str, Any]:
    quotation_id = str(detail.get("quotationId") or quotation.get("id") or quotation.get("quotationId") or "")
    inquiry_id = str(detail.get("inquiryId") or quotation.get("inquiryId") or "")
    store_id = str(detail.get("storeId") or quotation.get("storeId") or "")
    items = [_slim_quote_item(item) for item in (detail.get("quoteRecords") or []) if isinstance(item, dict)]
    return {
        "platform": "kaisi",
        "scene": "online_order",
        "manualPriceFillEnabled": manual_price_fill_enabled,
        "autoSubmitEnabled": auto_submit_enabled,
        "quotationId": quotation_id,
        "inquiryId": inquiry_id,
        "storeId": store_id,
        "supplierCompanyId": str(quotation.get("supplierCompanyId") or ""),
        "statusId": str(detail.get("statusId") or quotation.get("statusId") or ""),
        "statusIdDesc": str(detail.get("statusIdDesc") or quotation.get("statusIdDesc") or ""),
        "displayModelName": str(quotation.get("displayModelName") or ""),
        "itemCount": detail.get("itemCount") or len(items),
        "createdStamp": quotation.get("createdStamp"),
        "lastUpdatedStamp": quotation.get("lastUpdatedStamp"),
        "items": items,
        "flowStatus": "WAIT_PRICE_FILL" if manual_price_fill_enabled else "PRICE_FILLING",
        "processStatus": "PROCESSING",
        "currentNodeCode": "RECEIVE_QUOTATION_DETAIL",
        "currentNodeName": "报价单详情同步",
        "message": "报价单详情已同步到后端",
    }


def build_status_payload(
    *,
    manual_price_fill_enabled: bool,
    auto_submit_enabled: bool,
    quotation_id: str,
    store_id: str,
    flow_status: str,
    process_status: str,
    current_node_code: str,
    current_node_name: str,
    message: str,
    seed: Optional[Dict[str, Any]] = None,
    error_message: str = "",
) -> Dict[str, Any]:
    row = seed or {}
    return {
        "platform": "kaisi",
        "scene": "online_order",
        "manualPriceFillEnabled": manual_price_fill_enabled,
        "autoSubmitEnabled": auto_submit_enabled,
        "quotationId": quotation_id,
        "storeId": store_id,
        "inquiryId": str(row.get("inquiryId") or ""),
        "statusId": str(row.get("statusId") or ""),
        "statusIdDesc": str(row.get("statusIdDesc") or ""),
        "displayModelName": str(row.get("displayModelName") or ""),
        "flowStatus": flow_status,
        "processStatus": process_status,
        "currentNodeCode": current_node_code,
        "currentNodeName": current_node_name,
        "message": message,
        "errorMessage": error_message or None,
        "createdAt": now_iso(),
    }


def build_submit_payload(
    *,
    quotation_id: str,
    store_id: str,
    process_status: str,
    submit_results: List[Dict[str, Any]],
    message: str,
) -> Dict[str, Any]:
    return {
        "platform": "kaisi",
        "scene": "online_order",
        "quotationId": quotation_id,
        "storeId": store_id,
        "flowStatus": "COMPLETED",
        "processStatus": process_status,
        "currentNodeCode": "SUBMIT_QUOTATION",
        "currentNodeName": "提交报价单",
        "message": message,
        "submitResults": submit_results,
        "submittedAt": now_iso(),
    }


def apply_auto_fill_result(context_row: Dict[str, Any], payload: Dict[str, Any]) -> None:
    items = [item for item in (context_row.get("items") or []) if isinstance(item, dict)]
    if not items:
        return

    target_item_id = _to_int(payload.get("onlineOrderItemId") or payload.get("itemId") or payload.get("id"))
    quoted_price_item_id = _normalize_text(payload.get("quotedPriceItemId"))
    user_needs_item_id = _normalize_text(payload.get("userNeedsItemId"))
    resolve_result_id = _normalize_text(payload.get("resolveResultId"))
    parts_num = _normalize_parts_num(payload.get("partsNum"))

    for item in items:
        item_id = _candidate_item_id(item)
        if target_item_id is not None and item_id == target_item_id:
            _apply_payload_to_item(item, payload)
            return

    for field_name, field_value in (
        ("quotedPriceItemId", quoted_price_item_id),
        ("userNeedsItemId", user_needs_item_id),
    ):
        if not field_value:
            continue
        for item in items:
            if _item_field_text(item, field_name) == field_value:
                _apply_payload_to_item(item, payload)
                return

    same_resolve_items = [
        item
        for item in items
        if resolve_result_id and _normalize_text(item.get("resolveResultId")) == resolve_result_id
    ]
    matched_item = _pick_single_pending_item(same_resolve_items)
    if matched_item is not None:
        _apply_payload_to_item(matched_item, payload)
        return

    same_parts_items = [
        item
        for item in items
        if parts_num and _normalize_parts_num(item.get("partsNum")) == parts_num
    ]
    matched_item = _pick_single_pending_item(same_parts_items)
    if matched_item is not None:
        _apply_payload_to_item(matched_item, payload)


def _apply_payload_to_item(item: Dict[str, Any], payload: Dict[str, Any]) -> None:
    auto_fill_detail = payload.get("autoFillDetail") if isinstance(payload.get("autoFillDetail"), dict) else {}
    selected_candidate = auto_fill_detail.get("selected")
    if payload.get("price") is not None:
        item["price"] = payload.get("price")
    if payload.get("btPrice") is not None:
        item["btPrice"] = payload.get("btPrice")
    if payload.get("platformPrice") is not None:
        item["platformPrice"] = payload.get("platformPrice")
    if payload.get("arrivalTime") is not None:
        item["arrivalTime"] = payload.get("arrivalTime")
    if payload.get("brandId"):
        item["brandId"] = payload.get("brandId")
    if payload.get("brandName") and _should_update_brand_name(payload, selected_candidate):
        item["brandName"] = payload.get("brandName")
    if payload.get("selectionReason"):
        item["remark"] = payload.get("selectionReason")
    if payload.get("autoFillDetail") is not None:
        item["autoFillDetail"] = payload.get("autoFillDetail")
    if payload.get("selectionReason"):
        item["selectionReason"] = payload.get("selectionReason")
    merged_raw_payload = _to_object_map(item.get("rawPayload"))
    if payload.get("autoFillDetail") is not None:
        merged_raw_payload["autoFillDetail"] = payload.get("autoFillDetail")
    if payload.get("selectionReason"):
        merged_raw_payload["selectionReason"] = payload.get("selectionReason")
    # 补价阶段不修改 source，source 仅在详情同步阶段由后端原始数据决定。
    item["rawPayload"] = merged_raw_payload


def _pick_single_pending_item(items: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    writable_items = [item for item in items if not _is_auto_source(item)]
    if len(writable_items) == 1:
        return writable_items[0]

    pending_items = [item for item in writable_items if not _has_price_value(item)]
    if len(pending_items) == 1:
        return pending_items[0]

    return None


def _candidate_item_id(item: Dict[str, Any]) -> Optional[int]:
    return _to_int(
        item.get("onlineOrderItemId")
        or item.get("itemId")
        or item.get("id")
        or _to_object_map(item.get("rawPayload")).get("itemId")
        or _to_object_map(item.get("rawPayload")).get("id")
    )


def _item_field_text(item: Dict[str, Any], field_name: str) -> str:
    raw_payload = _to_object_map(item.get("rawPayload"))
    return _normalize_text(item.get(field_name) or raw_payload.get(field_name))


def _is_auto_source(item: Dict[str, Any]) -> bool:
    return _normalize_text(item.get("source") or _to_object_map(item.get("rawPayload")).get("source")).upper() == "AUTO"


def _has_price_value(item: Dict[str, Any]) -> bool:
    return item.get("price") not in (None, "", 0, 0.0) or item.get("btPrice") not in (None, "", 0, 0.0)


def _normalize_parts_num(value: Any) -> str:
    return str(value or "").replace(" ", "").strip()


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _should_update_brand_name(payload: Dict[str, Any], selected_candidate: Any) -> bool:
    candidate = selected_candidate if isinstance(selected_candidate, dict) else {}
    quality_origin_id = _normalize_text(
        payload.get("qualityOriginId")
        or candidate.get("qualityOriginId")
    ).upper()
    if quality_origin_id == "BRAND":
        return True
    quality_name = _normalize_text(
        payload.get("qualityName")
        or candidate.get("qualityName")
    )
    return quality_name in {"\u54c1\u724c", "\u54c1\u724c\u4ef6"}


def _to_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except Exception:
        return None


def _to_object_map(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    text = str(value or "").strip()
    if not text:
        return {}
    try:
        payload = json.loads(text)
    except Exception:
        return {}
    return dict(payload) if isinstance(payload, dict) else {}
