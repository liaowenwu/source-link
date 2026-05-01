import time
from typing import Any, Dict, List

from core.browser import Browser
from platforms.kaisi.auth import KaisiAuthManager
from platforms.kaisi.common.record_mapper import build_realtime_payload, to_result_row
from platforms.kaisi.common.task_state import should_terminate, wait_if_paused
from platforms.kaisi.history.crawler import KaisiCrawler
from service.reporter import (
    report_done,
    report_error,
    report_item,
    report_log,
    report_progress,
    report_result,
    report_task_start,
)

PLATFORM_NAME = "kaisi"

# 执行execute的相关逻辑。
def execute(task_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
    task_type = (params.get("taskType") or params.get("mode") or "single").strip().lower()
    trigger_by = params.get("triggerBy") or "qcpj-crawler"
    declared_total = int(params.get("totalCount") or 0)
    total = declared_total if declared_total > 0 else 1

    report_task_start(task_id, task_type=task_type, trigger_by=trigger_by, total_count=total)
    report_log(task_id, "[开思-历史] 开始抓取历史报价数据")

    success_count = 0
    fail_count = 0
    result_rows: List[Dict[str, Any]] = []

    browser = None
    history: Dict[str, Any] = {}
    pushed_item_count = 0
    start_ts = time.time()

    # 处理记录。
    def _on_record(record: Dict[str, Any]) -> None:
        nonlocal pushed_item_count
        payload = build_realtime_payload(
            record=record,
            task_id=task_id,
            platform=PLATFORM_NAME,
            message="上传开思历史报价记录",
        )
        report_item(task_id, payload)
        pushed_item_count += 1

    try:
        browser = Browser(channel="msedge", headless=True, image=False)
        auth_manager = KaisiAuthManager()
        context = auth_manager.get_context(browser, log_fn=lambda msg: report_log(task_id, str(msg)))

        crawler = KaisiCrawler(
            context=context,
            task_id=task_id,
            params=params,
            item_callback=_on_record,
        )

        wait_if_paused(task_id)
        if should_terminate(task_id):
            report_log(task_id, "抓取前收到终止信号", level="WARNING")
        else:
            history = crawler.crawl_history()

        quote_records = history.get("quoteRecords") or []
        out_of_stock_records = history.get("outOfStockRecords") or []
        demand_summary_rows = history.get("demandSummary") or []

        all_records = [to_result_row(item) for item in quote_records] + [to_result_row(item) for item in out_of_stock_records]

        success_count = 0 if should_terminate(task_id) else 1
        fail_count = 1 if should_terminate(task_id) else 0

        result_item = {
            "sku": "KAISI_HISTORY_TASK",
            "productId": None,
            "productName": "开思历史报价抓取",
            "supplierName": PLATFORM_NAME,
            "resultStatus": "FAILED" if should_terminate(task_id) else "SUCCESS",
            "message": (
                "任务已终止"
                if should_terminate(task_id)
                else (
                    f"抓取完成，报价记录={len(quote_records)}，"
                    f"缺货记录={len(out_of_stock_records)}，需求汇总={len(demand_summary_rows)}"
                )
            ),
            "skuRecords": all_records,
            "raw": {
                "taskType": task_type,
                "platform": PLATFORM_NAME,
                "scene": "history",
                "historyRange": {
                    "startDate": history.get("startDate"),
                    "endDate": history.get("endDate"),
                },
                "historyStats": {
                    "quotationCount": history.get("quotationCount", 0),
                    "quoteRecordCount": len(quote_records),
                    "outOfStockRecordCount": len(out_of_stock_records),
                    "demandSummaryCount": len(demand_summary_rows),
                    "realtimePushedItemCount": pushed_item_count,
                },
                "demandSummary": demand_summary_rows,
                "unmatchedResolveResultIds": history.get("unmatchedResolveResultIds") or [],
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

    except Exception as exc:
        fail_count = 1
        report_log(task_id, f"[开思-历史] 抓取失败: {exc}", level="ERROR")
        report_error(task_id, str(exc))

        result_item = {
            "sku": "KAISI_HISTORY_TASK",
            "productId": None,
            "productName": "开思历史报价抓取",
            "supplierName": PLATFORM_NAME,
            "resultStatus": "FAILED",
            "message": f"抓取失败: {exc}",
            "errorMessage": str(exc),
            "skuRecords": [],
            "raw": {
                "taskType": task_type,
                "platform": PLATFORM_NAME,
                "scene": "history",
                "historyStats": {
                    "realtimePushedItemCount": pushed_item_count,
                },
            },
        }
        report_result(task_id, result_item)
        result_rows.append(result_item)

    finally:
        if browser is not None:
            try:
                browser.stop()
                report_log(task_id, "浏览器已关闭")
            except Exception as exc:
                report_log(task_id, f"关闭浏览器失败: {exc}", level="WARNING")

    terminated = should_terminate(task_id) or bool(history.get("terminated"))
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

    report_log(task_id, f"[开思-历史] 执行结束，耗时={round(time.time() - start_ts, 2)}s")

    return {
        "taskId": task_id,
        "platform": PLATFORM_NAME,
        "taskType": task_type,
        "scene": "history",
        "successCount": success_count,
        "failCount": final_fail,
        "totalCount": total,
        "terminated": terminated,
        "items": result_rows,
    }
