from __future__ import annotations

import argparse
import copy
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.parse import parse_qs, urlparse

SCRIPT_DIR = Path(__file__).resolve().parent
CRAWLER_ROOT = SCRIPT_DIR.parent
REPO_ROOT = CRAWLER_ROOT.parent
if str(CRAWLER_ROOT) not in sys.path:
    sys.path.insert(0, str(CRAWLER_ROOT))

import requests

from config import BACKEND_BASE_URL, BACKEND_LOGIN_URL, BACKEND_PASSWORD, BACKEND_USERNAME
from core.browser import Browser
from platforms.benben.auth import BenbenAuthManager
from platforms.benben.crawler import BenbenCrawler
from platforms.kaisi.online_order.auto_fill import (
    AUTO_FILL_SCENE,
    build_report_payloads,
    normalize_benben_config,
    normalize_match_strategy,
)
from platforms.kaisi.online_order.query_param_support import (
    build_crawler_query_param_map,
    filter_and_apply_markup,
    normalize_text_list,
    resolve_quality_origin_ids,
    resolve_region_origin_ids,
    resolve_supplier_ids,
)
from platforms.kaisi.online_order.auto_fill_selector import (
    normalize_candidate,
    select_candidate,
    sort_candidates_for_display,
)
from platforms.kaisi.online_order.quality_support import collect_quality_origin_ids, resolve_item_quality
from platforms.kaisi.online_order.runtime_payloads import apply_auto_fill_result
from service.backend_client import (
    create_backend_task,
    get_backend_crawler_config,
    get_backend_online_order_crawler_query_params,
)
from service.reporter import register_task_context, report_done, report_error, report_task_start


def log(message: str) -> None:
    print(message, flush=True)


def normalize_ids(values: Sequence[str]) -> List[str]:
    result: List[str] = []
    seen = set()
    for value in values:
        for part in str(value or "").split(","):
            text = part.strip()
            if not text or text in seen:
                continue
            seen.add(text)
            result.append(text)
    return result


def safe_identifier(value: str) -> str:
    text = str(value or "").strip()
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", text):
        raise ValueError(f"Unsafe SQL identifier: {value}")
    return text


def read_backend_yml() -> str:
    path = REPO_ROOT / "backend" / "src" / "main" / "resources" / "application.yml"
    return path.read_text(encoding="utf-8") if path.exists() else ""


def yml_value(text: str, key: str) -> str:
    match = re.search(rf"^\s*{re.escape(key)}:\s*(.+?)\s*$", text, re.MULTILINE)
    if not match:
        return ""
    value = match.group(1).strip()
    if value.startswith(("'", '"')) and value.endswith(("'", '"')):
        return value[1:-1]
    return value


@dataclass
class DbConfig:
    host: str
    port: int
    dbname: str
    user: str
    password: str
    schema: str


def parse_jdbc_url(jdbc_url: str) -> Tuple[str, int, str, str]:
    if not jdbc_url.startswith("jdbc:postgresql://"):
        raise ValueError(f"Unsupported datasource url: {jdbc_url}")
    parsed = urlparse(jdbc_url[len("jdbc:"):])
    query = parse_qs(parsed.query)
    return (
        parsed.hostname or "localhost",
        int(parsed.port or 5432),
        parsed.path.lstrip("/") or "postgres",
        (query.get("currentSchema") or ["public"])[0] or "public",
    )


def load_db_config() -> DbConfig:
    app_yml = read_backend_yml()
    jdbc_url = os.getenv("ONLINE_ORDER_DB_JDBC_URL") or yml_value(app_yml, "url")
    username = os.getenv("ONLINE_ORDER_DB_USERNAME") or yml_value(app_yml, "username")
    password = os.getenv("ONLINE_ORDER_DB_PASSWORD") or yml_value(app_yml, "password")
    if not jdbc_url:
        raise RuntimeError("Cannot resolve PostgreSQL datasource url")
    host, port, dbname, schema = parse_jdbc_url(jdbc_url)
    return DbConfig(
        host=os.getenv("ONLINE_ORDER_DB_HOST") or host,
        port=int(os.getenv("ONLINE_ORDER_DB_PORT") or port),
        dbname=os.getenv("ONLINE_ORDER_DB_NAME") or dbname,
        user=os.getenv("ONLINE_ORDER_DB_USERNAME") or username,
        password=os.getenv("ONLINE_ORDER_DB_PASSWORD") or password,
        schema=os.getenv("ONLINE_ORDER_DB_SCHEMA") or schema,
    )


