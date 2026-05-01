from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Set

CRAWL_STRATEGY_FULL_SELECTED = "FULL_SELECTED"
CRAWL_STRATEGY_PRIORITY_STOP_ON_HIT = "PRIORITY_STOP_ON_HIT"

PLATFORM_CODE_MAPPING = {
    "BENBEN": "benben",
    "BEN_BEN": "benben",
    "BEN-BEN": "benben",
    "BENBENPLATFORM": "benben",
    "犇犇": "benben",
    "犇犇平台": "benben",
    "ROBOT": "robot",
    "ROBOTPLATFORM": "robot",
    "JIQIREN": "robot",
    "机器人": "robot",
    "机器人平台": "robot",
}

SUPPORTED_CRAWL_PLATFORMS = {"benben", "robot"}
PLATFORM_ID_MAPPING = {
    "1": "benben",
    "2": "robot",
}


def normalize_text(value: Any) -> str:
    return str(value or "").strip()


def normalize_parts_num(value: Any) -> str:
    return normalize_text(value).replace(" ", "")


def normalize_text_list(values: Any) -> List[str]:
    if not isinstance(values, list):
        return []
    result: List[str] = []
    seen: Set[str] = set()
    for value in values:
        text = normalize_text(value)
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def normalize_supplier_configs(values: Any) -> List[Dict[str, Any]]:
    if not isinstance(values, list):
        return []
    rows: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    for item in values:
        if not isinstance(item, dict):
            continue
        supplier_origin_id = normalize_text(item.get("supplierOriginId"))
        brand_origin_id = normalize_text(item.get("brandOriginId"))
        seen_key = f"{brand_origin_id}|{supplier_origin_id}"
        if not supplier_origin_id or seen_key in seen:
            continue
        seen.add(seen_key)
        rows.append(
            {
                "brandOriginId": brand_origin_id,
                "brandName": normalize_text(item.get("brandName")),
                "supplierOriginId": supplier_origin_id,
                "supplierName": normalize_text(item.get("supplierName")),
                "markupRate": to_float(item.get("markupRate")),
                "transferDays": to_int(item.get("transferDays")),
            }
        )
    return rows


