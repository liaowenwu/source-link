from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.browser import Browser
from platforms.benben.auth import BenbenAuthManager
from platforms.benben.crawler import BenbenCrawler
from platforms.kaisi.auth import KaisiAuthManager
from platforms.robot.auth import RobotAuthManager
from platforms.robot.crawler import RobotCrawler
from service.backend_client import (
    get_backend_kaisi_crawler_config,
    get_backend_kaisi_quality_dicts,
    get_backend_online_order_crawler_query_params,
    get_backend_online_order_quotation,
    get_backend_online_order_quotation_items,
)
from service.reporter import (
    clear_task_context,
    register_task_context,
    report_custom_event,
    report_online_order_quotation,
)

from .auto_fill import (
    AUTO_FILL_SCENE,
    build_report_payloads,
    normalize_benben_config,
    normalize_match_strategy,
    normalize_robot_config,
)
from .query_param_support import (
    build_crawler_query_param_map,
    filter_and_apply_markup,
    get_platform_query_params,
    normalize_supplier_configs,
    normalize_text_list,
    resolve_crawl_platform_plan,
    resolve_quality_origin_ids,
    resolve_region_origin_ids,
    resolve_supplier_ids,
)
from .quality_support import build_quality_maps, collect_quality_origin_ids, resolve_item_quality
from .runtime_payloads import apply_auto_fill_result, build_status_payload, build_submit_payload
from .submit_save_tool import save_online_order_quotation
from .runtime_support import (
    EVENT_ONLINE_ORDER_STATUS,
    EVENT_ONLINE_ORDER_SUBMIT,
    NODE_NAME_COMPLETED,
    NODE_NAME_PRICE_FILLING,
    NODE_NAME_SUBMIT_QUOTATION,
    NODE_NAME_WAIT_PRICE_FILL,
    NODE_NAME_WAIT_SUBMIT,
    build_quotation_task_context,
    quotation_task_no,
)