class PostgresAccessor:
    def __init__(self, config: DbConfig) -> None:
        self.config = config
        self.conn = None
        self.extras = None

    def __enter__(self) -> "PostgresAccessor":
        try:
            import psycopg2
            import psycopg2.extras
        except ImportError as exc:
            raise RuntimeError("psycopg2 is required for this tool") from exc
        self.conn = psycopg2.connect(
            host=self.config.host,
            port=self.config.port,
            dbname=self.config.dbname,
            user=self.config.user,
            password=self.config.password,
        )
        self.conn.autocommit = True
        self.extras = psycopg2.extras
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.conn is not None:
            self.conn.close()

    def table(self, table_name: str) -> str:
        return f"{safe_identifier(self.config.schema)}.{safe_identifier(table_name)}"

    def query(self, sql: str, params: Sequence[Any]) -> List[Dict[str, Any]]:
        if self.conn is None or self.extras is None:
            raise RuntimeError("Database connection is not initialized")
        with self.conn.cursor(cursor_factory=self.extras.RealDictCursor) as cursor:
            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]

    def quotations(self, quotation_ids: Sequence[str]) -> List[Dict[str, Any]]:
        return self.query(
            f"""
            select
              quotation_id, inquiry_id, store_id, supplier_company_id,
              status_id, status_id_desc, item_count, created_stamp, last_updated_stamp,
              display_model_name, flow_status, process_status, current_node_code,
              current_node_name, manual_price_fill_enabled, auto_submit_enabled,
              cast(raw_payload as text) as raw_payload_text
            from {self.table("online_order_kaisi_quotation")}
            where quotation_id = any(%s)
            order by quotation_id asc, store_id asc
            """,
            (list(quotation_ids),),
        )

    def quote_items(self, quotation_ids: Sequence[str]) -> List[Dict[str, Any]]:
        return self.query(
            f"""
            select
              id, quotation_id, inquiry_id, store_id, resolve_result_id, quoted_price_item_id,
              parts_num, parts_name, parts_brand_quality, brand_id, brand_name, quantity,
              price, bt_price, seller_price, seller_bt_price, arrival_time, seller_status,
              source, remark, cast(raw_payload as text) as raw_payload_text
            from {self.table("online_order_kaisi_quote_item")}
            where quotation_id = any(%s)
            order by quotation_id asc, store_id asc, id asc
            """,
            (list(quotation_ids),),
        )

    def quality_dict(self) -> List[Dict[str, Any]]:
        return self.query(
            f"""
            select quality_code, quality_name, quality_origin_id
            from {self.table("kaisi_quality_dict")}
            order by order_num asc, id asc
            """,
            (),
        )


def json_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    text = str(value or "").strip()
    if not text:
        return {}
    try:
        data = json.loads(text)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def builtin(value: Any) -> Any:
    return float(value) if isinstance(value, Decimal) else value


def to_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    return default


def build_quality_maps(rows: Iterable[Dict[str, Any]]) -> Dict[str, Dict[str, Dict[str, str]]]:
    by_code: Dict[str, Dict[str, str]] = {}
    by_name: Dict[str, Dict[str, str]] = {}
    for row in rows:
        code = str(row.get("quality_code") or "").strip()
        name = str(row.get("quality_name") or "").strip()
        origin_id = str(row.get("quality_origin_id") or code).strip()
        payload = {"qualityCode": code, "qualityName": name, "qualityOriginId": origin_id}
        if code:
            by_code[code] = payload
        if name:
            by_name[name] = payload
    return {"by_code": by_code, "by_name": by_name}


def normalize_quotation(row: Dict[str, Any]) -> Dict[str, Any]:
    raw = json_dict(row.get("raw_payload_text"))
    quotation_id = str(row.get("quotation_id") or "").strip()
    return {
        "id": quotation_id,
        "quotationId": quotation_id,
        "inquiryId": str(row.get("inquiry_id") or raw.get("inquiryId") or "").strip(),
        "storeId": str(row.get("store_id") or raw.get("storeId") or "").strip(),
        "supplierCompanyId": str(row.get("supplier_company_id") or raw.get("supplierCompanyId") or "").strip(),
        "statusId": str(row.get("status_id") or raw.get("statusId") or "").strip(),
        "statusIdDesc": str(row.get("status_id_desc") or raw.get("statusIdDesc") or "").strip(),
        "displayModelName": str(row.get("display_model_name") or raw.get("displayModelName") or "").strip(),
        "itemCount": builtin(row.get("item_count")),
        "createdStamp": builtin(row.get("created_stamp")),
        "lastUpdatedStamp": builtin(row.get("last_updated_stamp")),
        "manualPriceFillEnabled": to_bool(row.get("manual_price_fill_enabled"), True),
        "autoSubmitEnabled": to_bool(row.get("auto_submit_enabled"), False),
    }


