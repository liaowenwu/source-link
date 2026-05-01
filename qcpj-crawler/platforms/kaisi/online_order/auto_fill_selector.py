from __future__ import annotations

import hashlib
import re
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple

from .auto_fill_config import normalize_text, to_float, to_int
from .quality_support import is_brand_placeholder_quality_name, split_csv_values

QUALITY_NAME_MATCH_THRESHOLD = 0.88
BRAND_NAME_MATCH_THRESHOLD = 0.88


def build_auto_fill_payloads(
    sku: str,
    sku_records: List[Dict[str, Any]],
    online_order_item_ids: List[int],
    online_order_item_metas: List[Dict[str, Any]],
    match_strategy: Dict[str, Any],
) -> List[Dict[str, Any]]:
    item_metas = online_order_item_metas or [{"itemId": item_id} for item_id in online_order_item_ids]
    normalized_candidates = [normalize_candidate(record, match_strategy) for record in sku_records]
    normalized_candidates = [item for item in normalized_candidates if item]
    ordered_candidates = sort_candidates_for_display(normalized_candidates, match_strategy)
    ranked_candidates_by_index = [
        rank_candidates_for_item(ordered_candidates, match_strategy, meta)
        for meta in item_metas
    ]
    selected_candidates = assign_candidates_for_shared_quality_groups(item_metas, ranked_candidates_by_index)

    payloads: List[Dict[str, Any]] = []
    for index, meta in enumerate(item_metas):
        desired_quality = normalize_text(meta.get("qualityOriginId"))
        display_candidates = filter_candidates_by_quality(ordered_candidates, desired_quality, meta)
        selected = selected_candidates[index] if index < len(selected_candidates) else None
        selection_reason = build_selection_reason(selected, match_strategy)
        item_id = to_int(meta.get("itemId") or meta.get("id"))
        payloads.append(
            {
                "sku": sku,
                "scene": "online_order_auto_fill",
                "onlineOrderItemIds": [item_id] if item_id is not None else [],
                "onlineOrderItemId": item_id,
                "itemId": item_id,
                "quotationId": normalize_text(meta.get("quotationId")),
                "inquiryId": normalize_text(meta.get("inquiryId")),
                "storeId": normalize_text(meta.get("storeId")),
                "resolveResultId": normalize_text(meta.get("resolveResultId")),
                "quotedPriceItemId": normalize_text(meta.get("quotedPriceItemId")),
                "userNeedsItemId": normalize_text(meta.get("userNeedsItemId")),
                "partsNum": normalize_text(meta.get("partsNum")) or sku,
                "partsName": normalize_text(meta.get("partsName")),
                "brand": (selected.get("brandName") if selected else "") or normalize_text(meta.get("brandName")),
                "brandId": (selected.get("brandOriginId") if selected else "") or normalize_text(meta.get("brandId")),
                "brandName": (selected.get("brandName") if selected else "") or normalize_text(meta.get("brandName")),
                "region": selected.get("regionName") if selected else "",
                "regionName": selected.get("regionName") if selected else "",
                "regionOriginId": selected.get("regionOriginId") if selected else "",
                "companyName": selected.get("companyName") if selected else "",
                "supplierName": selected.get("supplierName") if selected else "",
                "supplierId": selected.get("supplierId") if selected else "",
                "stock": selected.get("stock") if selected else 0,
                "qualityCode": normalize_text(meta.get("qualityCode")),
                "qualityOriginId": (selected.get("qualityOriginId") if selected else "") or desired_quality,
                "qualityName": (selected.get("qualityName") if selected else "") or normalize_text(meta.get("qualityName")),
                "platformPrice": selected.get("platformPrice") if selected else None,
                "price": selected.get("price") if selected else None,
                "btPrice": selected.get("price") if selected else None,
                "arrivalTime": selected.get("transferDays") if selected else None,
                "message": "auto-fill matched" if selected else "auto-fill no candidate matched",
                "selectionReason": selection_reason,
                "autoFillDetail": {
                    "selected": serialize_candidate(selected) if selected else None,
                    "candidates": [serialize_candidate(item) for item in (display_candidates or ordered_candidates)[:8]],
                    "platformCandidates": build_platform_candidates(display_candidates or ordered_candidates),
                    "selectedPlatform": normalize_platform_name(selected.get("crawlPlatform") if selected else ""),
                    "selectionReason": selection_reason,
                },
            }
        )
    return payloads