def run_price_fill_once(quotations: List[Dict[str, Any]], task_id: str = "") -> Dict[str, Any]:
    normalized_rows = _normalize_quotation_rows(quotations)
    if not normalized_rows:
        return {
            "mode": "direct",
            "taskId": str(task_id or "").strip(),
            "taskNo": str(task_id or "").strip(),
            "quotationCount": 0,
            "updatedItemCount": 0,
            "quotationResults": [],
        }

    crawler_config = get_backend_kaisi_crawler_config()
    benben_config = normalize_benben_config(crawler_config)
    robot_config = normalize_robot_config(crawler_config)
    match_strategy = normalize_match_strategy({}, benben_config)
    quality_maps = build_quality_maps(get_backend_kaisi_quality_dicts())

    browser = Browser(channel="msedge", headless=True, image=False)
    try:
        benben_crawler: Optional[BenbenCrawler] = None
        robot_crawler: Optional[RobotCrawler] = None

        def ensure_price_fill_crawler(platform_name: str, quotation_task_id: str):
            nonlocal benben_crawler, robot_crawler
            if platform_name == "benben":
                if benben_crawler is None:
                    context = BenbenAuthManager().get_context(
                        browser,
                        log_fn=lambda *_args, **_kwargs: None,
                    )
                    benben_crawler = BenbenCrawler(
                        context=context,
                        task_id=str(task_id or "ONLINE_ORDER_DIRECT_PRICE_FILL").strip(),
                        city=str(benben_config.get("defaultCity") or ""),
                        suppliers=benben_config.get("supplierNames") or [],
                        supplier_ids=",".join(
                            [str(item) for item in benben_config.get("supplierOriginIds") or [] if str(item).strip()]
                        ),
                        brand_names=",".join(
                            [str(item) for item in benben_config.get("brandNames") or [] if str(item).strip()]
                        ),
                        single_sku_max_crawl_count=int(benben_config.get("singleSkuMaxCrawlCount") or 0),
                    )
                benben_crawler.set_log_task_id(quotation_task_id)
                return benben_crawler
            if platform_name == "robot":
                if robot_crawler is None:
                    context = RobotAuthManager().get_context(
                        browser,
                        log_fn=lambda *_args, **_kwargs: None,
                    )
                    robot_crawler = RobotCrawler(
                        context=context,
                        task_id=str(task_id or "ONLINE_ORDER_DIRECT_PRICE_FILL").strip(),
                        city=str(robot_config.get("defaultCity") or ""),
                        suppliers=robot_config.get("supplierNames") or [],
                        quality_origin_ids=",".join(
                            [str(item) for item in robot_config.get("qualityOriginIds") or [] if str(item).strip()]
                        ),
                        supplier_ids=",".join(
                            [str(item) for item in robot_config.get("supplierOriginIds") or [] if str(item).strip()]
                        ),
                        brand_names=",".join(
                            [str(item) for item in robot_config.get("brandNames") or [] if str(item).strip()]
                        ),
                        single_sku_max_crawl_count=int(robot_config.get("singleSkuMaxCrawlCount") or 0),
                    )
                robot_crawler.set_log_task_id(quotation_task_id)
                return robot_crawler
            return None

        quotation_results: List[Dict[str, Any]] = []
        updated_item_count = 0
        error_count = 0

        for row in normalized_rows:
            quotation_id = row["quotationId"]
            store_id = row["storeId"]
            quotation_task_id = _quotation_task_id(quotation_id, task_id)
            _register_direct_context(
                quotation_task_id=quotation_task_id,
                quotation_id=quotation_id,
                store_id=store_id,
                manual_price_fill_enabled=True,
                auto_submit_enabled=False,
            )
            seed = {
                "quotationId": quotation_id,
                "storeId": store_id,
                "inquiryId": row.get("inquiryId"),
            }
            try:
                quotation = _load_backend_quotation(quotation_id, store_id)
                items = _load_backend_items(quotation_id, store_id, quality_maps)
                sku_query_param_map = build_crawler_query_param_map(
                    get_backend_online_order_crawler_query_params(quotation_id, store_id)
                )
                context_row = _build_direct_context_row(
                    quotation_id=quotation_id,
                    store_id=store_id,
                    quotation=quotation,
                    items=items,
                    row=row,
                    manual_price_fill_enabled=True,
                    auto_submit_enabled=False,
                )
                _safe_report_status(
                    quotation_task_id=quotation_task_id,
                    payload=build_status_payload(
                        manual_price_fill_enabled=True,
                        auto_submit_enabled=False,
                        quotation_id=quotation_id,
                        store_id=store_id,
                        flow_status="WAIT_PRICE_FILL",
                        process_status="PROCESSING",
                        current_node_code="PRICE_FILLING",
                        current_node_name=NODE_NAME_PRICE_FILLING,
                        message="Direct price-fill started",
                        seed=context_row,
                    ),
                )

                target_items = [
                    item
                    for item in items
                    if str(item.get("source") or "").strip().upper() != "AUTO"
                    and not item.get("btPrice")
                    and not item.get("price")
                ]
                if not target_items:
                    context_row["itemCount"] = len(context_row.get("items") or [])
                    context_row["flowStatus"] = "WAIT_SUBMIT"
                    context_row["processStatus"] = "PROCESSING"
                    context_row["currentNodeCode"] = "WAIT_SUBMIT"
                    context_row["currentNodeName"] = NODE_NAME_WAIT_SUBMIT
                    context_row["message"] = "No pending items for price-fill"
                    report_online_order_quotation(quotation_task_id, context_row)
                    _safe_report_status(
                        quotation_task_id=quotation_task_id,
                        payload=build_status_payload(
                            manual_price_fill_enabled=True,
                            auto_submit_enabled=False,
                            quotation_id=quotation_id,
                            store_id=store_id,
                            flow_status="WAIT_SUBMIT",
                            process_status="PROCESSING",
                            current_node_code="WAIT_SUBMIT",
                            current_node_name=NODE_NAME_WAIT_SUBMIT,
                            message="No pending items for price-fill",
                            seed=context_row,
                        ),
                    )
                    quotation_results.append(
                        {
                            "quotationId": quotation_id,
                            "storeId": store_id,
                            "itemCount": len(items),
                            "targetItemCount": 0,
                            "updatedItemCount": 0,
                            "mode": "direct",
                        }
                    )
                    continue

                sku_to_items: Dict[str, List[Dict[str, Any]]] = {}
                for item in target_items:
                    sku = str(item.get("partsNum") or "").replace(" ", "")
                    if sku:
                        sku_to_items.setdefault(sku, []).append(item)

                shared_skus = list(sku_to_items.keys())
                if not shared_skus:
                    raise RuntimeError("No valid partsNum found for price-fill")
                # 先收集当前报价单所有 SKU 实际需要用到的平台，避免后面重复初始化 crawler。
                required_platforms: List[str] = []
                # 遍历每个 SKU，按“sku 级 -> 全局级”解析抓取平台策略。
                for sku in shared_skus:
                    # 取该 SKU 的查询参数（如果没有则用空 dict）。
                    sku_query_params = sku_query_param_map.get(sku) or {}
                    # 解析该 SKU 对应的平台执行计划（包含顺序与 stopOnHit）。
                    platform_plan = resolve_crawl_platform_plan(sku_query_params, benben_config)
                    # 把该 SKU 计划中的平台顺序并入 required_platforms（去重保序）。
                    for platform_name in platform_plan.get("platformSequence") or []:
                        if platform_name not in required_platforms:
                            required_platforms.append(platform_name)
                # 再过滤一次，仅保留当前 direct 模式支持的平台。
                required_platforms = [item for item in required_platforms if item in {"benben", "robot"}]
                # 若策略结果为空，兜底只跑 benben，避免任务直接失败。
                if not required_platforms:
                    required_platforms = ["benben"]
                # 对需要的平台做共享查询预热（同一平台仅初始化一次）。
                for platform_name in required_platforms:
                    crawler = ensure_price_fill_crawler(platform_name, quotation_task_id)
                    if crawler is None:
                        continue
                    if not crawler.prepare_shared_query(shared_skus):
                        raise RuntimeError(f"Prepare {platform_name} shared query failed")

                matched_item_count = 0
                for sku, sku_items in sku_to_items.items():
                    sku_query_params = sku_query_param_map.get(sku) or {}
                    benben_query_params = get_platform_query_params(sku_query_params, "benben")
                    robot_query_params = get_platform_query_params(sku_query_params, "robot")
                    quality_origin_ids = resolve_quality_origin_ids(sku_items, benben_query_params, benben_config)
                    if not quality_origin_ids:
                        quality_origin_ids = collect_quality_origin_ids(sku_items)
                    supplier_ids = resolve_supplier_ids(benben_query_params, benben_config)
                    brand_names = normalize_text_list(benben_config.get("brandNames"))
                    default_markup_rate = float(benben_config.get("defaultMarkupRate") or 0.0)
                    default_transfer_days = int(benben_config.get("defaultTransferDays") or 0)
                    region_origin_ids = resolve_region_origin_ids(benben_query_params, benben_config)
                    robot_supplier_ids = [
                        str(item.get("supplierOriginId")).strip()
                        for item in normalize_supplier_configs(robot_query_params.get("supplierConfigs"))
                        if str(item.get("supplierOriginId")).strip()
                    ]
                    if not robot_supplier_ids:
                        robot_supplier_ids = normalize_text_list(robot_config.get("supplierOriginIds"))
                    robot_brand_names = normalize_text_list(robot_query_params.get("brandNames")) or normalize_text_list(robot_config.get("brandNames"))
                    robot_region_origin_ids = normalize_text_list(robot_query_params.get("regionOriginIds")) or normalize_text_list(robot_config.get("regionOriginIds"))
                    robot_quality_origin_ids = normalize_text_list(robot_query_params.get("qualityOriginIds")) or normalize_text_list(robot_config.get("qualityOriginIds"))
                    # 重新解析当前 SKU 的平台计划，确保逐 SKU 执行顺序准确。
                    platform_plan = resolve_crawl_platform_plan(sku_query_params, benben_config)
                    # 优先取 SKU 自己的平台顺序；没有则回退到报价单级 required_platforms。
                    platform_sequence = [
                        item for item in (platform_plan.get("platformSequence") or required_platforms)
                        if item in {"benben", "robot"}
                    ]
                    # 如果仍为空，兜底为 benben。
                    if not platform_sequence:
                        platform_sequence = ["benben"]
                    # 是否命中即停：优先策略为 true，全量策略通常为 false。
                    stop_on_hit = bool(platform_plan.get("stopOnHit"))
                    # 本 SKU 的最终聚合记录（可能来自一个或多个平台）。
                    sku_records: List[Dict[str, Any]] = []
                    # 按平台顺序抓取。
                    for platform_name in platform_sequence:
                        # 获取对应平台 crawler（懒初始化，复用同一浏览器上下文）。
                        crawler = ensure_price_fill_crawler(platform_name, quotation_task_id)
                        if crawler is None:
                            continue
                        # 执行平台抓取。
                        if platform_name == "robot":
                            raw_records = crawler.crawl_sku(
                                sku,
                                quality_origin_ids=",".join(robot_quality_origin_ids),
                                supplier_ids=",".join(robot_supplier_ids),
                                brand_names=",".join(robot_brand_names),
                                region_origin_ids=",".join(robot_region_origin_ids),
                            )
                        else:
                            raw_records = crawler.crawl_sku(
                                sku,
                                quality_origin_ids=",".join(quality_origin_ids),
                                supplier_ids=",".join(supplier_ids),
                                brand_names=",".join(brand_names),
                                region_origin_ids=",".join(region_origin_ids),
                            )
                        # 对平台原始结果做过滤与加价处理。
                        current_records = filter_and_apply_markup(
                            raw_records,
                            robot_query_params if platform_name == "robot" else benben_query_params,
                            default_markup_rate=default_markup_rate,
                            default_transfer_days=default_transfer_days,
                        )
                        # 合并到当前 SKU 总结果集中。
                        sku_records.extend(current_records)
                        # 若启用命中即停且当前平台有命中，则停止后续平台抓取。
                        if stop_on_hit and current_records:
                            break
                    report_payloads = build_report_payloads(
                        sku=sku,
                        scene=AUTO_FILL_SCENE,
                        sku_records=sku_records,
                        online_order_item_ids=[],
                        online_order_item_metas=sku_items,
                        match_strategy=match_strategy,
                    )
                    for payload in report_payloads:
                        payload.setdefault("quotationId", quotation_id)
                        payload.setdefault("storeId", store_id)
                        if _has_selected_candidate(payload):
                            matched_item_count += 1
                        apply_auto_fill_result(context_row, payload)

                context_row["itemCount"] = len(context_row.get("items") or [])
                context_row["flowStatus"] = "WAIT_SUBMIT"
                context_row["processStatus"] = "PROCESSING"
                context_row["currentNodeCode"] = "WAIT_SUBMIT"
                context_row["currentNodeName"] = NODE_NAME_WAIT_SUBMIT
                context_row["message"] = "Direct price-fill completed"
                report_online_order_quotation(quotation_task_id, context_row)
                _safe_report_status(
                    quotation_task_id=quotation_task_id,
                    payload=build_status_payload(
                        manual_price_fill_enabled=True,
                        auto_submit_enabled=False,
                        quotation_id=quotation_id,
                        store_id=store_id,
                        flow_status="WAIT_SUBMIT",
                        process_status="PROCESSING",
                        current_node_code="WAIT_SUBMIT",
                        current_node_name=NODE_NAME_WAIT_SUBMIT,
                        message="Direct price-fill completed",
                        seed=context_row,
                    ),
                )

                updated_item_count += matched_item_count
                quotation_results.append(
                    {
                        "quotationId": quotation_id,
                        "storeId": store_id,
                        "itemCount": len(items),
                        "targetItemCount": len(target_items),
                        "updatedItemCount": matched_item_count,
                        "mode": "direct",
                    }
                )
            except Exception as exc:
                error_count += 1
                _safe_report_status(
                    quotation_task_id=quotation_task_id,
                    payload=build_status_payload(
                        manual_price_fill_enabled=True,
                        auto_submit_enabled=False,
                        quotation_id=quotation_id,
                        store_id=store_id,
                        flow_status="WAIT_PRICE_FILL",
                        process_status="FAILED",
                        current_node_code="PRICE_FILLING",
                        current_node_name=NODE_NAME_PRICE_FILLING,
                        message=f"Direct price-fill failed: {exc}",
                        error_message=str(exc),
                        seed=seed,
                    ),
                )
                quotation_results.append(
                    {
                        "quotationId": quotation_id,
                        "storeId": store_id,
                        "itemCount": 0,
                        "targetItemCount": 0,
                        "updatedItemCount": 0,
                        "mode": "direct",
                        "error": str(exc),
                    }
                )
            finally:
                clear_task_context(quotation_task_id)

        return {
            "mode": "direct",
            "taskId": str(task_id or "").strip(),
            "taskNo": str(task_id or "").strip(),
            "quotationCount": len(normalized_rows),
            "updatedItemCount": updated_item_count,
            "errorCount": error_count,
            "quotationResults": quotation_results,
        }
    finally:
        browser.stop()