def normalize_item(row: Dict[str, Any], quality_maps: Dict[str, Dict[str, Dict[str, str]]]) -> Dict[str, Any]:
    raw = json_dict(row.get("raw_payload_text"))
    parts_brand_quality = str(row.get("parts_brand_quality") or "").strip()
    normalized_quality = resolve_item_quality(
        {
            "partsBrandQuality": parts_brand_quality,
            "qualityCode": raw.get("qualityCode"),
            "qualityName": raw.get("qualityName"),
            "qualityOriginId": raw.get("qualityOriginId"),
            "rawPayload": raw,
        },
        quality_maps,
    )
    return {
        "itemId": builtin(row.get("id")),
        "id": builtin(row.get("id")),
        "quotationId": str(row.get("quotation_id") or "").strip(),
        "inquiryId": str(row.get("inquiry_id") or raw.get("inquiryId") or "").strip(),
        "storeId": str(row.get("store_id") or "").strip(),
        "resolveResultId": str(row.get("resolve_result_id") or raw.get("resolveResultId") or "").strip(),
        "quotedPriceItemId": str(row.get("quoted_price_item_id") or "").strip(),
        "partsNum": str(row.get("parts_num") or raw.get("partsNum") or "").strip(),
        "partsName": str(row.get("parts_name") or raw.get("partsName") or "").strip(),
        "partsBrandQuality": parts_brand_quality,
        "brandId": str(row.get("brand_id") or raw.get("brandId") or "").strip(),
        "brandName": str(row.get("brand_name") or raw.get("brandName") or "").strip(),
        "quantity": builtin(row.get("quantity")),
        "price": builtin(row.get("price")),
        "btPrice": builtin(row.get("bt_price")),
        "sellerPrice": builtin(row.get("seller_price")),
        "sellerBtPrice": builtin(row.get("seller_bt_price")),
        "arrivalTime": builtin(row.get("arrival_time")),
        "sellerStatus": str(row.get("seller_status") or "").strip(),
        "source": str(row.get("source") or raw.get("source") or "").strip(),
        "remark": str(row.get("remark") or raw.get("remark") or "").strip(),
        "qualityCode": str(normalized_quality.get("qualityCode") or "").strip(),
        "qualityName": str(normalized_quality.get("qualityName") or "").strip(),
        "qualityOriginId": str(normalized_quality.get("qualityOriginId") or "").strip(),
    }


def group_items(items: Iterable[Dict[str, Any]]) -> Dict[Tuple[str, str], List[Dict[str, Any]]]:
    grouped: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    for item in items:
        key = (str(item.get("quotationId") or "").strip(), str(item.get("storeId") or "").strip())
        grouped.setdefault(key, []).append(item)
    return grouped


def has_price(item: Dict[str, Any]) -> bool:
    return item.get("price") is not None or item.get("btPrice") is not None


class BackendApiClient:
    def __init__(self) -> None:
        self.base_url = BACKEND_BASE_URL.rstrip("/")
        self.login_url = BACKEND_LOGIN_URL
        self.username = BACKEND_USERNAME
        self.password = BACKEND_PASSWORD
        self.token = ""

    def login(self) -> None:
        response = requests.post(self.login_url, json={"username": self.username, "password": self.password}, timeout=(3, 8))
        response.raise_for_status()
        body = response.json() or {}
        token = (body.get("data") or {}).get("accessToken")
        if not token:
            raise RuntimeError(f"Backend login did not return accessToken: {body}")
        self.token = token

    def post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.token:
            self.login()
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(f"{self.base_url}{path}", json=payload, headers=headers, timeout=(3, 8))
        if response.status_code in (401, 403):
            self.login()
            headers["Authorization"] = f"Bearer {self.token}"
            response = requests.post(f"{self.base_url}{path}", json=payload, headers=headers, timeout=(3, 8))
        response.raise_for_status()
        return response.json() if response.content else {}


