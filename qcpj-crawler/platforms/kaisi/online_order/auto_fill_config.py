"""在线接单自动补价配置标准化。"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from platforms.benben.crawler import normalize_sku


# 统一清洗奔奔配置，确保后续补价逻辑拿到稳定结构。
def normalize_benben_config(raw_config: Any) -> Dict[str, Any]:
    config = raw_config if isinstance(raw_config, dict) else {}
    region_extra_days = config.get("regionExtraDays") if isinstance(config.get("regionExtraDays"), dict) else {}
    return {
        "crawlStrategyType": normalize_text(config.get("crawlStrategyType")).upper() or "FULL_SELECTED",
        "crawlStrategySelectedPlatformCodes": normalize_text_list(config.get("crawlStrategySelectedPlatformCodes")),
        "crawlStrategyPriorityPlatformCodes": normalize_text_list(config.get("crawlStrategyPriorityPlatformCodes")),
        "crawlStrategyStopOnHit": bool(config.get("crawlStrategyStopOnHit")),
        "qualityIds": normalize_int_list(config.get("qualityIds")),
        "qualityOriginIds": normalize_text_list(config.get("qualityOriginIds")),
        "brandOriginIds": normalize_text_list(config.get("brandOriginIds")),
        "brandNames": normalize_text_list(config.get("brandNames")),
        "regionOriginIds": normalize_text_list(config.get("regionOriginIds")),
        "regionNames": normalize_text_list(config.get("regionNames")),
        "supplierOriginIds": normalize_text_list(config.get("supplierOriginIds")),
        "supplierNames": normalize_text_list(config.get("supplierNames")),
        "defaultCity": normalize_text(config.get("defaultCity")),
        "priceAdvantageRate": normalize_rate(config.get("priceAdvantageRate")),
        "defaultMarkupRate": max(to_float(config.get("defaultMarkupRate")) or 0.0, 0.0),
        "defaultTransferDays": max(to_int(config.get("defaultTransferDays")) or 0, 0),
        "singleSkuMaxCrawlCount": normalize_non_negative_int(config.get("singleSkuMaxCrawlCount")),
        "regionExtraDays": {
            normalize_text(key): max(to_int(value) or 0, 0)
            for key, value in region_extra_days.items()
            if normalize_text(key)
        },
    }


def normalize_robot_config(raw_config: Any) -> Dict[str, Any]:
    config = _extract_platform_config(raw_config, platform_names={"robot", "jiqiren", "机器人"}, platform_ids={"2"})
    region_extra_days = config.get("regionExtraDays") if isinstance(config.get("regionExtraDays"), dict) else {}
    return {
        "qualityIds": normalize_int_list(config.get("qualityIds")),
        "qualityOriginIds": normalize_text_list(config.get("qualityOriginIds")),
        "brandOriginIds": normalize_text_list(config.get("brandOriginIds")),
        "brandNames": normalize_text_list(config.get("brandNames")),
        "regionOriginIds": normalize_text_list(config.get("regionOriginIds")),
        "regionNames": normalize_text_list(config.get("regionNames")),
        "supplierOriginIds": normalize_text_list(config.get("supplierOriginIds")),
        "supplierNames": normalize_text_list(config.get("supplierNames")),
        "defaultCity": normalize_text(config.get("defaultCity")),
        "defaultMarkupRate": max(to_float(config.get("defaultMarkupRate")) or 0.0, 0.0),
        "defaultTransferDays": max(to_int(config.get("defaultTransferDays")) or 0, 0),
        "singleSkuMaxCrawlCount": normalize_non_negative_int(config.get("singleSkuMaxCrawlCount")),
        "regionExtraDays": {
            normalize_text(key): max(to_int(value) or 0, 0)
            for key, value in region_extra_days.items()
            if normalize_text(key)
        },
    }


# 统一清洗价格匹配策略，没有显式配置时回退到奔奔配置。
def normalize_match_strategy(raw_strategy: Any, raw_benben_config: Any = None) -> Dict[str, Any]:
    strategy = raw_strategy if isinstance(raw_strategy, dict) else {}
    benben_config = normalize_benben_config(raw_benben_config)
    price_advantage_rate = to_float(strategy.get("priceAdvantageRate"))
    if price_advantage_rate is None:
        price_advantage_rate = benben_config["priceAdvantageRate"]

    brand_priority = normalize_priority_list(strategy.get("brandPriority"))
    if not brand_priority:
        brand_priority = [
            {
                "originId": origin_id,
                "name": benben_config["brandNames"][index] if index < len(benben_config["brandNames"]) else "",
            }
            for index, origin_id in enumerate(benben_config["brandOriginIds"])
            if origin_id
        ]

    region_priority = normalize_region_priority_list(strategy.get("regionPriority"))
    if not region_priority:
        region_priority = [
            {
                "originId": origin_id,
                "name": benben_config["regionNames"][index] if index < len(benben_config["regionNames"]) else "",
                "extraDays": max(to_int(benben_config["regionExtraDays"].get(origin_id)) or 0, 0),
            }
            for index, origin_id in enumerate(benben_config["regionOriginIds"])
            if origin_id
        ]

    region_extra_days_by_origin: Dict[str, int] = {}
    region_extra_days_by_name: Dict[str, int] = {}
    for item in region_priority:
        origin_id = normalize_text(item.get("originId"))
        name = normalize_text(item.get("name"))
        extra_days = max(to_int(item.get("extraDays")) or 0, 0)
        if origin_id:
            region_extra_days_by_origin[origin_id] = extra_days
        if name:
            region_extra_days_by_name[name.lower()] = extra_days

    return {
        "priceAdvantageRate": round(max(0.0, min(to_float(price_advantage_rate) or 5.0, 100.0)), 2),
        "brandPriority": brand_priority,
        "regionPriority": region_priority,
        "brandIndexByOrigin": {
            item["originId"]: index
            for index, item in enumerate(brand_priority)
            if item.get("originId")
        },
        "brandIndexByName": {
            item["name"].lower(): index
            for index, item in enumerate(brand_priority)
            if item.get("name")
        },
        "regionIndexByOrigin": {
            item["originId"]: index
            for index, item in enumerate(region_priority)
            if item.get("originId")
        },
        "regionIndexByName": {
            item["name"].lower(): index
            for index, item in enumerate(region_priority)
            if item.get("name")
        },
        "regionExtraDaysByOrigin": region_extra_days_by_origin,
        "regionExtraDaysByName": region_extra_days_by_name,
    }


# 把“sku => itemId 列表”标准化成稳定结构。
def normalize_online_order_item_map(raw_item_map: Any) -> Dict[str, List[int]]:
    result: Dict[str, List[int]] = {}
    if not isinstance(raw_item_map, dict):
        return result
    for raw_sku, raw_ids in raw_item_map.items():
        sku_key = normalize_sku(raw_sku)
        if not sku_key:
            continue
        values = raw_ids if isinstance(raw_ids, list) else [raw_ids]
        item_ids: List[int] = []
        for value in values:
            normalized = to_int(value)
            if normalized is not None:
                item_ids.append(normalized)
        if item_ids:
            result[sku_key] = item_ids
    return result


# 把“sku => item 元数据列表”标准化，供自动补价精确回写。
def normalize_online_order_item_meta_map(raw_meta_map: Any) -> Dict[str, List[Dict[str, Any]]]:
    result: Dict[str, List[Dict[str, Any]]] = {}
    if not isinstance(raw_meta_map, dict):
        return result
    for raw_sku, raw_items in raw_meta_map.items():
        sku_key = normalize_sku(raw_sku)
        if not sku_key or not isinstance(raw_items, list):
            continue
        normalized_items: List[Dict[str, Any]] = []
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            normalized_items.append(
                {
                    "itemId": to_int(item.get("itemId")),
                    "quotationId": normalize_text(item.get("quotationId")),
                    "inquiryId": normalize_text(item.get("inquiryId")),
                    "storeId": normalize_text(item.get("storeId")),
                    "resolveResultId": normalize_text(item.get("resolveResultId")),
                    "partsNum": normalize_text(item.get("partsNum")),
                    "partsName": normalize_text(item.get("partsName")),
                    "brandId": normalize_text(item.get("brandId")),
                    "brandName": normalize_text(item.get("brandName")),
                    "qualityCode": normalize_text(item.get("qualityCode")),
                    "qualityOriginId": normalize_text(item.get("qualityOriginId")),
                    "quantity": to_int(item.get("quantity")) or 0,
                    "price": to_float(item.get("price")),
                    "btPrice": to_float(item.get("btPrice")),
                    "source": normalize_text(item.get("source")),
                }
            )
        if normalized_items:
            result[sku_key] = normalized_items
    return result


# 标准化优先级数组。
def normalize_priority_list(raw_items: Any) -> List[Dict[str, str]]:
    result: List[Dict[str, str]] = []
    if not isinstance(raw_items, list):
        return result
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        origin_id = normalize_text(item.get("originId"))
        name = normalize_text(item.get("name"))
        if origin_id or name:
            result.append({"originId": origin_id, "name": name})
    return result


# 标准化区域优先级数组。
def normalize_region_priority_list(raw_items: Any) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    if not isinstance(raw_items, list):
        return result
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        origin_id = normalize_text(item.get("originId"))
        name = normalize_text(item.get("name"))
        extra_days = max(to_int(item.get("extraDays")) or 0, 0)
        if origin_id or name:
            result.append({"originId": origin_id, "name": name, "extraDays": extra_days})
    return result


# 把任意数组去重并转成字符串列表。
def normalize_text_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    result: List[str] = []
    seen = set()
    for item in value:
        text = normalize_text(item)
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result


# 把任意数组去重并转成正整数列表。
def normalize_int_list(value: Any) -> List[int]:
    if not isinstance(value, list):
        return []
    result: List[int] = []
    seen = set()
    for item in value:
        number = to_int(item)
        if number is None or number <= 0 or number in seen:
            continue
        seen.add(number)
        result.append(number)
    return result


# 价格优势阈值统一约束在 0 到 100 之间。
def normalize_rate(value: Any) -> float:
    rate = to_float(value)
    if rate is None:
        return 5.0
    return max(0.0, min(rate, 100.0))


def normalize_non_negative_int(value: Any) -> int:
    number = to_int(value)
    if number is None or number < 0:
        return 0
    return number


# 统一把值转成去首尾空格的文本。
def normalize_text(value: Any) -> str:
    return str(value or "").strip()


# 安全转浮点。
def to_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except Exception:
        return None


# 安全转整数。
def to_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except Exception:
        return None


def _extract_platform_config(raw_config: Any, *, platform_names: set[str], platform_ids: set[str]) -> Dict[str, Any]:
    root = raw_config if isinstance(raw_config, dict) else {}
    direct_config = root.get("robotConfig")
    if isinstance(direct_config, dict):
        return direct_config

    nested_dict_candidates = [
        root.get("platformConfigMap"),
        root.get("platformConfigsMap"),
        root.get("crawlerPlatformConfigMap"),
    ]
    for candidate in nested_dict_candidates:
        if not isinstance(candidate, dict):
            continue
        for key, value in candidate.items():
            key_text = normalize_text(key).lower().replace("_", "").replace("-", "").replace(" ", "")
            if key_text in platform_names or key_text in {"2", "platform2"}:
                return value if isinstance(value, dict) else {}

    list_candidates = [
        root.get("platformConfigs"),
        root.get("crawlerPlatformConfigs"),
        root.get("userPartCrawlerPlatformConfigs"),
        root.get("platformConfigList"),
    ]
    for rows in list_candidates:
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            row_platform_id = normalize_text(
                row.get("platformId")
                or row.get("platform_id")
                or row.get("plantformId")
                or row.get("plantform_id")
            )
            row_platform_name = normalize_text(
                row.get("platformCode")
                or row.get("platform_code")
                or row.get("platformName")
                or row.get("platform_name")
            ).lower().replace("_", "").replace("-", "").replace(" ", "")
            if row_platform_id in platform_ids or row_platform_name in platform_names:
                nested = row.get("config")
                return nested if isinstance(nested, dict) else row
    return {}
