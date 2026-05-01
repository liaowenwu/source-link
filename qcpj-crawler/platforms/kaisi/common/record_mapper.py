from typing import Any, Dict

# 处理int。
def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default

# 处理intornone。
def _to_int_or_none(value: Any) -> Any:
    try:
        if value is None or value == "":
            return None
        return int(float(value))
    except Exception:
        return None

# 处理结果row。
def to_result_row(record: Dict[str, Any], supplier_name: str = "kaisi") -> Dict[str, Any]:
    quantity = _to_int(record.get("quantity"), 0)
    row = {
        "partsNum": str(record.get("partsNum") or ""),
        "partsName": str(record.get("partsName") or ""),
        "brandId": str(record.get("brandId") or ""),
        "brandName": str(record.get("brandName") or ""),
        "source": str(record.get("source") or ""),
        "partsBrandQuality": str(record.get("partsBrandQuality") or ""),
        "quantity": quantity,
        "price": record.get("price"),
        "btPrice": record.get("btPrice"),
        "productType": str(record.get("productType") or ""),
        "partType": str(record.get("partType") or ""),
        "recordType": str(record.get("recordType") or ""),
        "statusIdDesc": str(record.get("statusIdDesc") or ""),
        "resolveResultId": str(record.get("resolveResultId") or ""),
        "resolveStatus": str(record.get("resolveStatus") or ""),
        "quotationId": str(record.get("quotationId") or ""),
        "createdStamp": _to_int_or_none(record.get("createdStamp")),
        "quotationCreatedStamp": _to_int_or_none(record.get("quotationCreatedStamp")),
        "inquiryId": str(record.get("inquiryId") or ""),
        "storeId": str(record.get("storeId") or ""),
    }
    row["sku"] = row["partsNum"]
    row["productName"] = row["partsName"]
    row["brand"] = row["brandName"] or row["brandId"]
    row["supplierName"] = supplier_name
    row["stock"] = 0 if row["recordType"] == "OUT_OF_STOCK" else max(quantity, 1)
    row["region"] = ""
    row["companyName"] = ""
    return row

# 构建realtime载荷。
def build_realtime_payload(record: Dict[str, Any], task_id: str, platform: str, message: str) -> Dict[str, Any]:
    return {
        **to_result_row(record),
        "platform": platform,
        "taskId": task_id,
        "message": message,
    }