def task_id(prefix: str) -> str:
    return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}"


def run_sync(args: argparse.Namespace, quotations: List[Dict[str, Any]]) -> Dict[str, Any]:
    try:
        from platforms.kaisi.online_order.pending_status_sync import sync_pending_quotation_statuses
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            f"sync mode is missing dependency: {exc.name}. Install qcpj-crawler requirements first."
        ) from exc

    sync_task_id = args.task_id or create_backend_task(
        task_type="batch" if len(quotations) > 1 else "single",
        trigger_by="online-order-debug-tool",
        total_count=max(len(quotations), 1),
        biz_type="KAISI_ONLINE_ORDER",
        task_params={"scene": "online_order", "kaisiScene": "online_order"},
    )
    register_task_context(
        sync_task_id,
        {
            "platform": "kaisi",
            "scene": "online_order",
            "kaisiScene": "online_order",
            "manualPriceFillEnabled": bool(args.manual_price_fill_enabled),
            "autoSubmitEnabled": bool(args.auto_submit_enabled),
            "totalCount": len(quotations),
        },
    )
    log(f"[sync] taskNo={sync_task_id}, quotationCount={len(quotations)}")
    report_task_start(
        sync_task_id,
        "batch" if len(quotations) > 1 else "single",
        "online-order-debug-tool",
        max(len(quotations), 1),
    )
    try:
        summary = sync_pending_quotation_statuses(
            task_id=sync_task_id,
            quotations=quotations,
            manual_price_fill_enabled=bool(args.manual_price_fill_enabled),
            auto_submit_enabled=bool(args.auto_submit_enabled),
        )
        fail_count = int(summary.get("failedCount") or 0) + int(summary.get("detailFailedCount") or 0)
        report_done(
            sync_task_id,
            int(summary.get("syncedCount") or 0),
            fail_count,
            int(summary.get("requestedCount") or len(quotations) or 1),
            (
                "报价单同步完成: "
                f"状态成功={int(summary.get('syncedCount') or 0)}, "
                f"详情成功={int(summary.get('detailSyncedCount') or 0)}, "
                f"跳过={int(summary.get('skippedCount') or 0)}, "
                f"失败={fail_count}"
            ),
        )
        return {"taskId": sync_task_id, "summary": summary}
    except Exception as exc:
        report_error(sync_task_id, str(exc))
        report_done(sync_task_id, 0, max(len(quotations), 1), max(len(quotations), 1), f"报价单同步异常: {exc}")
        raise


def json_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text or None
    try:
        return json.dumps(value, ensure_ascii=False)
    except Exception:
        text = str(value).strip()
        return text or None


def build_snapshot_candidates(
    item: Dict[str, Any],
    sku_records: List[Dict[str, Any]],
    match_strategy: Dict[str, Any],
) -> List[Dict[str, Any]]:
    normalized_candidates = [normalize_candidate(record, match_strategy) for record in (sku_records or [])]
    normalized_candidates = [record for record in normalized_candidates if record]
    return sort_candidates_for_display(normalized_candidates, match_strategy)


