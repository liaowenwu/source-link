import time
from typing import Dict, Any, List

from core.browser import Browser
from core.task_queue import is_task_paused, is_task_terminate_requested
from platforms.benben.auth import BenbenAuthManager
from platforms.benben.crawler import BenbenCrawler, normalize_supplier_filters, normalize_sku
from service.backend_client import query_products_for_task
from service.reporter import (
    report_task_start,
    report_log,
    report_progress,
    report_result,
    report_item,
    report_done,
    report_error,
)

PLATFORM_NAME = "benben"


def _wait_if_paused(task_id: str) -> None:
    paused_logged = False
    while is_task_paused(task_id) and not is_task_terminate_requested(task_id):
        if not paused_logged:
            report_log(task_id, "任务已暂停，等待继续执行", level="WARNING")
            paused_logged = True
        time.sleep(1)
    if paused_logged and not is_task_terminate_requested(task_id):
        report_log(task_id, "任务已继续执行")


def _should_terminate(task_id: str) -> bool:
    return is_task_terminate_requested(task_id)


def execute(task_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
    task_type = (params.get("taskType") or params.get("mode") or "single").strip().lower()
    trigger_by = params.get("triggerBy") or "qcpj-crawler"
    declared_total = int(params.get("totalCount") or 0)
    scene = str(params.get("scene") or "").strip()
    raw_item_map = params.get("onlineOrderItemMap") or {}
    online_order_item_map: Dict[str, List[int]] = {}
    if isinstance(raw_item_map, dict):
        for raw_sku, raw_ids in raw_item_map.items():
            sku_key = normalize_sku(raw_sku)
            if not sku_key:
                continue
            if isinstance(raw_ids, list):
                values = raw_ids
            elif isinstance(raw_ids, str):
                values = [item.strip() for item in raw_ids.split(",") if item and item.strip()]
            else:
                values = [raw_ids]
            normalized_ids: List[int] = []
            for value in values:
                try:
                    normalized_ids.append(int(value))
                except Exception:
                    continue
            if normalized_ids:
                online_order_item_map[sku_key] = normalized_ids

    report_task_start(task_id, task_type=task_type, trigger_by=trigger_by, total_count=declared_total)
    report_log(task_id, "[犇犇] 开始查询任务关联商品")

    products = query_products_for_task(params)
    total = declared_total if declared_total > 0 else len(products)
    report_log(task_id, f"[犇犇] 查询到商品数量: {len(products)}")

    success_count = 0
    fail_count = 0
    result_rows: List[Dict[str, Any]] = []

    if not products:
        report_log(task_id, "未找到可执行商品，任务结束", level="WARNING")
        report_done(task_id, success_count=0, fail_count=0, total_count=0, message="未找到可执行商品")
        return {
            "taskId": task_id,
            "platform": PLATFORM_NAME,
            "taskType": task_type,
            "successCount": 0,
            "failCount": 0,
            "totalCount": 0,
            "items": [],
        }

    city = str(params.get("city") or "")
    quality_codes = str(params.get("qualityCodes") or "").strip()
    suppliers = normalize_supplier_filters(params)
    supplier_id = str(params.get("supplierId") or "").strip()
    brand_names = str(params.get("brandNames") or "").strip()
    report_log(
        task_id,
        (
            f"[犇犇] 抓取筛选条件: 城市={city or '全部'}，"
            f"供应商={','.join(suppliers) if suppliers else '全部'}，"
            f"qualityCodes={quality_codes or '空'}，"
            f"supplierId={supplier_id or '空'}，brandNames={brand_names or '空'}"
        ),
    )

    browser = None
    try:
        browser = Browser(channel="msedge", headless=True, image=False)
        auth_manager = BenbenAuthManager()
        context = auth_manager.get_context(browser, log_fn=lambda msg: report_log(task_id, str(msg)))
        crawler = BenbenCrawler(
            context=context,
            task_id=task_id,
            city=city,
            suppliers=suppliers,
            quality_codes=quality_codes,
            supplier_ids=supplier_id,
            brand_names=brand_names,
        )

        shared_skus = [normalize_sku(item.get("sku")) for item in products]
        shared_skus = [item for item in shared_skus if item]
        if not crawler.prepare_shared_query(shared_skus):
            raise RuntimeError("获取共享query_id失败，任务已停止")

        report_log(task_id, f"[犇犇] 待抓取商品数量: {len(products)}")
        report_log(task_id, "======================== 开始抓取 =========================")
        start_ts = time.time()

        for index, product in enumerate(products, start=1):
            _wait_if_paused(task_id)
            if _should_terminate(task_id):
                report_log(task_id, "收到终止信号，停止抓取", level="WARNING")
                break

            sku = normalize_sku(product.get("sku"))
            product_name = product.get("productName") or ""

            if not sku:
                fail_count += 1
                message = f"第 {index} 个商品 SKU 为空，已跳过"
                report_log(task_id, message, level="ERROR")
                report_result(task_id, {
                    "sku": "",
                    "productId": product.get("id"),
                    "productName": product_name,
                    "supplierName": "",
                    "resultStatus": "FAILED",
                    "message": message,
                    "errorMessage": message,
                    "skuRecords": [],
                    "raw": {"taskType": task_type, "platform": PLATFORM_NAME},
                })
                report_progress(
                    task_id,
                    success_count=success_count,
                    fail_count=fail_count,
                    total_count=total,
                    message=f"进度 {success_count + fail_count}/{total}",
                )
                continue

            report_log(task_id, "")
            report_log(task_id, f"----------------- 开始抓取 SKU: {sku} -------------------")

            try:
                sku_records = crawler.crawl_sku(sku)
                for record in sku_records:
                    _wait_if_paused(task_id)
                    if _should_terminate(task_id):
                        report_log(task_id, f"抓取 SKU {sku} 期间收到终止信号", level="WARNING")
                        break
                    report_item(task_id, {
                        **record,
                        "scene": scene,
                        "onlineOrderItemIds": online_order_item_map.get(sku, []),
                        "message": "已采集价格记录",
                    })

                if _should_terminate(task_id):
                    break

                success_count += 1
                result_item = {
                    "sku": sku,
                    "productId": product.get("id"),
                    "productName": product_name,
                    "supplierName": "",
                    "resultStatus": "SUCCESS",
                    "message": f"抓取成功，记录数: {len(sku_records)}",
                    "skuRecords": sku_records,
                    "raw": {
                        "taskType": task_type,
                        "platform": PLATFORM_NAME,
                        "recordCount": len(sku_records),
                        "brand": product.get("brand"),
                    },
                }
                report_result(task_id, result_item)
                result_rows.append(result_item)
                report_log(task_id, f"----------------- SKU {sku} 抓取完成 -------------------")
            except Exception as exc:
                fail_count += 1
                error_message = f"SKU {sku} 抓取失败: {exc}"
                report_log(task_id, error_message, level="ERROR")
                report_error(task_id, str(exc), sku=sku)

                result_item = {
                    "sku": sku,
                    "productId": product.get("id"),
                    "productName": product_name,
                    "supplierName": "",
                    "resultStatus": "FAILED",
                    "message": error_message,
                    "errorMessage": str(exc),
                    "skuRecords": [],
                    "raw": {
                        "taskType": task_type,
                        "platform": PLATFORM_NAME,
                        "brand": product.get("brand"),
                    },
                }
                report_result(task_id, result_item)
                result_rows.append(result_item)

            report_progress(
                task_id,
                success_count=success_count,
                fail_count=fail_count,
                total_count=total,
                message=f"进度 {success_count + fail_count}/{total}",
            )

        end_ts = time.time()
        report_log(task_id, f"======================== 抓取完成 =========================，耗时: {round(end_ts - start_ts, 2)}s")
    finally:
        if browser is not None:
            try:
                browser.stop()
                report_log(task_id, "浏览器已关闭")
            except Exception as exc:
                report_log(task_id, f"关闭浏览器失败: {exc}", level="WARNING")

    terminated = _should_terminate(task_id)
    unfinished = max(total - success_count - fail_count, 0)
    final_fail = fail_count + unfinished if terminated else fail_count
    final_message = "任务已终止" if terminated else "任务已完成"

    report_done(
        task_id,
        success_count=success_count,
        fail_count=final_fail,
        total_count=total,
        message=final_message,
    )

    return {
        "taskId": task_id,
        "platform": PLATFORM_NAME,
        "taskType": task_type,
        "successCount": success_count,
        "failCount": final_fail,
        "totalCount": total,
        "terminated": terminated,
        "items": result_rows,
    }