def build_crawler_query_param_map(rows: Any) -> Dict[str, Dict[str, Any]]:
    if not isinstance(rows, list):
        return {}
    result: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        parts_num = normalize_parts_num(row.get("partsNum"))
        if not parts_num:
            continue
        quality_origin_ids = normalize_text_list(row.get("qualityOriginIds"))
        quality_codes = normalize_text_list(row.get("qualityCodes"))
        brand_origin_ids = normalize_text_list(row.get("brandOriginIds"))
        region_origin_ids = normalize_text_list(row.get("regionOriginIds"))
        supplier_configs = normalize_supplier_configs(row.get("supplierConfigs"))
        crawl_strategy_type = normalize_crawl_strategy_type(row.get("crawlStrategyType"))
        crawl_strategy_selected_platform_codes = normalize_text_list(row.get("crawlStrategySelectedPlatformCodes"))
        crawl_strategy_priority_platform_codes = normalize_text_list(row.get("crawlStrategyPriorityPlatformCodes"))
        crawl_strategy_stop_on_hit = to_bool(row.get("crawlStrategyStopOnHit"))
        row_platform = resolve_row_platform(row)
        platform_query_params = {
            "qualityCodes": quality_codes,
            "qualityOriginIds": quality_origin_ids,
            "brandOriginIds": brand_origin_ids,
            "regionOriginIds": region_origin_ids,
            "supplierConfigs": supplier_configs,
        }

        existing = result.get(parts_num)
        if not existing:
            result[parts_num] = {
                "partsNum": parts_num,
                "qualityCodes": quality_codes,
                "qualityOriginIds": quality_origin_ids,
                "brandOriginIds": brand_origin_ids,
                "regionOriginIds": region_origin_ids,
                "supplierConfigs": supplier_configs,
                "crawlStrategyType": crawl_strategy_type,
                "crawlStrategySelectedPlatformCodes": crawl_strategy_selected_platform_codes,
                "crawlStrategyPriorityPlatformCodes": crawl_strategy_priority_platform_codes,
                "crawlStrategyStopOnHit": crawl_strategy_stop_on_hit,
                "platformQueryParams": (
                    {row_platform: platform_query_params} if row_platform in SUPPORTED_CRAWL_PLATFORMS else {}
                ),
            }
            continue

        existing["qualityCodes"] = merge_text_lists(existing.get("qualityCodes"), quality_codes)
        existing["qualityOriginIds"] = merge_text_lists(existing.get("qualityOriginIds"), quality_origin_ids)
        existing["brandOriginIds"] = merge_text_lists(existing.get("brandOriginIds"), brand_origin_ids)
        existing["regionOriginIds"] = merge_text_lists(existing.get("regionOriginIds"), region_origin_ids)
        existing["supplierConfigs"] = merge_supplier_configs(
            existing.get("supplierConfigs"), supplier_configs
        )
        existing["crawlStrategyType"] = normalize_crawl_strategy_type(
            existing.get("crawlStrategyType") or crawl_strategy_type
        )
        existing["crawlStrategySelectedPlatformCodes"] = merge_text_lists(
            existing.get("crawlStrategySelectedPlatformCodes"),
            crawl_strategy_selected_platform_codes,
        )
        existing["crawlStrategyPriorityPlatformCodes"] = merge_text_lists(
            existing.get("crawlStrategyPriorityPlatformCodes"),
            crawl_strategy_priority_platform_codes,
        )
        existing["crawlStrategyStopOnHit"] = bool(
            existing.get("crawlStrategyStopOnHit") or crawl_strategy_stop_on_hit
        )
        if row_platform in SUPPORTED_CRAWL_PLATFORMS:
            existing_platform_map = existing.get("platformQueryParams")
            if not isinstance(existing_platform_map, dict):
                existing_platform_map = {}
            current_platform_params = existing_platform_map.get(row_platform) or {}
            existing_platform_map[row_platform] = {
                "qualityCodes": merge_text_lists(current_platform_params.get("qualityCodes"), quality_codes),
                "qualityOriginIds": merge_text_lists(current_platform_params.get("qualityOriginIds"), quality_origin_ids),
                "brandOriginIds": merge_text_lists(current_platform_params.get("brandOriginIds"), brand_origin_ids),
                "regionOriginIds": merge_text_lists(current_platform_params.get("regionOriginIds"), region_origin_ids),
                "supplierConfigs": merge_supplier_configs(current_platform_params.get("supplierConfigs"), supplier_configs),
            }
            existing["platformQueryParams"] = existing_platform_map
    return result


def normalize_platform_name(value: Any) -> str:
    text = normalize_text(value).upper()
    if text in PLATFORM_ID_MAPPING:
        return PLATFORM_ID_MAPPING.get(text) or ""
    canonical_key = text.replace(" ", "").replace("_", "").replace("-", "")
    mapped = PLATFORM_CODE_MAPPING.get(text) or PLATFORM_CODE_MAPPING.get(canonical_key)
    if mapped in SUPPORTED_CRAWL_PLATFORMS:
        return mapped
    if text.lower() in SUPPORTED_CRAWL_PLATFORMS:
        return text.lower()
    return ""


def resolve_row_platform(row: Dict[str, Any]) -> str:
    if not isinstance(row, dict):
        return ""
    for key in (
        "platformId",
        "platform_id",
        "plantformId",
        "plantform_id",
        "platformCode",
        "platform_code",
        "platformName",
        "platform_name",
        "crawlerPlatform",
        "crawler_platform",
    ):
        platform = normalize_platform_name(row.get(key))
        if platform:
            return platform
    return ""


def get_platform_query_params(sku_query_params: Dict[str, Any], platform_name: str) -> Dict[str, Any]:
    if not isinstance(sku_query_params, dict):
        return {}
    platform = normalize_platform_name(platform_name)
    platform_map = sku_query_params.get("platformQueryParams")
    if isinstance(platform_map, dict):
        scoped = platform_map.get(platform)
        if isinstance(scoped, dict):
            return scoped
    return {}