def build_snapshot_save_request(
    item: Dict[str, Any],
    candidate: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    if not candidate:
        return None

    raw_payload = candidate.get("rawPayload")
    if isinstance(raw_payload, dict):
        merged_raw_payload = dict(raw_payload)
    elif isinstance(raw_payload, str):
        try:
            parsed = json.loads(raw_payload)
            merged_raw_payload = dict(parsed) if isinstance(parsed, dict) else {}
        except Exception:
            merged_raw_payload = {}
    else:
        merged_raw_payload = {}

    merged_raw_payload.update(
        {
            "sku": str(candidate.get("sku") or item.get("partsNum") or ""),
            "productName": str(candidate.get("productName") or item.get("partsName") or ""),
            "brandName": str(candidate.get("brandName") or ""),
            "brandOriginId": str(candidate.get("brandOriginId") or ""),
            "qualityName": str(candidate.get("qualityName") or item.get("qualityName") or ""),
            "qualityOriginId": str(candidate.get("qualityOriginId") or item.get("qualityOriginId") or ""),
            "regionName": str(candidate.get("regionName") or ""),
            "regionOriginId": str(candidate.get("regionOriginId") or ""),
            "companyName": str(candidate.get("companyName") or ""),
            "supplierName": str(candidate.get("supplierName") or ""),
            "supplierId": str(candidate.get("supplierId") or ""),
            "stock": candidate.get("stock"),
            "price": candidate.get("price"),
            "transferDays": candidate.get("transferDays"),
        }
    )

    return {
        "sku": str(candidate.get("sku") or item.get("partsNum") or ""),
        "productName": str(candidate.get("productName") or item.get("partsName") or ""),
        "brand": str(candidate.get("brandName") or ""),
        "brandOriginId": str(candidate.get("brandOriginId") or ""),
        "qualityName": str(candidate.get("qualityName") or item.get("qualityName") or ""),
        "qualityOriginId": str(candidate.get("qualityOriginId") or item.get("qualityOriginId") or ""),
        "region": str(candidate.get("regionName") or ""),
        "regionOriginId": str(candidate.get("regionOriginId") or ""),
        "companyName": str(candidate.get("companyName") or ""),
        "supplierName": str(candidate.get("supplierName") or ""),
        "supplierId": str(candidate.get("supplierId") or ""),
        "stock": candidate.get("stock"),
        "price": candidate.get("price"),
        "transferDays": candidate.get("transferDays"),
        "rawPayload": json_text(merged_raw_payload),
    }


def build_snapshot_batch_item(
    item: Dict[str, Any],
    sku_records: List[Dict[str, Any]],
    match_strategy: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    quote_item_id = item.get("itemId")
    if quote_item_id is None:
        return None

    candidates = build_snapshot_candidates(item, sku_records, match_strategy)
    matched_snapshot = build_snapshot_save_request(item, select_candidate(candidates, match_strategy, item))
    snapshots = [build_snapshot_save_request(item, candidate) for candidate in candidates]
    snapshots = [snapshot for snapshot in snapshots if snapshot]
    return {
        "quoteItemId": int(quote_item_id),
        "matchedSnapshot": matched_snapshot,
        "snapshots": snapshots,
    }


def run_auto_fill(args: argparse.Namespace, quotations: List[Dict[str, Any]], items_by_key: Dict[Tuple[str, str], List[Dict[str, Any]]]) -> Dict[str, Any]:
    benben_config = normalize_benben_config(get_backend_crawler_config())
    strategy_override = {}
    if args.match_strategy_file:
        strategy_override = json.loads(Path(args.match_strategy_file).read_text(encoding="utf-8"))
    elif args.match_strategy_json:
        strategy_override = json.loads(args.match_strategy_json)
    match_strategy = normalize_match_strategy(strategy_override, benben_config)
    fill_task_id = args.task_id or task_id("AUTOFILL")

    contexts: List[Dict[str, Any]] = []
    unique_skus: List[str] = []
    seen_skus = set()
    sku_quality_origin_ids_map: Dict[str, List[str]] = {}
    for quotation in quotations:
        key = (quotation["quotationId"], quotation["storeId"])
        context_row = {**quotation, "items": copy.deepcopy(items_by_key.get(key, []))}
        context_row["itemCount"] = len(context_row["items"])
        contexts.append(context_row)
        for item in context_row["items"]:
            if has_price(item):
                continue
            sku = str(item.get("partsNum") or "").replace(" ", "")
            if sku and sku not in seen_skus:
                seen_skus.add(sku)
                unique_skus.append(sku)
            if sku:
                sku_quality_origin_ids_map.setdefault(sku, [])
                for quality_origin_id in collect_quality_origin_ids([item]):
                    if quality_origin_id not in sku_quality_origin_ids_map[sku]:
                        sku_quality_origin_ids_map[sku].append(quality_origin_id)

    if not unique_skus:
        return {
            "taskId": fill_task_id,
            "benbenConfig": benben_config,
            "matchStrategy": match_strategy,
            "quotationResults": [
                {
                    "quotationId": str(context_row.get("quotationId") or "").strip(),
                    "storeId": str(context_row.get("storeId") or "").strip(),
                    "totalItemCount": len(context_row.get("items") or []),
                    "targetItemCount": 0,
                    "matchedItemCount": 0,
                    "snapshotItemCount": 0,
                    "writeBackCount": 0,
                    "writeBackErrors": [],
                    "priceSnapshotRequest": {"storeId": str(context_row.get("storeId") or "").strip() or None, "items": []},
                    "writeBackResponse": None,
                    "payloads": [],
                    "updatedItems": context_row.get("items") or [],
                }
                for context_row in contexts
            ],
        }

    backend_api = BackendApiClient() if args.write_back else None
    browser = Browser(channel="msedge", headless=not args.show_browser, image=False)
    try:
        context = BenbenAuthManager().get_context(browser, log_fn=lambda message: log(f"[benben] {message}"))
        crawler = BenbenCrawler(
            context=context,
            task_id=fill_task_id,
            city=str(benben_config.get("defaultCity") or ""),
            suppliers=[str(item) for item in (benben_config.get("supplierNames") or []) if str(item).strip()],
            supplier_ids=",".join([str(item) for item in (benben_config.get("supplierOriginIds") or []) if str(item).strip()]),
            brand_names=",".join([str(item) for item in (benben_config.get("brandNames") or []) if str(item).strip()]),
            single_sku_max_crawl_count=int(benben_config.get("singleSkuMaxCrawlCount") or 0),
        )
        log(f"[auto-fill] uniqueSkuCount={len(unique_skus)}")
        if not crawler.prepare_shared_query(unique_skus):
            raise RuntimeError("Benben shared query preparation failed")
        crawl_cache: Dict[Tuple[str, str, str, str, str], List[Dict[str, Any]]] = {}

        quotation_results = []
        for context_row in contexts:
            qid = str(context_row.get("quotationId") or "").strip()
            sid = str(context_row.get("storeId") or "").strip()
            sku_query_param_map = build_crawler_query_param_map(
                get_backend_online_order_crawler_query_params(qid, sid)
            )
            target_items = [item for item in (context_row.get("items") or []) if not has_price(item)]
            sku_to_items: Dict[str, List[Dict[str, Any]]] = {}
            for item in target_items:
                sku = str(item.get("partsNum") or "").replace(" ", "")
                if sku:
                    sku_to_items.setdefault(sku, []).append(item)

            payloads = []
            snapshot_items = []
            write_back_count = 0
            write_back_errors = []
            for sku, sku_items in sku_to_items.items():
                sku_query_params = sku_query_param_map.get(sku) or {}
                quality_origin_ids = resolve_quality_origin_ids(sku_items, sku_query_params, benben_config)
                supplier_ids = resolve_supplier_ids(sku_query_params, benben_config)
                brand_names = normalize_text_list(benben_config.get("brandNames"))
                region_origin_ids = resolve_region_origin_ids(sku_query_params, benben_config)
                cache_key = (
                    sku,
                    ",".join(quality_origin_ids),
                    ",".join(supplier_ids),
                    ",".join(brand_names),
                    ",".join(region_origin_ids),
                )
                raw_records = crawl_cache.get(cache_key)
                if raw_records is None:
                    log(f"[auto-fill] crawl sku={sku}")
                    raw_records = crawler.crawl_sku(
                        sku,
                        quality_origin_ids=cache_key[1],
                        supplier_ids=cache_key[2],
                        brand_names=cache_key[3],
                        region_origin_ids=cache_key[4],
                    )
                    crawl_cache[cache_key] = raw_records
                sku_records = filter_and_apply_markup(
                    raw_records,
                    sku_query_params,
                    default_markup_rate=float(benben_config.get("defaultMarkupRate") or 0.0),
                    default_transfer_days=int(benben_config.get("defaultTransferDays") or 0),
                )
                for payload in build_report_payloads(
                    sku=sku,
                    scene=AUTO_FILL_SCENE,
                    sku_records=sku_records,
                    online_order_item_ids=[],
                    online_order_item_metas=sku_items,
                    match_strategy=match_strategy,
                ):
                    payload.setdefault("quotationId", qid)
                    payload.setdefault("storeId", sid)
                    payload.setdefault("inquiryId", context_row.get("inquiryId"))
                    payloads.append(payload)
                    apply_auto_fill_result(context_row, payload)
                for item in sku_items:
                    snapshot_item = build_snapshot_batch_item(item, sku_records, match_strategy)
                    if snapshot_item:
                        snapshot_items.append(snapshot_item)

            matched_count = sum(1 for item in snapshot_items if item.get("matchedSnapshot"))
            price_snapshot_request = {
                "storeId": sid or None,
                "items": snapshot_items,
            }
            write_back_response = None
            if backend_api is not None and snapshot_items:
                try:
                    log(
                        f"[auto-fill] write-back quotationId={qid}, storeId={sid}, "
                        f"snapshotItemCount={len(snapshot_items)}, matchedItemCount={matched_count}"
                    )
                    write_back_response = backend_api.post(
                        f"/api/online-orders/quotations/{qid}/price-snapshots/batch",
                        price_snapshot_request,
                    )
                    write_back_count = len(snapshot_items)
                except Exception as exc:
                    write_back_errors.append(f"quotationId={qid}, storeId={sid}, error={exc}")

            quotation_results.append(
                {
                    "quotationId": qid,
                    "storeId": sid,
                    "totalItemCount": len(context_row.get("items") or []),
                    "targetItemCount": len(target_items),
                    "matchedItemCount": matched_count,
                    "snapshotItemCount": len(snapshot_items),
                    "writeBackCount": write_back_count,
                    "writeBackErrors": write_back_errors,
                    "priceSnapshotRequest": price_snapshot_request,
                    "writeBackResponse": write_back_response,
                    "payloads": payloads,
                    "updatedItems": context_row.get("items") or [],
                }
            )

        return {
            "taskId": fill_task_id,
            "benbenConfig": benben_config,
            "matchStrategy": match_strategy,
            "quotationResults": quotation_results,
        }
    finally:
        browser.stop()


def parser() -> argparse.ArgumentParser:
    arg_parser = argparse.ArgumentParser(description="Debug online-order sync and auto-fill by quotationId")
    arg_parser.add_argument("quotation_ids", nargs="+", help="Quotation ids. Comma-separated values are supported.")
    arg_parser.add_argument("--mode", choices=("sync", "auto-fill", "both"), default="both")
    arg_parser.add_argument("--task-id", default="")
    arg_parser.add_argument("--manual-price-fill-enabled", dest="manual_price_fill_enabled", action=argparse.BooleanOptionalAction, default=True)
    arg_parser.add_argument("--auto-submit-enabled", dest="auto_submit_enabled", action=argparse.BooleanOptionalAction, default=False)
    arg_parser.add_argument("--after-sync-wait-seconds", type=float, default=1.0)
    arg_parser.add_argument("--show-browser", action="store_true")
    arg_parser.add_argument("--write-back", action="store_true")
    arg_parser.add_argument("--match-strategy-file", default="")
    arg_parser.add_argument("--match-strategy-json", default="")
    arg_parser.add_argument("--output", default="")
    return arg_parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parser().parse_args(argv)
    quotation_ids = normalize_ids(args.quotation_ids)
    if not quotation_ids:
        raise RuntimeError("No valid quotation ids were provided")

    db = load_db_config()
    log(f"[db] host={db.host}, port={db.port}, db={db.dbname}, schema={db.schema}, quotationCount={len(quotation_ids)}")

    result: Dict[str, Any] = {"mode": args.mode, "requestedQuotationIds": quotation_ids}
    with PostgresAccessor(db) as accessor:
        quotation_rows = accessor.quotations(quotation_ids)
        if not quotation_rows:
            raise RuntimeError(f"No quotation rows found for ids: {','.join(quotation_ids)}")
        quality_maps = build_quality_maps(accessor.quality_dict())
        item_rows = accessor.quote_items(quotation_ids)

        quotations = [normalize_quotation(row) for row in quotation_rows]
        items = [normalize_item(row, quality_maps) for row in item_rows]
        items_by_key = group_items(items)

        result["foundQuotations"] = [
            {
                "quotationId": row["quotationId"],
                "storeId": row["storeId"],
                "inquiryId": row["inquiryId"],
                "statusId": row["statusId"],
                "itemCount": row.get("itemCount"),
            }
            for row in quotations
        ]

        if args.mode in {"sync", "both"}:
            result["sync"] = run_sync(args, quotations)
            if args.mode == "both" and args.after_sync_wait_seconds > 0:
                log(f"[sync] wait {args.after_sync_wait_seconds}s before auto-fill reload")
                time.sleep(args.after_sync_wait_seconds)
                quotation_rows = accessor.quotations(quotation_ids)
                item_rows = accessor.quote_items(quotation_ids)
                quotations = [normalize_quotation(row) for row in quotation_rows]
                items = [normalize_item(row, quality_maps) for row in item_rows]
                items_by_key = group_items(items)

        if args.mode in {"auto-fill", "both"}:
            result["autoFill"] = run_auto_fill(args, quotations, items_by_key)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        log(f"[output] saved json to {args.output}")

    log(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
