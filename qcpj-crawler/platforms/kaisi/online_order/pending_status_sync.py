"""开思在线接单启动前的待完成报价单状态与详情同步服务。"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from core.browser import Browser
from platforms.kaisi.auth import KaisiAuthManager
from service.reporter import (
    flush_online_order_quotation,
    register_task_context,
    report_custom_event,
    report_log,
    report_online_order_quotation,
)

from .crawler import KaisiOnlineOrderCrawler
from .runtime_payloads import build_quotation_payload
from .runtime_support import (
    EVENT_ONLINE_ORDER_STATUS,
    build_quotation_task_context,
    normalize_seed,
    quotation_task_no,
)


# 启动前状态同步统一落到这个节点编码，便于后端执行节点和日志按同一节点展示。
SYNC_NODE_CODE = "SYNC_PENDING_STATUS"
# 启动前状态同步统一落到这个节点名称，前端列表和日志都能直接显示中文。
SYNC_NODE_NAME = "启动前状态同步"
# 启动前详情同步使用单独的节点编码，便于后端执行日志和节点轨迹区分“拉详情”和“改状态”两个动作。
DETAIL_SYNC_NODE_CODE = "SYNC_PENDING_DETAIL"
# 启动前详情同步使用单独的节点名称，用户在日志列表里可以直接看出这是预同步详情。
DETAIL_SYNC_NODE_NAME = "启动前同步详情"


def _quotation_report_task_id(task_id: str, quotation_id: str) -> str:
    return quotation_task_no(quotation_id, fallback=task_id)


def _register_quotation_context(
    *,
    task_id: str,
    source: Optional[Dict[str, Any]],
    latest: Optional[Dict[str, Any]],
    manual_price_fill_enabled: bool,
    auto_submit_enabled: bool,
) -> str:
    normalized_source = normalize_seed(source or {})
    normalized_latest = normalize_seed(latest or {})
    quotation_id = str(normalized_latest.get("quotationId") or normalized_source.get("quotationId") or "").strip()
    store_id = str(normalized_latest.get("storeId") or normalized_source.get("storeId") or "").strip()
    quotation_task_id = _quotation_report_task_id(task_id, quotation_id)
    register_task_context(
        quotation_task_id,
        build_quotation_task_context(
            quotation_id=quotation_id,
            store_id=store_id,
            manual_price_fill_enabled=manual_price_fill_enabled,
            auto_submit_enabled=auto_submit_enabled,
            backend_task_no=task_id,
            runtime_id=task_id,
            extra_context={
                "platform": "kaisi",
                "inquiryId": str(normalized_latest.get("inquiryId") or normalized_source.get("inquiryId") or "").strip(),
                "statusId": str(normalized_latest.get("statusId") or normalized_source.get("statusId") or "").strip(),
                "statusIdDesc": str(normalized_latest.get("statusIdDesc") or normalized_source.get("statusIdDesc") or "").strip(),
                "displayModelName": str(normalized_latest.get("displayModelName") or normalized_source.get("displayModelName") or "").strip(),
                "supplierCompanyId": str(normalized_latest.get("supplierCompanyId") or normalized_source.get("supplierCompanyId") or "").strip(),
            },
        ),
    )
    return quotation_task_id


def sync_pending_quotation_statuses(
    task_id: str,
    quotations: Optional[Iterable[Dict[str, Any]]],
    manual_price_fill_enabled: bool = True,
    auto_submit_enabled: bool = False,
) -> Dict[str, Any]:
    """启动在线接单前，同步当前未完成报价单的最新状态与详情。"""

    # 先把前端传入的报价单列表规整成最小同步模型，避免后续流程反复做空值判断。
    normalized_rows = _normalize_rows(quotations)
    # 任务号为空或没有待同步数据时直接返回，避免无意义地拉起浏览器。
    if not str(task_id or "").strip() or not normalized_rows:
        # 即使没有待同步报价单，也要写主线程日志，方便快速区分“前端没传数据”和“同步过程失败”。
        if str(task_id or "").strip():
            report_log(task_id, "启动前待同步报价单为空，本次跳过状态和详情同步", level="WARNING")
        return {
            "requestedCount": len(normalized_rows),
            "syncedCount": 0,
            "detailSyncedCount": 0,
            "skippedCount": len(normalized_rows),
            "failedCount": 0,
            "detailFailedCount": 0,
        }

    # 先写一条主线程日志，方便前端在 sync_task_log 中看到启动前同步动作。
    report_log(task_id, f"启动前开始同步未完成报价单状态和详情，待同步数量={len(normalized_rows)}")

    # 同步逻辑需要复用本地开思登录态，所以这里临时启动一个浏览器上下文。
    browser = None
    # 统计信息最终会回传给启动接口，便于前端知道本次预同步执行结果。
    synced_count = 0
    # 单独统计详情同步成功数量，便于排查“状态更新了但详情没入库”的场景。
    detail_synced_count = 0
    skipped_count = 0
    failed_count = 0
    # 详情同步失败不一定阻断状态同步，因此这里单独维护详情失败计数。
    detail_failed_count = 0

    try:
        # 使用本地 Edge 无头浏览器复用 cookies，减少对现有运行时主流程的侵入。
        browser = Browser(channel="msedge", headless=True, image=False)
        # 直接走认证管理器的统一入口，未登录时会拉起登录流程，保证同步结果可信。
        context = KaisiAuthManager().get_context(browser, log_fn=lambda *_args, **_kwargs: None)
        # 这里只复用开思报价单查询能力，不启动在线接单运行时线程。
        crawler = KaisiOnlineOrderCrawler(
            context=context,
            task_id=str(task_id).strip(),
            params={"scene": "online_order"},
        )

        # 逐条同步当前待完成报价单，避免单条异常导致整批同步中断。
        for row in normalized_rows:
            # 每条记录都至少要有 inquiryId，开思侧是按询价单查询最新报价单状态。
            inquiry_id = str(row.get("inquiryId") or "").strip()
            # 报价单号用于在同一询价单多条记录时优先匹配目标报价单。
            quotation_id = str(row.get("quotationId") or "").strip()
            # 门店编号用于进一步缩小查询范围，减少错配。
            store_id = str(row.get("storeId") or "").strip()

            # 缺少 inquiryId 无法发起开思查询，这种数据直接跳过并记录告警。
            row_task_id = _register_quotation_context(
                task_id=task_id,
                source=row,
                latest=None,
                manual_price_fill_enabled=manual_price_fill_enabled,
                auto_submit_enabled=auto_submit_enabled,
            )
            if not inquiry_id:
                skipped_count += 1
                report_log(
                    row_task_id,
                    f"启动前同步跳过报价单：缺少 inquiryId，报价单号={quotation_id or '-'}，门店={store_id or '-'}",
                    level="WARNING",
                )
                continue

            try:
                # 强制刷新开思列表接口，优先拿到最新业务状态，避免使用旧缓存。
                crawler.set_log_task_id(row_task_id)
                latest_match = crawler.query_quotations_by_inquiry_id(
                    inquiry_id=inquiry_id,
                    max_pages=3,
                    store_id=store_id,
                    force_refresh=True,
                    prefer_quotation_id=quotation_id,
                )
                latest_rows = [latest_match] if latest_match else []
                # 从同一询价单结果里挑出与当前报价单最匹配的最新一条记录。
                latest_row = _pick_latest_row(latest_rows, quotation_id, store_id)

                # 开思侧查不到最新记录时不强行覆盖数据库状态，避免误改。
                if not latest_row:
                    skipped_count += 1
                    report_log(
                        row_task_id,
                        f"启动前同步未命中开思最新状态：报价单号={quotation_id or '-'}，询价单号={inquiry_id}",
                        level="WARNING",
                    )
                    continue

                # 把开思最新状态映射成在线接单模块内部状态，再推送给后端落库。
                quotation_task_id = _register_quotation_context(
                    task_id=task_id,
                    source=row,
                    latest=latest_row,
                    manual_price_fill_enabled=manual_price_fill_enabled,
                    auto_submit_enabled=auto_submit_enabled,
                )
                crawler.set_log_task_id(quotation_task_id)
                status_payload = _build_status_payload(
                    source=row,
                    latest=latest_row,
                    manual_price_fill_enabled=manual_price_fill_enabled,
                    auto_submit_enabled=auto_submit_enabled,
                )
                # 启动前同步不仅要更新状态，也要把报价单详情补拉到后端，避免详情页和执行日志为空。
                try:
                    detail_synced = _sync_pending_quotation_detail(
                        task_id=quotation_task_id,
                        crawler=crawler,
                        source=row,
                        latest=latest_row,
                        status_payload=status_payload,
                        manual_price_fill_enabled=manual_price_fill_enabled,
                        auto_submit_enabled=auto_submit_enabled,
                    )
                    # 详情同步结果单独计数，便于启动返回信息明确反馈。
                    if detail_synced:
                        detail_synced_count += 1
                except Exception as detail_exc:
                    # 详情同步失败时仍继续回写状态，避免用户只能看到旧状态。
                    detail_failed_count += 1
                    report_log(
                        quotation_task_id,
                        (
                            f"启动前同步报价单详情失败：报价单号={quotation_id or '-'}，"
                            f"询价单号={inquiry_id}，错误={detail_exc}"
                        ),
                        level="WARNING",
                    )
                # 沿用在线接单状态事件，后端会统一更新主表、执行日志和节点日志。
                report_custom_event(quotation_task_id, EVENT_ONLINE_ORDER_STATUS, status_payload)
                synced_count += 1
            except Exception as exc:
                # 单条失败只记告警并继续后续记录，避免整批同步因为一条数据失败而中断。
                failed_count += 1
                report_log(
                    row_task_id,
                    f"启动前同步报价单状态失败：报价单号={quotation_id or '-'}，询价单号={inquiry_id}，错误={exc}",
                    level="WARNING",
                )
    finally:
        # 无论同步成功还是失败，都要及时关闭临时浏览器，避免本地残留无头进程。
        if browser is not None:
            try:
                browser.stop()
            except Exception:
                pass

    # 同步结束后再写一条汇总日志，前端主线程日志按钮里可以直接看到结果。
    report_log(
        task_id,
        (
            f"启动前同步未完成报价单状态和详情结束：状态成功={synced_count}，"
            f"详情成功={detail_synced_count}，跳过={skipped_count}，"
            f"失败={failed_count}，详情失败={detail_failed_count}"
        ),
    )
    # 把统计信息回传给启动接口，便于前端决定是否需要提示用户。
    return {
        "requestedCount": len(normalized_rows),
        "syncedCount": synced_count,
        "detailSyncedCount": detail_synced_count,
        "skippedCount": skipped_count,
        "failedCount": failed_count,
        "detailFailedCount": detail_failed_count,
    }


def _sync_pending_quotation_detail(
    *,
    task_id: str,
    crawler: KaisiOnlineOrderCrawler,
    source: Dict[str, Any],
    latest: Dict[str, Any],
    status_payload: Dict[str, Any],
    manual_price_fill_enabled: bool,
    auto_submit_enabled: bool,
) -> bool:
    """启动前补拉报价单详情，并复用现有详情入库链路。"""

    # 优先使用开思最新报价单记录补齐详情采集所需字段，缺失时再回退到前端原始行。
    merged_row = {
        **(source or {}),
        **(latest or {}),
    }
    # 先调用现有采集器抓完整明细，避免重写另一套开思详情解析逻辑。
    detail = crawler.collect_quotation_records(merged_row)
    # 把采集结果组装成现有详情同步 payload，后端会复用统一入库逻辑写主表和明细表。
    detail_payload = build_quotation_payload(
        manual_price_fill_enabled=manual_price_fill_enabled,
        auto_submit_enabled=auto_submit_enabled,
        quotation=merged_row,
        detail=detail,
    )
    # 启动前详情同步要继承最新业务状态，避免外部已完成的报价单被误写回“待补价”。
    detail_payload["flowStatus"] = str(status_payload.get("flowStatus") or detail_payload.get("flowStatus") or "").strip()
    # 处理状态同样以状态同步结果为准，保证详情事件不会覆盖最终状态。
    detail_payload["processStatus"] = str(status_payload.get("processStatus") or detail_payload.get("processStatus") or "").strip()
    # 使用单独详情节点，方便前端和后端清楚区分“拉详情”和“改状态”两个动作。
    detail_payload["currentNodeCode"] = DETAIL_SYNC_NODE_CODE
    # 详情节点名称统一使用中文，保证日志 UTF-8 展示一致。
    detail_payload["currentNodeName"] = DETAIL_SYNC_NODE_NAME
    # 详情同步日志里明确带上明细数，用户可以直接判断这次有没有真正拉到详情。
    detail_payload["message"] = f"启动前同步详情：报价单明细已拉取，明细数={len(detail_payload.get('items') or [])}"
    # 把报价单详情事件先发给后端，写入主表和明细表后，再由状态事件落最终状态。
    report_online_order_quotation(task_id, detail_payload)
    flush_online_order_quotation(task_id)
    # 主线程日志补一条详情成功信息，便于快速判断这次同步是否真的拉了详情。
    report_log(
        task_id,
        (
            f"启动前同步报价单详情成功：报价单号={detail_payload.get('quotationId') or '-'}，"
            f"门店={detail_payload.get('storeId') or '-'}，"
            f"明细数={len(detail_payload.get('items') or [])}"
        ),
    )
    # 成功执行到这里说明详情事件已经发出。
    return True


def _normalize_rows(rows: Optional[Iterable[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """把前端传入的待同步报价单列表规整成统一结构。"""

    # 规整后的列表只保留状态同步真正需要的关键字段，减少路由与服务之间的耦合。
    normalized_rows: List[Dict[str, Any]] = []
    # 逐条清洗输入数据，过滤掉空对象和无效记录。
    for row in rows or []:
        # 非字典结构不是合法报价单记录，直接忽略。
        if not isinstance(row, dict):
            continue
        # 报价单号是同步结果回写时的主键之一，需要统一转成字符串。
        quotation_id = str(row.get("quotationId") or row.get("id") or "").strip()
        # 询价单号用于从开思列表查询最新状态，是状态同步的核心查询条件。
        inquiry_id = str(row.get("inquiryId") or "").strip()
        # 门店编号是另一半主键，也用于缩小开思查询结果范围。
        store_id = str(row.get("storeId") or "").strip()
        # 缺少报价单号和询价单号时没有同步价值，避免传入后续处理链路。
        if not quotation_id and not inquiry_id:
            continue
        # 把当前前端行上已有的业务状态字段也带上，方便同步消息保留上下文。
        normalized_rows.append(
            {
                "quotationId": quotation_id,
                "inquiryId": inquiry_id,
                "storeId": store_id,
                "statusId": str(row.get("statusId") or "").strip(),
                "statusIdDesc": str(row.get("statusIdDesc") or "").strip(),
                "displayModelName": str(row.get("displayModelName") or "").strip(),
            }
        )
    # 返回统一格式的待同步列表，供主同步流程直接消费。
    return normalized_rows


def _pick_latest_row(rows: Iterable[Dict[str, Any]], quotation_id: str, store_id: str) -> Dict[str, Any]:
    """从开思返回结果里挑选当前报价单最匹配的一条最新记录。"""

    # 先过滤掉空值和非字典项，避免排序和筛选过程中出现字段访问异常。
    candidates = [row for row in rows or [] if isinstance(row, dict)]
    # 候选为空时直接返回空对象，交由上层决定跳过。
    if not candidates:
        return {}

    # 优先按报价单号精确匹配，避免同一询价单下取错其他门店或其他报价单。
    normalized_quotation_id = str(quotation_id or "").strip()
    if normalized_quotation_id:
        matched = [
            row
            for row in candidates
            if str(row.get("id") or row.get("quotationId") or "").strip() == normalized_quotation_id
        ]
        if matched:
            candidates = matched

    # 报价单号仍不唯一时，再按门店编号精确收窄范围。
    normalized_store_id = str(store_id or "").strip()
    if normalized_store_id:
        matched = [row for row in candidates if str(row.get("storeId") or "").strip() == normalized_store_id]
        if matched:
            candidates = matched

    # 按开思更新时间倒序排序，确保取到最新的一条状态记录。
    candidates.sort(key=_row_sort_key, reverse=True)
    # 返回排序后的第一条作为最新状态。
    return candidates[0]


def _row_sort_key(row: Dict[str, Any]) -> tuple[int, int, str]:
    """生成开思报价单列表记录的排序键。"""

    # 更新时间戳优先级最高，用于优先选中真正最新的记录。
    updated_millis = _to_millis(row.get("lastUpdatedStamp"))
    # 创建时间作为第二排序位，处理更新时间缺失的情况。
    created_millis = _to_millis(row.get("createdStamp"))
    # 报价单号作为兜底排序位，保证排序结果稳定。
    quotation_id = str(row.get("id") or row.get("quotationId") or "").strip()
    # 返回元组供 list.sort 使用。
    return updated_millis, created_millis, quotation_id


def _to_millis(value: Any) -> int:
    """把开思列表中的秒级或毫秒级时间戳统一转成毫秒整数。"""

    # 空值直接按 0 处理，避免排序比较时报错。
    if value is None or value == "":
        return 0
    try:
        # 开思接口有时是字符串，有时是数字，这里统一转成整数。
        number = int(float(value))
        # 小于 13 位时视为秒级时间戳，补齐成毫秒后再参与排序。
        return number * 1000 if abs(number) < 100000000000 else number
    except Exception:
        # 异常值按 0 兜底即可，不阻断整批状态同步。
        return 0


def _build_status_payload(
    *,
    source: Dict[str, Any],
    latest: Dict[str, Any],
    manual_price_fill_enabled: bool,
    auto_submit_enabled: bool,
) -> Dict[str, Any]:
    """把开思最新状态转换为在线接单模块统一状态事件。"""

    # 优先使用开思返回的报价单号，不存在时回退到前端原始行数据。
    quotation_id = str(latest.get("id") or latest.get("quotationId") or source.get("quotationId") or "").strip()
    # 询价单号用于后端回写时补全记录上下文。
    inquiry_id = str(latest.get("inquiryId") or source.get("inquiryId") or "").strip()
    # 门店编号和报价单号一起构成在线接单主表唯一任务标识。
    store_id = str(latest.get("storeId") or source.get("storeId") or "").strip()
    # 开思原始业务状态编码一并透传，前端列表的业务状态列直接复用它展示中文。
    status_id = str(latest.get("statusId") or source.get("statusId") or "").strip()
    # 开思原始业务状态中文描述同样透传，便于表格直接展示真实业务状态。
    status_id_desc = str(latest.get("statusIdDesc") or source.get("statusIdDesc") or "").strip()
    # 车型名称优先使用最新开思数据，减少本地旧数据残留。
    display_model_name = str(latest.get("displayModelName") or source.get("displayModelName") or "").strip()
    # 认领人不为空通常说明这条报价单已经不属于当前待接单列表。
    quote_user_name = str(latest.get("quoteUserName") or "").strip()
    # 导航页签可以辅助判断当前报价单是否还在“未认领”列表里。
    nav_tab = str(latest.get("currentTab") or latest.get("navTab") or "").strip().upper()
    # 仅当报价单仍处于未认领未报价态时，才继续保留为待补价状态。
    is_pending = _is_pending_external_status_by_status_id(
        status_id=status_id,
        nav_tab=nav_tab,
        quote_user_name=quote_user_name,
    )

    # 外部仍待处理时回写内部待补价状态，保证它继续停留在“未完成”页签。
    flow_status = "WAIT_PRICE_FILL" if is_pending else "COMPLETED"
    # 外部已离开待接单列表时视为本地同步完成，从“未完成”页签移到“已完成”页签。
    process_status = "PROCESSING" if is_pending else "SUCCESS"
    # 当前节点编码和名称保持和内部流程节点一致，便于前端表格和日志统一展示。
    current_node_code = "WAIT_PRICE_FILL" if is_pending else "COMPLETED"
    current_node_name = "待补价" if is_pending else "已完成"
    # 消息里优先展示开思原始业务状态中文，用户可以直接看到同步后的真实状态。
    latest_status_text = status_id_desc or status_id or ("未认领" if is_pending else "已完成")
    # 认领人存在时一并回显到消息，便于用户知道这条单据为什么被移出未完成页签。
    claimant_text = f"，认领人={quote_user_name}" if quote_user_name else ""
    # 最终消息统一写中文 UTF-8，后端执行日志和前端 websocket 都直接复用。
    message = f"启动前同步状态：当前业务状态={latest_status_text}{claimant_text}"

    # 返回统一结构的状态事件载荷，交由后端统一落主表和执行日志。
    return {
        "platform": "kaisi",
        "scene": "online_order",
        "kaisiScene": "online_order",
        "onlineOrderScene": "online_order",
        "manualPriceFillEnabled": manual_price_fill_enabled,
        "autoSubmitEnabled": auto_submit_enabled,
        "quotationId": quotation_id,
        "inquiryId": inquiry_id,
        "storeId": store_id,
        "statusId": status_id,
        "statusIdDesc": status_id_desc,
        "displayModelName": display_model_name,
        "flowStatus": flow_status,
        "processStatus": process_status,
        "currentNodeCode": current_node_code,
        "currentNodeName": current_node_name,
        "message": message,
        "syncNodeCode": SYNC_NODE_CODE,
        "syncNodeName": SYNC_NODE_NAME,
        "quoteUserName": quote_user_name or None,
        "rawNavTab": nav_tab or None,
        "errorMessage": None,
    }


def _is_pending_external_status_by_status_id(*, status_id: str, nav_tab: str, quote_user_name: str) -> bool:
    """Treat a quotation as completed only when statusId is QUOTE."""

    normalized_status_id = str(status_id or "").strip().upper()
    _ = nav_tab
    _ = quote_user_name
    return normalized_status_id != "QUOTE"
