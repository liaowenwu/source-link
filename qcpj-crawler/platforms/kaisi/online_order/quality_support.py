from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List

from .auto_fill_config import normalize_text

DEFAULT_EMPTY_QUALITY_CODE = "OTHER"
DEFAULT_EMPTY_QUALITY_NAME = "其他"

BRAND_PLACEHOLDER_QUALITY_NAMES = {"品牌"}


def split_csv_values(value: Any) -> List[str]:
    values = value if isinstance(value, list) else str(value or "").split(",")
    result: List[str] = []
    seen = set()
    for raw in values:
        text = normalize_text(raw)
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def build_quality_maps(rows: Iterable[Dict[str, Any]]) -> Dict[str, Dict[str, Dict[str, str]]]:
    by_code: Dict[str, Dict[str, str]] = {}
    by_name: Dict[str, Dict[str, str]] = {}
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        quality_code = normalize_text(row.get("qualityCode") or row.get("quality_code"))
        quality_name = normalize_text(row.get("qualityName") or row.get("quality_name"))
        quality_origin_id = normalize_text(row.get("qualityOriginId") or row.get("quality_origin_id")) or quality_code
        payload = {
            "qualityCode": quality_code,
            "qualityName": quality_name,
            "qualityOriginId": quality_origin_id,
        }
        if quality_code:
            by_code[quality_code] = payload
        if quality_name and quality_name not in by_name:
            by_name[quality_name] = payload
    return {"by_code": by_code, "by_name": by_name}


def resolve_item_quality(
    item: Dict[str, Any],
    quality_maps: Dict[str, Dict[str, Dict[str, str]]],
) -> Dict[str, Any]:
    result = dict(item or {})
    raw_payload = _to_object_map(result.get("rawPayload"))

    quality_code = normalize_text(
        result.get("qualityCode")
        or result.get("quality_code")
        or raw_payload.get("qualityCode")
        or raw_payload.get("quality_code")
        or result.get("partsBrandQuality")
        or result.get("parts_brand_quality")
        or raw_payload.get("partsBrandQuality")
        or raw_payload.get("parts_brand_quality")
    )
    quality_name = normalize_text(
        result.get("qualityName")
        or result.get("quality_name")
        or result.get("partsBrandQualityName")
        or result.get("parts_brand_quality_name")
        or raw_payload.get("qualityName")
        or raw_payload.get("quality_name")
        or raw_payload.get("partsBrandQualityName")
        or raw_payload.get("parts_brand_quality_name")
    )
    quality_origin_id = normalize_text(
        result.get("qualityOriginId")
        or result.get("quality_origin_id")
        or raw_payload.get("qualityOriginId")
        or raw_payload.get("quality_origin_id")
    )

    by_code = quality_maps.get("by_code") or {}
    by_name = quality_maps.get("by_name") or {}

    if quality_code and quality_code in by_code:
        matched = by_code[quality_code]
        quality_name = quality_name or matched.get("qualityName", "")
        quality_origin_id = quality_origin_id or matched.get("qualityOriginId", "")

    if not quality_origin_id and quality_name and quality_name in by_name:
        matched = by_name[quality_name]
        quality_code = quality_code or matched.get("qualityCode", "")
        quality_origin_id = quality_origin_id or matched.get("qualityOriginId", "")

    if not quality_code and not quality_name and not quality_origin_id:
        default_quality = _resolve_default_empty_quality(quality_maps)
        quality_code = default_quality["qualityCode"]
        quality_name = default_quality["qualityName"]
        quality_origin_id = default_quality["qualityOriginId"]

    result["qualityCode"] = quality_code
    result["qualityName"] = quality_name or normalize_text(result.get("partsBrandQuality")) or quality_code
    result["qualityOriginId"] = quality_origin_id or quality_code
    return result


def collect_quality_origin_ids(items: Iterable[Dict[str, Any]]) -> List[str]:
    result: List[str] = []
    seen = set()
    for item in items or []:
        if not isinstance(item, dict):
            continue
        for quality_origin_id in split_csv_values(item.get("qualityOriginId")):
            if quality_origin_id in seen:
                continue
            seen.add(quality_origin_id)
            result.append(quality_origin_id)
    return result


def is_brand_placeholder_quality_name(value: Any) -> bool:
    return normalize_text(value) in BRAND_PLACEHOLDER_QUALITY_NAMES


def _resolve_default_empty_quality(
    quality_maps: Dict[str, Dict[str, Dict[str, str]]],
) -> Dict[str, str]:
    by_name = quality_maps.get("by_name") or {}
    by_code = quality_maps.get("by_code") or {}
    matched = by_name.get(DEFAULT_EMPTY_QUALITY_NAME) or by_code.get(DEFAULT_EMPTY_QUALITY_CODE) or {}
    quality_code = normalize_text(matched.get("qualityCode")) or DEFAULT_EMPTY_QUALITY_CODE
    quality_name = normalize_text(matched.get("qualityName")) or DEFAULT_EMPTY_QUALITY_NAME
    quality_origin_id = normalize_text(matched.get("qualityOriginId")) or quality_code
    return {
        "qualityCode": quality_code,
        "qualityName": quality_name,
        "qualityOriginId": quality_origin_id,
    }


def _to_object_map(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    text = normalize_text(value)
    if not text:
        return {}
    try:
        payload = json.loads(text)
    except Exception:
        return {}
    return dict(payload) if isinstance(payload, dict) else {}