def run_submit_once(quotations: List[Dict[str, Any]], task_id: str = "") -> Dict[str, Any]:
    normalized_rows = _normalize_quotation_rows(quotations)
    if not normalized_rows:
        return {
            "mode": "direct",
            "taskId": str(task_id or "").strip(),
            "taskNo": str(task_id or "").strip(),
            "enqueuedCount": 0,
            "submittedCount": 0,
            "quotationResults": [],
        }

    quotation_results: List[Dict[str, Any]] = []
    submitted_count = 0
    error_count = 0

    browser = Browser(channel="msedge", headless=True, image=False)
    try:
        context = KaisiAuthManager().get_context(
            browser,
            log_fn=lambda *_args, **_kwargs: None,
        )
        for row in normalized_rows:
            quotation_id = row["quotationId"]
            store_id = row["storeId"]
            quotation_task_id = _quotation_task_id(quotation_id, task_id)
            _register_direct_context(
                quotation_task_id=quotation_task_id,
                quotation_id=quotation_id,
                store_id=store_id,
                manual_price_fill_enabled=True,
                auto_submit_enabled=False,
            )
            seed = {
                "quotationId": quotation_id,
                "storeId": store_id,
                "inquiryId": row.get("inquiryId"),
            }
            try:
                quotation = _load_backend_quotation(quotation_id, store_id)
                items = get_backend_online_order_quotation_items(quotation_id, store_id)
                if not items:
                    raise RuntimeError("Quotation items are empty")

                seed = {
                    **seed,
                    "inquiryId": str(quotation.get("inquiryId") or seed.get("inquiryId") or "").strip(),
                    "statusId": str(quotation.get("statusId") or "").strip(),
                    "statusIdDesc": str(quotation.get("statusIdDesc") or "").strip(),
                    "displayModelName": str(quotation.get("displayModelName") or "").strip(),
                    "supplierCompanyId": str(quotation.get("supplierCompanyId") or "").strip(),
                }
                _safe_report_status(
                    quotation_task_id=quotation_task_id,
                    payload=build_status_payload(
                        manual_price_fill_enabled=True,
                        auto_submit_enabled=False,
                        quotation_id=quotation_id,
                        store_id=store_id,
                        flow_status="WAIT_SUBMIT",
                        process_status="PROCESSING",
                        current_node_code="SUBMIT_QUOTATION",
                        current_node_name=NODE_NAME_SUBMIT_QUOTATION,
                        message="Direct submit started",
                        seed=seed,
                    ),
                )

                submit_result = save_online_order_quotation(
                    context=context,
                    quotation=quotation,
                    items=items,
                    quotation_source="PC",
                    save_status="DRAFT",
                    back_url="",
                )
                process_status = "SUCCESS" if submit_result.get("success") else "FAILED"
                submit_payload = build_submit_payload(
                    quotation_id=quotation_id,
                    store_id=store_id,
                    process_status=process_status,
                    submit_results=submit_result.get("submitResults") or [],
                    message=str(submit_result.get("message") or ""),
                )
                report_custom_event(quotation_task_id, EVENT_ONLINE_ORDER_SUBMIT, submit_payload)
                _safe_report_status(
                    quotation_task_id=quotation_task_id,
                    payload=build_status_payload(
                        manual_price_fill_enabled=True,
                        auto_submit_enabled=False,
                        quotation_id=quotation_id,
                        store_id=store_id,
                        flow_status="COMPLETED" if process_status == "SUCCESS" else "WAIT_SUBMIT",
                        process_status=process_status,
                        current_node_code="COMPLETED" if process_status == "SUCCESS" else "WAIT_SUBMIT",
                        current_node_name=NODE_NAME_COMPLETED if process_status == "SUCCESS" else NODE_NAME_WAIT_SUBMIT,
                        message=submit_payload["message"],
                        error_message="" if process_status == "SUCCESS" else str(submit_result.get("message") or "Direct submit failed"),
                        seed=seed,
                    ),
                )
                if process_status == "SUCCESS":
                    submitted_count += 1
                else:
                    error_count += 1
                quotation_results.append(
                    {
                        "quotationId": quotation_id,
                        "storeId": store_id,
                        "itemCount": len(items),
                        "successItemCount": int(submit_result.get("successCount") or 0),
                        "failedItemCount": int(submit_result.get("failCount") or 0),
                        "processStatus": process_status,
                        "mode": "direct",
                        "request": submit_result.get("request"),
                        "response": submit_result.get("response"),
                    }
                )
            except Exception as exc:
                error_count += 1
                _safe_report_status(
                    quotation_task_id=quotation_task_id,
                    payload=build_status_payload(
                        manual_price_fill_enabled=True,
                        auto_submit_enabled=False,
                        quotation_id=quotation_id,
                        store_id=store_id,
                        flow_status="WAIT_SUBMIT",
                        process_status="FAILED",
                        current_node_code="SUBMIT_QUOTATION",
                        current_node_name=NODE_NAME_SUBMIT_QUOTATION,
                        message=f"Direct submit failed: {exc}",
                        error_message=str(exc),
                        seed=seed,
                    ),
                )
                quotation_results.append(
                    {
                        "quotationId": quotation_id,
                        "storeId": store_id,
                        "itemCount": 0,
                        "successItemCount": 0,
                        "failedItemCount": 0,
                        "processStatus": "FAILED",
                        "mode": "direct",
                        "error": str(exc),
                    }
                )
            finally:
                clear_task_context(quotation_task_id)
    finally:
        browser.stop()

    return {
        "mode": "direct",
        "taskId": str(task_id or "").strip(),
        "taskNo": str(task_id or "").strip(),
        "enqueuedCount": len(normalized_rows),
        "submittedCount": submitted_count,
        "errorCount": error_count,
        "quotationResults": quotation_results,
    }