def resolve_crawl_platform_plan(
    sku_query_params: Dict[str, Any],
    benben_config: Dict[str, Any],
) -> Dict[str, Any]:
    # 保证 sku 级策略对象一定是 dict，避免 None 或其他类型导致后续取值报错。
    query_params = sku_query_params if isinstance(sku_query_params, dict) else {}
    # 保证全局配置对象一定是 dict，避免 None 或其他类型导致后续取值报错。
    config = benben_config if isinstance(benben_config, dict) else {}

    # 先取 sku 级策略类型，sku 未配置时回退到全局策略类型。
    strategy_type = normalize_crawl_strategy_type(
        query_params.get("crawlStrategyType") or config.get("crawlStrategyType")
    )
    # 先取 sku 级“全量平台勾选”，sku 未配置时回退到全局“全量平台勾选”。
    selected_codes = normalize_text_list(
        query_params.get("crawlStrategySelectedPlatformCodes")
        or config.get("crawlStrategySelectedPlatformCodes")
    )
    # 先取 sku 级“优先顺序”，sku 未配置时回退到全局“优先顺序”。
    priority_codes = normalize_text_list(
        query_params.get("crawlStrategyPriorityPlatformCodes")
        or config.get("crawlStrategyPriorityPlatformCodes")
    )
    # 如果全量平台一个都没配，则兜底为 BENBEN，保证至少有一个可执行平台。
    if not selected_codes:
        selected_codes = ["BENBEN"]
    # 如果优先顺序没配，则回退到全量平台顺序。
    if not priority_codes:
        priority_codes = selected_codes

    # 把全量平台编码标准化成内部平台名（benben/robot）。
    selected_platforms = _normalize_platform_codes_to_supported(selected_codes)
    # 把优先顺序编码标准化成内部平台名（benben/robot）。
    priority_platforms = _normalize_platform_codes_to_supported(priority_codes)

    # 如果是“优先命中即停”策略，则严格按优先顺序执行，并强制 stop_on_hit = True。
    if strategy_type == CRAWL_STRATEGY_PRIORITY_STOP_ON_HIT:
        # 优先用优先顺序；如果优先顺序为空则退到全量平台；再退不到则兜底 benben。
        sequence = priority_platforms or selected_platforms or ["benben"]
        # 优先策略固定命中即停。
        stop_on_hit = True
    else:
        # 全量策略按勾选平台执行；如果为空则兜底 benben。
        sequence = selected_platforms or ["benben"]
        # 全量策略允许显式传 stopOnHit，但默认按 false 处理。
        stop_on_hit = bool(
            query_params.get("crawlStrategyStopOnHit")
            if "crawlStrategyStopOnHit" in query_params
            else config.get("crawlStrategyStopOnHit")
        )

    # 再做一次白名单过滤，只保留当前代码支持的平台。
    sequence = [item for item in sequence if item in SUPPORTED_CRAWL_PLATFORMS]
    # 如果过滤后为空，最终兜底 benben，避免执行链路空跑。
    if not sequence:
        sequence = ["benben"]

    # 返回统一结构，供 runtime 与 direct 两条补价链路复用。
    return {
        "strategyType": strategy_type,
        "platformSequence": sequence,
        "stopOnHit": bool(stop_on_hit),
    }


def _normalize_platform_codes_to_supported(codes: List[str]) -> List[str]:
    # 结果列表用于保留原始顺序（去重后）。
    result: List[str] = []
    # 集合用于快速去重，避免同一平台重复抓取。
    seen: Set[str] = set()
    # 先把输入列表做文本归一化与去空。
    for code in normalize_text_list(codes):
        # 做一次“强归一化”键：去空格、去下划线、去中划线，再转大写，兼容更多平台编码写法。
        canonical_key = normalize_text(code).replace(" ", "").replace("_", "").replace("-", "").upper()
        # 先按完整大写键匹配（例如 BEN_BEN、ROBOT）。
        platform = PLATFORM_CODE_MAPPING.get(normalize_text(code).upper())
        # 完整键未命中时按强归一化键再匹配（例如 BENBENPLATFORM、机器人平台）。
        if not platform:
            platform = PLATFORM_CODE_MAPPING.get(canonical_key)
        # 若仍未命中，则兼容直接传内部平台名（benben / robot）。
        if not platform and code.lower() in SUPPORTED_CRAWL_PLATFORMS:
            platform = code.lower()
        # 未识别或不在支持名单内则跳过。
        if not platform or platform not in SUPPORTED_CRAWL_PLATFORMS:
            continue
        # 已加入过则跳过，防止重复执行。
        if platform in seen:
            continue
        # 记录已出现平台。
        seen.add(platform)
        # 按输入顺序写入结果。
        result.append(platform)
    # 返回标准化后的平台序列。
    return result


