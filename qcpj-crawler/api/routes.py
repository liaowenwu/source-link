from uuid import uuid4

import requests
from flask import jsonify, request

from config import DEFAULT_PLATFORM
from core.task_queue import (
    create_task_record,
    enqueue_task,
    get_task,
    request_task_terminate,
    set_task_paused,
    task_queue,
)
from platforms.kaisi.online_order.runtime import (
    enqueue_online_order_price_fill,
    enqueue_online_order_submit,
    get_online_order_runtime_status,
    start_online_order_runtime,
    stop_online_order_runtime,
)
from platforms.kaisi.online_order.pending_status_sync import sync_pending_quotation_statuses
from service.backend_client import create_backend_task
from service.reporter import (
    register_task_context,
    report_control,
    report_log,
    ws_status,
)


# 规范化逗号分隔文本。
def _normalize_csv_text(value):
    if isinstance(value, list):
        parts = [str(item).strip() for item in value if str(item).strip()]
        return ",".join(parts)
    if isinstance(value, str):
        parts = [item.strip() for item in value.split(",") if item.strip()]
        return ",".join(parts)
    return ""


# 规范化凯思场景值。
def _normalize_kaisi_scene(value):
    text = str(value or "").strip().lower()
    if text in ("online", "online-order", "online_order", "在线接单", "接单"):
        return "online_order"
    if text in ("history", "historical", "history_quote", "历史报价", "历史"):
        return "history"
    return ""


# 解析业务类型。
def _resolve_biz_type(platform, task_type, kaisi_scene, biz_type):
    text = str(biz_type or "").strip()
    if text:
        return text.upper()

    if platform == "kaisi":
        return "KAISI_ONLINE_ORDER" if kaisi_scene == "online_order" else "KAISI_HISTORY_QUOTE"
    if platform in ("benben", "robot"):
        return "PRODUCT_SYNC"
    return "GENERIC_SYNC"


# 规范化请求载荷。
def _normalize_request_payload(data):
    payload = data or {}
    mode = (payload.get("mode") or payload.get("taskType") or "single").strip().lower()
    task_type = "batch" if mode == "batch" else "single"
    platform = (payload.get("platform") or DEFAULT_PLATFORM).strip().lower() or DEFAULT_PLATFORM
    kaisi_scene = (
        _normalize_kaisi_scene(payload.get("kaisiScene"))
        or _normalize_kaisi_scene(payload.get("kaisiJobType"))
        or _normalize_kaisi_scene(payload.get("scene"))
        or _normalize_kaisi_scene(payload.get("bizType"))
    )

    sku = (payload.get("sku") or "").strip()
    skus = payload.get("skus") or []
    city = (payload.get("city") or "").strip()
    quality_codes = _normalize_csv_text(payload.get("qualityCodes"))
    supplier_id = _normalize_csv_text(payload.get("supplierId"))
    brand_names = _normalize_csv_text(payload.get("brandNames"))
    pricing_match_strategy = payload.get("pricingMatchStrategy") or payload.get("matchStrategy") or {}
    benben_config = payload.get("benbenConfig") or payload.get("crawlerConfig") or {}
    online_order_item_map = payload.get("onlineOrderItemMap") or {}
    online_order_item_meta_map = payload.get("onlineOrderItemMetaMap") or {}
    suppliers_raw = payload.get("suppliers")
    if isinstance(suppliers_raw, str):
        suppliers = [item.strip() for item in suppliers_raw.split(",") if item and item.strip()]
    elif isinstance(suppliers_raw, list):
        suppliers = [str(item).strip() for item in suppliers_raw if str(item).strip()]
    else:
        suppliers = []

    if platform == "kaisi":
        total_count = 1
    elif task_type == "single":
        total_count = 1 if sku else 0
    else:
        total_count = len([item for item in skus if (item or "").strip()])
    biz_type = _resolve_biz_type(platform, task_type, kaisi_scene, payload.get("bizType") or payload.get("businessType"))
    task_params = payload.get("taskParams")
    task_params = dict(task_params) if isinstance(task_params, dict) else {}

    scene = (
        str(payload.get("scene") or "").strip()
        or str(payload.get("onlineOrderScene") or "").strip()
        or (kaisi_scene if platform == "kaisi" else "")
    )

    task_params.update({
        "platform": platform,
        "mode": task_type,
        "scene": scene,
        "kaisiScene": kaisi_scene if platform == "kaisi" else "",
        "onlineOrderScene": scene,
        "sku": sku,
        "skus": skus,
        "city": city,
        "suppliers": suppliers,
        "qualityCodes": quality_codes,
        "supplierId": supplier_id,
        "brandNames": brand_names,
        "benbenConfig": benben_config,
        "pricingMatchStrategy": pricing_match_strategy,
        "onlineOrderItemMap": online_order_item_map,
        "onlineOrderItemMetaMap": online_order_item_meta_map,
        "enableBenbenPriceFill": payload.get("enableBenbenPriceFill"),
        "autoSubmit": payload.get("autoSubmit"),
    })

    return {
        **payload,
        "mode": task_type,
        "taskType": task_type,
        "bizType": biz_type,
        "taskParams": task_params,
        "triggerBy": payload.get("triggerBy") or "frontend",
        "totalCount": payload.get("totalCount") or total_count,
        "platform": platform,
        "sku": sku,
        "skus": skus,
        "city": city,
        "qualityCodes": quality_codes,
        "supplierId": supplier_id,
        "brandNames": brand_names,
        "benbenConfig": benben_config,
        "pricingMatchStrategy": pricing_match_strategy,
        "onlineOrderItemMap": online_order_item_map,
        "onlineOrderItemMetaMap": online_order_item_meta_map,
        "suppliers": suppliers,
        "kaisiScene": kaisi_scene if platform == "kaisi" else "",
        "scene": scene,
    }