def _normalize_quotation_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    seen = set()
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        quotation_id = str(row.get("quotationId") or "").strip()
        store_id = str(row.get("storeId") or "").strip()
        if not quotation_id or not store_id:
            continue
        key = f"{quotation_id}::{store_id}"
        if key in seen:
            continue
        seen.add(key)
        normalized.append(
            {
                "quotationId": quotation_id,
                "storeId": store_id,
                "inquiryId": str(row.get("inquiryId") or "").strip(),
            }
        )
    return normalized


def _quotation_task_id(quotation_id: str, task_id: str = "") -> str:
    return quotation_task_no(quotation_id, fallback=str(task_id or "").strip())


def _register_direct_context(
    *,
    quotation_task_id: str,
    quotation_id: str,
    store_id: str,
    manual_price_fill_enabled: bool,
    auto_submit_enabled: bool,
) -> None:
    register_task_context(
        quotation_task_id,
        build_quotation_task_context(
            quotation_id=quotation_id,
            store_id=store_id,
            manual_price_fill_enabled=manual_price_fill_enabled,
            auto_submit_enabled=auto_submit_enabled,
            backend_task_no=quotation_task_id,
            runtime_id="",
        ),
    )


def _load_backend_items(
    quotation_id: str,
    store_id: str,
    quality_maps: Dict[str, Dict[str, Dict[str, str]]],
) -> List[Dict[str, Any]]:
    rows = get_backend_online_order_quotation_items(quotation_id, store_id)
    return [resolve_item_quality(item, quality_maps) for item in rows if isinstance(item, dict)]