def merge_text_lists(left: Any, right: Any) -> List[str]:
    merged: List[str] = []
    seen: Set[str] = set()
    for value in normalize_text_list(left) + normalize_text_list(right):
        if not value or value in seen:
            continue
        seen.add(value)
        merged.append(value)
    return merged


def merge_supplier_configs(left: Any, right: Any) -> List[Dict[str, Any]]:
    merged: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    for row in normalize_supplier_configs(left) + normalize_supplier_configs(right):
        supplier_origin_id = normalize_text(row.get("supplierOriginId"))
        brand_origin_id = normalize_text(row.get("brandOriginId"))
        seen_key = f"{brand_origin_id}|{supplier_origin_id}"
        if not supplier_origin_id or seen_key in seen:
            continue
        seen.add(seen_key)
        merged.append(row)
    return merged


def resolve_quality_origin_ids(sku_items: List[Dict[str, Any]], sku_query_params: Dict[str, Any], benben_config: Dict[str, Any]) -> List[str]:
    quality_origin_ids = normalize_text_list((sku_query_params or {}).get("qualityOriginIds"))
    if quality_origin_ids:
        return quality_origin_ids

    for item in sku_items or []:
        quality_origin_id = normalize_text(item.get("qualityOriginId"))
        if quality_origin_id:
            return [quality_origin_id]
    return normalize_text_list((benben_config or {}).get("qualityOriginIds"))


def resolve_supplier_ids(sku_query_params: Dict[str, Any], benben_config: Dict[str, Any]) -> List[str]:
    supplier_ids = [
        normalize_text(item.get("supplierOriginId"))
        for item in normalize_supplier_configs((sku_query_params or {}).get("supplierConfigs"))
    ]
    supplier_ids = [item for item in supplier_ids if item]
    if supplier_ids:
        return supplier_ids
    return normalize_text_list((benben_config or {}).get("supplierOriginIds"))


def resolve_region_origin_ids(sku_query_params: Dict[str, Any], benben_config: Dict[str, Any]) -> List[str]:
    region_ids = normalize_text_list((sku_query_params or {}).get("regionOriginIds"))
    if region_ids:
        return region_ids
    return normalize_text_list((benben_config or {}).get("regionOriginIds"))