# 处理普通标准化任务。
def _enqueue_normalized_task(app, data):
    scene = str(data.get("scene") or "").strip().lower()
    is_online_order_flow = scene in {"online_order", "online_order_auto_fill"} or str(data.get("kaisiScene") or "").strip().lower() == "online_order"
    if is_online_order_flow:
        task_id = f"ONLINE-{uuid4().hex[:16].upper()}"
    else:
        try:
            task_id = create_backend_task(
                task_type=data["taskType"],
                trigger_by=data["triggerBy"],
                total_count=int(data["totalCount"] or 0),
                sku=data.get("sku") or "",
                skus=data.get("skus") or [],
                biz_type=data.get("bizType") or "",
                task_params=data.get("taskParams"),
            )
        except requests.RequestException as exc:
            app.logger.exception("创建后端任务失败")
            return jsonify({
                "error": "创建后端任务失败",
                "message": str(exc),
            }), 502

    register_task_context(task_id, {
        "taskType": data.get("taskType"),
        "triggerBy": data.get("triggerBy"),
        "totalCount": int(data.get("totalCount") or 0),
        "bizType": data.get("bizType"),
        "platform": data.get("platform"),
        "mode": data.get("mode"),
        "scene": data.get("scene"),
        "kaisiScene": data.get("kaisiScene"),
        "onlineOrderScene": data.get("scene"),
        "enableBenbenPriceFill": (data.get("taskParams") or {}).get("enableBenbenPriceFill"),
        "autoSubmit": (data.get("taskParams") or {}).get("autoSubmit"),
    })

    try:
        report_log(
            task_id,
            (
                f"任务已入队：平台={data.get('platform')}，模式={data.get('mode')}，"
                f"业务类型={data.get('bizType')}，"
                f"凯思场景={data.get('kaisiScene')}，"
                f"SKU={data.get('sku')}，批量 SKU={data.get('skus')}，"
                f"城市={data.get('city')}，供应商={data.get('suppliers')}，"
                f"品质编码={data.get('qualityCodes')}，"
                f"供应商 ID={data.get('supplierId')}，品牌={data.get('brandNames')}"
            ),
        )
    except Exception:
        pass

    create_task_record(task_id, data)
    enqueue_task(task_id, data)

    return jsonify({
        "taskId": task_id,
        "taskNo": task_id,
        "status": "queued",
        "queueSize": task_queue.qsize(),
    })


# 处理通用终止任务请求。
def _terminate_task(task_id: str):
    record = request_task_terminate(task_id)
    try:
        report_log(task_id, "收到终止任务指令", level="WARNING")
        report_control(task_id, "TERMINATE", "收到终止任务指令")
    except Exception:
        pass
    return jsonify({
        "taskId": task_id,
        "taskNo": task_id,
        "terminateRequested": bool(record.get("terminateRequested")),
        "status": record.get("status"),
    })