def normalize_candidate(record: Dict[str, Any], match_strategy: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    price = to_float(record.get("price"))
    if price is None:
        return None
    brand_origin_id = normalize_text(record.get("brandOriginId"))
    brand_name = normalize_text(record.get("brandName") or record.get("brand"))
    region_origin_id = normalize_text(record.get("regionOriginId"))
    region_name = normalize_text(record.get("regionName") or record.get("region"))
    quality_origin_id = normalize_text(record.get("qualityOriginId"))
    quality_name = normalize_text(record.get("qualityName"))
    crawl_platform = normalize_platform_name(record.get("crawlPlatform") or record.get("platformCode") or record.get("source"))
    return {
        "sku": normalize_text(record.get("sku")),
        "crawlPlatform": crawl_platform,
        "productName": normalize_text(record.get("productName")),
        "brandName": brand_name,
        "brandOriginId": brand_origin_id,
        "regionName": region_name,
        "regionOriginId": region_origin_id,
        "qualityName": quality_name,
        "qualityOriginId": quality_origin_id,
        "companyName": normalize_text(record.get("companyName")),
        "supplierName": normalize_text(record.get("supplierName")),
        "supplierId": normalize_text(record.get("supplierId")),
        "stock": to_int(record.get("stock")) or 0,
        "price": round(price, 2),
        "platformPrice": to_float(record.get("platformPrice")) or round(price, 2),
        "markupRate": to_float(record.get("markupRate")),
        "transferDays": (
            to_int(record.get("transferDays"))
            if to_int(record.get("transferDays")) is not None
            else resolve_transfer_days(region_origin_id, region_name, match_strategy)
        ),
        "rawPayload": record.get("rawPayload"),
    }


def filter_candidates_by_quality(
    candidates: List[Dict[str, Any]],
    desired_quality: str,
    item_meta: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    preferred_candidates, _ = resolve_preferred_candidates(candidates, desired_quality, item_meta)
    return preferred_candidates or candidates


def sort_candidates_for_display(candidates: List[Dict[str, Any]], match_strategy: Dict[str, Any]) -> List[Dict[str, Any]]:
    return sorted(
        candidates,
        key=lambda item: (
            brand_priority_score(item, match_strategy),
            region_priority_score(item, match_strategy),
            item.get("price") if item.get("price") is not None else float("inf"),
            item.get("transferDays") if item.get("transferDays") is not None else float("inf"),
        ),
    )


def select_candidate(
    candidates: List[Dict[str, Any]],
    match_strategy: Dict[str, Any],
    item_meta: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    ranked_candidates = rank_candidates_for_item(candidates, match_strategy, item_meta)
    return ranked_candidates[0] if ranked_candidates else None


def rank_candidates_for_item(
    candidates: List[Dict[str, Any]],
    match_strategy: Dict[str, Any],
    item_meta: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    pool, match_mode = resolve_candidate_pool(candidates, item_meta)
    if not pool:
        return []

    ranked_candidates: List[Dict[str, Any]] = []
    remaining = [dict(candidate) for candidate in pool]
    while remaining:
        if match_mode == "brand-fallback-random":
            selected = select_stable_fallback_candidate(remaining, item_meta)
        else:
            selected = _select_best_candidate(remaining, match_strategy)
        if not selected:
            break
        ranked_candidates.append(clone_selected_candidate(selected, match_mode))
        selected_key = candidate_identity(selected)
        remaining = [candidate for candidate in remaining if candidate_identity(candidate) != selected_key]
    return ranked_candidates


def assign_candidates_for_shared_quality_groups(
    item_metas: List[Dict[str, Any]],
    ranked_candidates_by_index: List[List[Dict[str, Any]]],
) -> List[Optional[Dict[str, Any]]]:
    selected_candidates: List[Optional[Dict[str, Any]]] = [
        ranked_candidates[0] if ranked_candidates else None
        for ranked_candidates in ranked_candidates_by_index
    ]

    for group_indices in build_shared_quality_groups(item_metas):
        used_candidate_keys = set()
        for index in group_indices:
            ranked_candidates = ranked_candidates_by_index[index] if index < len(ranked_candidates_by_index) else []
            if not ranked_candidates:
                selected_candidates[index] = None
                continue

            selected = next(
                (
                    candidate
                    for candidate in ranked_candidates
                    if candidate_identity(candidate) not in used_candidate_keys
                ),
                ranked_candidates[0],
            )
            selected_candidates[index] = mark_allocation_mode(selected, "shared-quality-distinct")
            used_candidate_keys.add(candidate_identity(selected))

    return selected_candidates


def _select_best_candidate(candidates: List[Dict[str, Any]], match_strategy: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not candidates:
        return None

    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for candidate in candidates:
        brand_key = candidate.get("brandOriginId") or (candidate.get("brandName") or "").lower() or "__UNKNOWN__"
        grouped.setdefault(brand_key, []).append(candidate)

    ordered_groups = sorted(
        grouped.values(),
        key=lambda items: (
            min(brand_priority_score(item, match_strategy) for item in items),
            min(item.get("price") if item.get("price") is not None else float("inf") for item in items),
        ),
    )
    for group in ordered_groups:
        selected = select_region_candidate(group, match_strategy)
        if selected:
            return selected
    return None


def select_region_candidate(candidates: List[Dict[str, Any]], match_strategy: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not candidates:
        return None
    ordered = sort_candidates_for_display(candidates, match_strategy)
    baseline = ordered[0]
    threshold_ratio = float(match_strategy.get("priceAdvantageRate") or 0) / 100.0
    if threshold_ratio <= 0:
        return baseline

    baseline_price = baseline.get("price")
    if baseline_price is None:
        return baseline

    override_candidates = []
    for candidate in ordered[1:]:
        price = candidate.get("price")
        if price is None:
            continue
        if price <= baseline_price * (1 - threshold_ratio):
            override_candidates.append(candidate)

    if not override_candidates:
        return baseline

    return sorted(
        override_candidates,
        key=lambda item: (
            item.get("price") if item.get("price") is not None else float("inf"),
            item.get("transferDays") if item.get("transferDays") is not None else float("inf"),
            region_priority_score(item, match_strategy),
        ),
    )[0]


def build_selection_reason(selected: Optional[Dict[str, Any]], match_strategy: Dict[str, Any]) -> str:
    if not selected:
        return "no usable candidate"
    brand_rank = brand_priority_score(selected, match_strategy) + 1
    region_rank = region_priority_score(selected, match_strategy) + 1
    match_mode = normalize_text(selected.get("_matchMode"))
    allocation_mode = normalize_text(selected.get("_allocationMode"))
    parts = []
    if match_mode:
        parts.append(f"matchMode={match_mode}")
    if allocation_mode:
        parts.append(f"allocationMode={allocation_mode}")
    parts.append(f"brandPriority#{brand_rank}")
    parts.append(f"regionPriority#{region_rank}")
    parts.append(f"priceAdvantageRate={match_strategy.get('priceAdvantageRate') or 0}%")
    return ", ".join(parts)


def serialize_candidate(candidate: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not candidate:
        return None
    return {
        "crawlPlatform": normalize_platform_name(candidate.get("crawlPlatform")),
        "brandName": candidate.get("brandName"),
        "brandOriginId": candidate.get("brandOriginId"),
        "qualityName": candidate.get("qualityName"),
        "qualityOriginId": candidate.get("qualityOriginId"),
        "regionName": candidate.get("regionName"),
        "regionOriginId": candidate.get("regionOriginId"),
        "companyName": candidate.get("companyName"),
        "supplierName": candidate.get("supplierName"),
        "supplierId": candidate.get("supplierId"),
        "platformPrice": candidate.get("platformPrice"),
        "markupRate": candidate.get("markupRate"),
        "price": candidate.get("price"),
        "stock": candidate.get("stock"),
        "transferDays": candidate.get("transferDays"),
    }


def normalize_platform_name(value: Any) -> str:
    text = normalize_text(value).upper()
    if text in {"BENBEN", "犇犇", "犇犇平台"}:
        return "BENBEN"
    if text in {"ROBOT", "JIQIREN", "机器人", "机器人平台"}:
        return "JIQIREN"
    return text or "UNKNOWN"


def build_platform_candidates(candidates: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for candidate in candidates[:20]:
        platform = normalize_platform_name(candidate.get("crawlPlatform"))
        grouped.setdefault(platform, []).append(serialize_candidate(candidate) or {})
    return grouped


def brand_priority_score(candidate: Dict[str, Any], match_strategy: Dict[str, Any]) -> int:
    origin_id = candidate.get("brandOriginId")
    if origin_id and origin_id in match_strategy["brandIndexByOrigin"]:
        return match_strategy["brandIndexByOrigin"][origin_id]
    brand_name = candidate.get("brandName")
    if brand_name and brand_name.lower() in match_strategy["brandIndexByName"]:
        return match_strategy["brandIndexByName"][brand_name.lower()]
    return len(match_strategy["brandPriority"]) + 1000 if match_strategy["brandPriority"] else 0


def region_priority_score(candidate: Dict[str, Any], match_strategy: Dict[str, Any]) -> int:
    origin_id = candidate.get("regionOriginId")
    if origin_id and origin_id in match_strategy["regionIndexByOrigin"]:
        return match_strategy["regionIndexByOrigin"][origin_id]
    region_name = candidate.get("regionName")
    if region_name and region_name.lower() in match_strategy["regionIndexByName"]:
        return match_strategy["regionIndexByName"][region_name.lower()]
    return len(match_strategy["regionPriority"]) + 1000 if match_strategy["regionPriority"] else 0


def resolve_transfer_days(region_origin_id: str, region_name: str, match_strategy: Dict[str, Any]) -> int:
    if region_origin_id and region_origin_id in match_strategy["regionExtraDaysByOrigin"]:
        return match_strategy["regionExtraDaysByOrigin"][region_origin_id]
    if region_name and region_name.lower() in match_strategy["regionExtraDaysByName"]:
        return match_strategy["regionExtraDaysByName"][region_name.lower()]
    return 0


def resolve_preferred_candidates(
    candidates: List[Dict[str, Any]],
    desired_quality: str,
    item_meta: Optional[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], str]:
    if not candidates:
        return [], ""

    quality_origin_ids = split_csv_values(desired_quality)
    if quality_origin_ids:
        exact_quality_candidates = [
            candidate
            for candidate in candidates
            if set(split_csv_values(candidate.get("qualityOriginId"))).intersection(quality_origin_ids)
        ]
        if exact_quality_candidates:
            return exact_quality_candidates, "quality-origin"

    desired_quality_name = normalize_text(item_meta.get("qualityName")) if isinstance(item_meta, dict) else ""
    if desired_quality_name and not is_brand_placeholder_quality_name(desired_quality_name):
        quality_name_candidates = [
            candidate
            for candidate in candidates
            if match_name_score(desired_quality_name, candidate.get("brandName")) >= QUALITY_NAME_MATCH_THRESHOLD
            or match_name_score(desired_quality_name, candidate.get("qualityName")) >= QUALITY_NAME_MATCH_THRESHOLD
        ]
        if quality_name_candidates:
            return quality_name_candidates, "quality-name"

    desired_brand_name = normalize_text(item_meta.get("brandName")) if isinstance(item_meta, dict) else ""
    if should_match_brand_by_name(item_meta) and desired_brand_name:
        brand_name_candidates = [
            candidate
            for candidate in candidates
            if match_name_score(desired_brand_name, candidate.get("brandName")) >= BRAND_NAME_MATCH_THRESHOLD
        ]
        if brand_name_candidates:
            return brand_name_candidates, "brand-fuzzy"

    return [], ""


def resolve_candidate_pool(
    candidates: List[Dict[str, Any]],
    item_meta: Optional[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], str]:
    if not candidates:
        return [], ""

    desired_quality = normalize_text(item_meta.get("qualityOriginId")) if isinstance(item_meta, dict) else ""
    preferred_candidates, match_mode = resolve_preferred_candidates(candidates, desired_quality, item_meta)
    if preferred_candidates:
        return preferred_candidates, match_mode

    if should_use_brand_fallback(item_meta):
        return candidates, "brand-fallback-random"

    return candidates, "best-effort"


def should_match_brand_by_name(item_meta: Optional[Dict[str, Any]]) -> bool:
    if not isinstance(item_meta, dict):
        return False
    quality_name = normalize_text(item_meta.get("qualityName"))
    if not quality_name:
        return True
    return is_brand_placeholder_quality_name(quality_name)


def should_use_brand_fallback(item_meta: Optional[Dict[str, Any]]) -> bool:
    if not should_match_brand_by_name(item_meta):
        return False
    return bool(normalize_text((item_meta or {}).get("brandName")))


def select_stable_fallback_candidate(
    candidates: List[Dict[str, Any]],
    item_meta: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    if not candidates:
        return None
    identity = "||".join(
        [
            normalize_text((item_meta or {}).get("itemId") or (item_meta or {}).get("id")),
            normalize_text((item_meta or {}).get("resolveResultId")),
            normalize_text((item_meta or {}).get("quotationId")),
            normalize_text((item_meta or {}).get("partsNum")),
            normalize_text((item_meta or {}).get("qualityCode")),
            normalize_text((item_meta or {}).get("brandName")),
        ]
    )
    digest = hashlib.md5(identity.encode("utf-8")).hexdigest()
    index = int(digest[:8], 16) % len(candidates)
    return candidates[index]


def clone_selected_candidate(candidate: Optional[Dict[str, Any]], match_mode: str) -> Optional[Dict[str, Any]]:
    if not candidate:
        return None
    cloned = dict(candidate)
    cloned["_matchMode"] = normalize_text(match_mode)
    return cloned


def mark_allocation_mode(candidate: Optional[Dict[str, Any]], allocation_mode: str) -> Optional[Dict[str, Any]]:
    if not candidate:
        return None
    cloned = dict(candidate)
    cloned["_allocationMode"] = normalize_text(allocation_mode)
    return cloned


def build_shared_quality_groups(item_metas: List[Dict[str, Any]]) -> List[List[int]]:
    grouped: Dict[str, Dict[str, Any]] = {}
    for index, meta in enumerate(item_metas or []):
        if not isinstance(meta, dict):
            continue
        quality_name = normalize_text(meta.get("qualityName")).lower()
        if not quality_name:
            continue
        quality_identity = normalize_text(meta.get("qualityOriginId") or meta.get("qualityCode"))
        bucket = grouped.setdefault(
            quality_name,
            {
                "indices": [],
                "qualityIds": set(),
            },
        )
        bucket["indices"].append(index)
        if quality_identity:
            bucket["qualityIds"].add(quality_identity)

    result: List[List[int]] = []
    for bucket in grouped.values():
        indices = list(bucket.get("indices") or [])
        quality_ids = set(bucket.get("qualityIds") or set())
        if len(indices) > 1 and len(quality_ids) > 1:
            result.append(indices)
    return result


def candidate_identity(candidate: Optional[Dict[str, Any]]) -> str:
    if not candidate:
        return ""
    return "||".join(
        [
            normalize_text(candidate.get("brandOriginId") or candidate.get("brandName")),
            normalize_text(candidate.get("qualityOriginId") or candidate.get("qualityName")),
            normalize_text(candidate.get("regionOriginId") or candidate.get("regionName")),
            normalize_text(candidate.get("supplierId") or candidate.get("supplierName")),
            normalize_text(candidate.get("companyName")),
            normalize_text(candidate.get("price")),
            normalize_text(candidate.get("transferDays")),
        ]
    )


def match_name_score(left: Any, right: Any) -> float:
    left_aliases = normalize_name_aliases(left)
    right_aliases = normalize_name_aliases(right)
    if not left_aliases or not right_aliases:
        return 0.0

    best_score = 0.0
    for left_alias in left_aliases:
        for right_alias in right_aliases:
            if left_alias == right_alias:
                return 1.0
            if left_alias in right_alias or right_alias in left_alias:
                best_score = max(best_score, 0.95)
                continue
            best_score = max(best_score, SequenceMatcher(None, left_alias, right_alias).ratio())
    return best_score


def normalize_name_aliases(value: Any) -> List[str]:
    text = normalize_text(value).lower()
    if not text:
        return []

    unified = text.replace("（", "(").replace("）", ")")
    aliases = set()
    normalized_text = normalize_name_token(unified)
    if normalized_text:
        aliases.add(normalized_text)

    for part in re.split(r"[()\\/,\s，、-]+", unified):
        normalized_part = normalize_name_token(part)
        if normalized_part:
            aliases.add(normalized_part)

    return sorted(aliases)


def normalize_name_token(value: str) -> str:
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", str(value or "").lower())