def filter_and_apply_markup(
    records: List[Dict[str, Any]],
    sku_query_params: Dict[str, Any],
    default_markup_rate: float,
    default_transfer_days: int,
) -> List[Dict[str, Any]]:
    allowed_quality_codes = expand_id_tokens(normalize_text_list((sku_query_params or {}).get("qualityCodes")))
    allowed_quality_ids = expand_id_tokens(normalize_text_list((sku_query_params or {}).get("qualityOriginIds")))
    allowed_brand_ids = expand_id_tokens(normalize_text_list((sku_query_params or {}).get("brandOriginIds")))
    allowed_region_ids = expand_id_tokens(normalize_text_list((sku_query_params or {}).get("regionOriginIds")))
    supplier_configs = normalize_supplier_configs((sku_query_params or {}).get("supplierConfigs"))
    supplier_config_map = {
        f"{normalize_text(item.get('brandOriginId'))}|{normalize_text(item.get('supplierOriginId'))}": item
        for item in supplier_configs
    }
    supplier_fallback_map = {
        normalize_text(item.get("supplierOriginId")): item
        for item in supplier_configs
        if not normalize_text(item.get("brandOriginId"))
    }
    allowed_supplier_ids = {
        normalize_text(item.get("supplierOriginId"))
        for item in supplier_configs
        if normalize_text(item.get("supplierOriginId"))
    }

    filtered: List[Dict[str, Any]] = []
    for record in records or []:
        if not isinstance(record, dict):
            continue
        raw_payload = record.get("rawPayload") if isinstance(record.get("rawPayload"), dict) else {}
        quality_origin_id = normalize_text(record.get("qualityOriginId"))
        quality_code = normalize_text(
            record.get("qualityCode")
            or raw_payload.get("qualityCode")
            or raw_payload.get("partsBrandQuality")
        )
        quality_name = normalize_text(record.get("qualityName"))
        brand_origin_id = normalize_text(record.get("brandOriginId"))
        brand_name = normalize_text(record.get("brandName") or record.get("brand"))
        region_origin_id = normalize_text(record.get("regionOriginId"))
        region_name = normalize_text(record.get("regionName") or record.get("region"))
        supplier_id = normalize_text(record.get("supplierId"))
        supplier_name = normalize_text(record.get("supplierName"))
        company_name = normalize_text(record.get("companyName"))

        quality_allowed = set(allowed_quality_ids)
        quality_allowed.update(allowed_quality_codes)
        if quality_allowed and not matches_allowed(
            [quality_origin_id, quality_code, quality_name], quality_allowed, allow_unknown=False
        ):
            continue
        if allowed_brand_ids and not matches_allowed(
            [brand_origin_id, brand_name], allowed_brand_ids
        ):
            continue
        if allowed_region_ids and not matches_allowed(
            [region_origin_id, region_name], allowed_region_ids
        ):
            continue
        if allowed_supplier_ids and not matches_allowed(
            [supplier_id, supplier_name, company_name], allowed_supplier_ids
        ):
            continue

        # 优先使用“品牌+商家”规则；历史无品牌配置再按商家兜底。
        supplier_cfg = supplier_config_map.get(f"{brand_origin_id}|{supplier_id}") or supplier_fallback_map.get(supplier_id) or {}
        markup_rate = to_float(supplier_cfg.get("markupRate"))
        if markup_rate is None:
            markup_rate = float(default_markup_rate or 0.0)
        transfer_days = to_int(supplier_cfg.get("transferDays"))
        if transfer_days is None:
            transfer_days = int(default_transfer_days or 0)

        platform_price = to_float(record.get("price"))
        if platform_price is None:
            continue
        adjusted_price = apply_markup(platform_price, markup_rate)

        enriched = dict(record)
        enriched["platformPrice"] = adjusted_price_to_float(platform_price)
        enriched["markupRate"] = markup_rate
        enriched["price"] = adjusted_price
        enriched["transferDays"] = transfer_days
        filtered.append(enriched)
    return filtered


def expand_id_tokens(values: List[str]) -> Set[str]:
    expanded: Set[str] = set()
    for value in values or []:
        text = normalize_text(value)
        if not text:
            continue
        expanded.add(text)
        for part in text.split(","):
            token = normalize_text(part)
            if token:
                expanded.add(token)
    return expanded


def matches_allowed(record_values: List[str], allowed_values: Set[str], allow_unknown: bool = True) -> bool:
    if not allowed_values:
        return True
    normalized_record_values = {normalize_text(value) for value in record_values if normalize_text(value)}
    if not normalized_record_values:
        return allow_unknown
    return any(value in allowed_values for value in normalized_record_values)


def apply_markup(price: float, markup_rate: float) -> float:
    value = Decimal(str(price)) * (Decimal("1") + Decimal(str(markup_rate or 0)) / Decimal("100"))
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def adjusted_price_to_float(price: float) -> float:
    value = Decimal(str(price))
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except Exception:
        return None


def to_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except Exception:
        return None


def to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = normalize_text(value).lower()
    return text in {"1", "true", "yes", "y", "on"}


def normalize_crawl_strategy_type(value: Any) -> str:
    strategy = normalize_text(value).upper()
    if strategy == CRAWL_STRATEGY_PRIORITY_STOP_ON_HIT:
        return CRAWL_STRATEGY_PRIORITY_STOP_ON_HIT
    return CRAWL_STRATEGY_FULL_SELECTED