# 注册所有 HTTP 路由。
def register_routes(app):
    @app.route("/run", methods=["POST"])
    def run_task():
        data = _normalize_request_payload(request.json)
        return _enqueue_normalized_task(app, data)

    @app.route("/kaisi/online/start", methods=["POST"])
    def start_kaisi_online_order():
        payload = request.json or {}
        data = _normalize_request_payload({
            **payload,
            "platform": "kaisi",
            "kaisiScene": "online_order",
            "mode": "single",
            "taskType": "single",
            "totalCount": 1,
            "triggerBy": payload.get("triggerBy") or "online-order",
        })
        try:
            # 在线接单启动入口要先创建后端 sync_task，后续主线程日志和状态都围绕这个 taskNo 追踪。
            backend_task_no = create_backend_task(
                task_type=data["taskType"],
                trigger_by=data["triggerBy"],
                total_count=int(data["totalCount"] or 1),
                sku=data.get("sku") or "",
                skus=data.get("skus") or [],
                biz_type=data.get("bizType") or "",
                task_params=data.get("taskParams"),
            )
        except requests.RequestException as exc:
            app.logger.exception("创建在线接单后端主任务失败")
            return jsonify({
                "error": "创建在线接单后端主任务失败",
                "message": str(exc),
            }), 502
        # 把后端主任务号提前塞入运行时参数，start_online_order_runtime 只负责消费，不再临时生成。
        data["backendTaskNo"] = backend_task_no
        data["taskId"] = backend_task_no
        data["taskNo"] = backend_task_no
        # 启动前先把前端传入的待同步报价单数量记入主线程日志，便于排查是否真的把列表传到了 Flask。
        report_log(
            backend_task_no,
            f"启动前收到待同步报价单数量={len(data.get('pendingQuotations') or [])}",
        )
        pending_sync_summary = sync_pending_quotation_statuses(
            task_id=backend_task_no,
            quotations=data.get("pendingQuotations") or [],
            manual_price_fill_enabled=bool(data.get("manualPriceFillEnabled", True)),
            auto_submit_enabled=bool(data.get("autoSubmitEnabled", False)),
        )
        runtime_status = start_online_order_runtime(data)
        return jsonify({
            **runtime_status,
            "taskId": runtime_status.get("taskId") or backend_task_no,
            "taskNo": runtime_status.get("taskNo") or backend_task_no,
            "pendingSyncSummary": pending_sync_summary,
        })

    @app.route("/kaisi/online/status", methods=["GET"])
    def kaisi_online_status():
        return jsonify(get_online_order_runtime_status())

    @app.route("/kaisi/online/stop", methods=["POST"])
    def stop_kaisi_online_order():
        return jsonify(stop_online_order_runtime(reason="收到停止在线接单指令"))

    @app.route("/kaisi/online/price-fill", methods=["POST"])
    def kaisi_online_price_fill():
        data = request.json or {}
        task_id = (data.get("taskId") or data.get("taskNo") or "").strip()
        try:
            result = enqueue_online_order_price_fill(
                data.get("quotations") or data.get("items") or [],
                task_id=task_id,
            )
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 404
        return jsonify({
            "code": 0,
            "message": "补价任务已入队",
            "data": result,
        })

    @app.route("/kaisi/online/submit", methods=["POST"])
    def kaisi_online_submit():
        data = request.json or {}
        task_id = (data.get("taskId") or data.get("taskNo") or "").strip()
        try:
            result = enqueue_online_order_submit(
                data.get("quotations") or data.get("items") or [],
                task_id=task_id,
            )
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 404
        return jsonify({
            "code": 0,
            "message": "提交任务已入队",
            "data": result,
        })

    @app.route("/kaisi/submit", methods=["POST"])
    def kaisi_submit_alias():
        return kaisi_online_submit()

    @app.route("/task/pause", methods=["POST"])
    def pause_task():
        data = request.json or {}
        task_id = (data.get("taskId") or data.get("taskNo") or "").strip()
        if not task_id:
            return jsonify({"error": "缺少 taskId"}), 400

        paused = bool(data.get("paused", True))
        record = set_task_paused(task_id, paused)
        try:
            report_log(task_id, "任务已暂停" if paused else "任务已继续")
            report_control(task_id, "PAUSE" if paused else "RESUME", "任务已暂停" if paused else "任务已继续")
        except Exception:
            pass
        return jsonify({
            "taskId": task_id,
            "taskNo": task_id,
            "paused": bool(record.get("paused")),
            "status": record.get("status"),
        })

    @app.route("/task/terminate", methods=["POST"])
    def terminate_task():
        data = request.json or {}
        task_id = (data.get("taskId") or data.get("taskNo") or "").strip()
        if not task_id:
            return jsonify({"error": "缺少 taskId"}), 400
        return _terminate_task(task_id)

    @app.route("/task/<task_id>", methods=["GET"])
    def task_status(task_id):
        task_id = str(task_id or "").strip()
        if not task_id:
            return jsonify({"error": "缺少 taskId"}), 400
        runtime_status = get_online_order_runtime_status(task_id)
        if runtime_status.get("status") != "NOT_FOUND":
            return jsonify(runtime_status)
        record = get_task(task_id)
        if not record:
            return jsonify({
                "error": "任务不存在",
                "taskId": task_id,
                "taskNo": task_id,
            }), 404
        payload = record.get("payload") or {}
        return jsonify({
            "taskId": task_id,
            "taskNo": task_id,
            "status": record.get("status"),
            "paused": bool(record.get("paused")),
            "terminateRequested": bool(record.get("terminateRequested")),
            "error": record.get("error"),
            "scene": payload.get("scene") or payload.get("kaisiScene") or "",
        })

    @app.route("/ws/status", methods=["GET"])
    def websocket_status():
        status = ws_status(reconnect=True)
        return jsonify({
            "serviceUp": True,
            "wsConnected": bool(status.get("connected")),
            "error": status.get("error") or "",
        })