def _load_backend_quotation(quotation_id: str, store_id: str) -> Dict[str, Any]:
    row = get_backend_online_order_quotation(quotation_id, store_id)
    return row if isinstance(row, dict) else {}


def _build_direct_context_row(
    *,
    quotation_id: str,
    store_id: str,
    quotation: Dict[str, Any],
    items: List[Dict[str, Any]],
    row: Dict[str, Any],
    manual_price_fill_enabled: bool,
    auto_submit_enabled: bool,
) -> Dict[str, Any]:
    inquiry_id = str(row.get("inquiryId") or quotation.get("inquiryId") or "").strip()
    if not inquiry_id:
        inquiry_id = str(next((item.get("inquiryId") for item in items if item.get("inquiryId")), "") or "").strip()
    return {
        "platform": "kaisi",
        "scene": "online_order",
        "manualPriceFillEnabled": manual_price_fill_enabled,
        "autoSubmitEnabled": auto_submit_enabled,
        "quotationId": quotation_id,
        "storeId": store_id,
        "inquiryId": inquiry_id,
        "supplierCompanyId": str(row.get("supplierCompanyId") or quotation.get("supplierCompanyId") or "").strip(),
        "statusId": str(row.get("statusId") or quotation.get("statusId") or "").strip(),
        "statusIdDesc": str(row.get("statusIdDesc") or quotation.get("statusIdDesc") or "").strip(),
        "displayModelName": str(row.get("displayModelName") or quotation.get("displayModelName") or "").strip(),
        "createdStamp": quotation.get("createdStamp") or row.get("createdStamp"),
        "lastUpdatedStamp": quotation.get("lastUpdatedStamp") or row.get("lastUpdatedStamp"),
        "itemCount": len(items),
        "items": items,
    }


def _has_selected_candidate(payload: Dict[str, Any]) -> bool:
    auto_fill_detail = payload.get("autoFillDetail")
    if not isinstance(auto_fill_detail, dict):
        return False
    return bool(auto_fill_detail.get("selected"))


def _safe_report_status(quotation_task_id: str, payload: Dict[str, Any]) -> None:
    try:
        report_custom_event(quotation_task_id, EVENT_ONLINE_ORDER_STATUS, payload)
    except Exception:
        return
