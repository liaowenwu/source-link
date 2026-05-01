import json
import time
from typing import Any, Dict, List

import requests
from requests.exceptions import ConnectTimeout, ReadTimeout

from config import (
    BACKEND_BENBEN_CRAWLER_CONFIG_URL,
    BACKEND_BENBEN_QUALITY_DICTS_URL,
    BACKEND_KAISI_CRAWLER_CONFIG_URL,
    BACKEND_KAISI_QUALITY_DICTS_URL,
    BACKEND_LOGIN_URL,
    BACKEND_ONLINE_ORDER_QUOTATIONS_URL,
    BACKEND_ONLINE_ORDER_QUOTATION_CRAWLER_QUERY_PARAMS_URL_TEMPLATE,
    BACKEND_ONLINE_ORDER_EVENT_INGEST_URL,
    BACKEND_ONLINE_ORDER_QUOTATION_INGEST_URL,
    BACKEND_ONLINE_ORDER_QUOTATION_ITEMS_URL_TEMPLATE,
    BACKEND_PASSWORD,
    BACKEND_PRODUCT_LIST_URL,
    BACKEND_TASK_CREATE_URL,
    BACKEND_USERNAME,
    HTTP_CONNECT_TIMEOUT_SECONDS,
    HTTP_RETRY_BACKOFF_SECONDS,
    HTTP_RETRY_TIMES,
    HTTP_TIMEOUT_SECONDS,
)

_access_token = ""


def _request_with_retry(method: str, url: str, **kwargs) -> requests.Response:
    timeout = kwargs.pop("timeout", (HTTP_CONNECT_TIMEOUT_SECONDS, HTTP_TIMEOUT_SECONDS))
    last_error = None
    for attempt in range(HTTP_RETRY_TIMES + 1):
        try:
            return requests.request(method, url, timeout=timeout, **kwargs)
        except (ReadTimeout, ConnectTimeout) as exc:
            last_error = exc
            if attempt >= HTTP_RETRY_TIMES:
                break
            time.sleep(HTTP_RETRY_BACKOFF_SECONDS * (attempt + 1))
    raise requests.RequestException(
        f"{method} {url} failed after {HTTP_RETRY_TIMES + 1} attempts: {last_error}"
    ) from last_error


def _ensure_success(response: requests.Response, action: str) -> None:
    if response.ok:
        return
    body = (response.text or "").strip()
    if len(body) > 500:
        body = body[:500] + "..."
    raise requests.RequestException(
        f"{action} failed, status_code={response.status_code}, body={body}"
    )


def _login() -> str:
    response = _request_with_retry(
        "POST",
        BACKEND_LOGIN_URL,
        json={"username": BACKEND_USERNAME, "password": BACKEND_PASSWORD},
    )
    _ensure_success(response, "backend login")
    data = response.json() or {}
    token = (data.get("data") or {}).get("accessToken")
    if not token:
        raise requests.RequestException("backend login succeeded but accessToken is missing")
    return token


def _request_with_auth(method: str, url: str, **kwargs) -> requests.Response:
    global _access_token
    if not _access_token:
        _access_token = _login()

    headers = kwargs.pop("headers", {}) or {}
    headers["Authorization"] = f"Bearer {_access_token}"
    kwargs["headers"] = headers

    response = _request_with_retry(method, url, **kwargs)
    if response.status_code not in (401, 403):
        return response

    _access_token = _login()
    headers["Authorization"] = f"Bearer {_access_token}"
    kwargs["headers"] = headers
    return _request_with_retry(method, url, **kwargs)


def create_backend_task(
    task_type: str,
    trigger_by: str,
    total_count: int,
    sku: str = "",
    skus=None,
    biz_type: str = "",
    task_params: Any = None,
) -> str:
    normalized_skus = skus or []
    task_params_payload = task_params
    if task_params_payload is not None and not isinstance(task_params_payload, str):
        try:
            task_params_payload = json.dumps(task_params_payload, ensure_ascii=False)
        except Exception:
            task_params_payload = str(task_params_payload)

    payload = {
        "taskType": task_type,
        "bizType": (biz_type or "").strip() or None,
        "taskParams": task_params_payload,
        "triggerBy": trigger_by,
        "totalCount": total_count,
        "sku": (sku or "").strip(),
        "skus": normalized_skus,
    }
    response = _request_with_auth("POST", BACKEND_TASK_CREATE_URL, json=payload)
    _ensure_success(response, "create backend task")

    data = response.json() or {}
    task_no = (data.get("data") or {}).get("taskNo") or data.get("taskNo")
    if not task_no:
        raise requests.RequestException("backend task response is missing taskNo")
    return task_no


def get_backend_crawler_config() -> Dict[str, Any]:
    response = _request_with_auth("GET", BACKEND_BENBEN_CRAWLER_CONFIG_URL)
    _ensure_success(response, "query backend crawler config")
    body = response.json() or {}
    data = body.get("data") or body
    return data if isinstance(data, dict) else {}


def get_backend_kaisi_crawler_config() -> Dict[str, Any]:
    """
    查询开思抓价配置，失败时回退到旧的奔奔配置接口。
    """
    try:
        response = _request_with_auth("GET", BACKEND_KAISI_CRAWLER_CONFIG_URL)
        _ensure_success(response, "query kaisi crawler config")
        body = response.json() or {}
        data = body.get("data") or body
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return get_backend_crawler_config()


def get_backend_quality_dicts() -> List[Dict[str, Any]]:
    response = _request_with_auth("GET", BACKEND_BENBEN_QUALITY_DICTS_URL)
    _ensure_success(response, "query backend quality dicts")
    body = response.json() or {}
    data = body.get("data") or body
    if not isinstance(data, list):
        return []
    return [row for row in data if isinstance(row, dict)]


def get_backend_kaisi_quality_dicts() -> List[Dict[str, Any]]:
    """
    查询开思质量基础配置，失败时回退到旧的质量字典接口。
    """
    try:
        response = _request_with_auth("GET", BACKEND_KAISI_QUALITY_DICTS_URL)
        _ensure_success(response, "query kaisi quality dicts")
        body = response.json() or {}
        data = body.get("data") or body
        if isinstance(data, list):
            return [row for row in data if isinstance(row, dict)]
    except Exception:
        pass
    return get_backend_quality_dicts()


def get_backend_online_order_quotation_items(
    quotation_id: str, store_id: str = ""
) -> List[Dict[str, Any]]:
    normalized_quotation_id = str(quotation_id or "").strip()
    normalized_store_id = str(store_id or "").strip()
    if not normalized_quotation_id:
        return []

    url = BACKEND_ONLINE_ORDER_QUOTATION_ITEMS_URL_TEMPLATE.format(
        quotation_id=normalized_quotation_id
    )
    params = {"storeId": normalized_store_id} if normalized_store_id else None
    response = _request_with_auth("GET", url, params=params)
    _ensure_success(response, "query online-order quotation items")

    body = response.json() or {}
    data = body.get("data") or body
    if not isinstance(data, list):
        return []
    return [row for row in data if isinstance(row, dict)]


def get_backend_online_order_quotation(
    quotation_id: str, store_id: str = ""
) -> Dict[str, Any]:
    normalized_quotation_id = str(quotation_id or "").strip()
    normalized_store_id = str(store_id or "").strip()
    if not normalized_quotation_id:
        return {}

    response = _request_with_auth(
        "GET",
        BACKEND_ONLINE_ORDER_QUOTATIONS_URL,
        params={
            "quotationId": normalized_quotation_id,
            "pageNo": 1,
            "pageSize": 200,
        },
    )
    _ensure_success(response, "query online-order quotation")

    body = response.json() or {}
    data = body.get("data") or body
    rows = []
    if isinstance(data, dict):
        rows = data.get("list") or data.get("records") or []
    elif isinstance(data, list):
        rows = data

    if not isinstance(rows, list):
        return {}

    matched_rows = [
        row
        for row in rows
        if isinstance(row, dict)
        and str(row.get("quotationId") or row.get("id") or "").strip() == normalized_quotation_id
    ]
    if normalized_store_id:
        matched_rows = [
            row for row in matched_rows if str(row.get("storeId") or "").strip() == normalized_store_id
        ]
    return matched_rows[0] if matched_rows else {}


def get_backend_online_order_crawler_query_params(
    quotation_id: str, store_id: str = ""
) -> List[Dict[str, Any]]:
    normalized_quotation_id = str(quotation_id or "").strip()
    normalized_store_id = str(store_id or "").strip()
    if not normalized_quotation_id:
        return []

    url = BACKEND_ONLINE_ORDER_QUOTATION_CRAWLER_QUERY_PARAMS_URL_TEMPLATE.format(
        quotation_id=normalized_quotation_id
    )
    params = {"storeId": normalized_store_id} if normalized_store_id else None
    response = _request_with_auth("GET", url, params=params)
    _ensure_success(response, "query online-order crawler query params")

    body = response.json() or {}
    data = body.get("data") or body
    if not isinstance(data, list):
        return []
    return [row for row in data if isinstance(row, dict)]


def query_products_for_task(task_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    mode = (task_payload.get("mode") or "single").strip().lower()
    if mode == "single":
        sku = _normalize_sku(task_payload.get("sku"))
        if not sku:
            return []
        return _query_products_by_sku(sku)

    if mode == "batch":
        skus = task_payload.get("skus") or []
        result = []
        seen = set()
        for sku in skus:
            cleaned = _normalize_sku(sku)
            if not cleaned or cleaned in seen:
                continue
            seen.add(cleaned)
            rows = _query_products_by_sku(cleaned)
            if rows:
                result.extend(rows)
        return result

    return []


def _query_products_by_sku(sku: str) -> List[Dict[str, Any]]:
    params = {
        "sku": sku,
        "pageNo": 1,
        "pageSize": 100,
    }
    response = _request_with_auth("GET", BACKEND_PRODUCT_LIST_URL, params=params)
    _ensure_success(response, "query backend products")

    body = response.json() or {}
    payload = body.get("data") or {}
    rows = payload.get("list") or []
    return [row for row in rows if _normalize_sku(row.get("sku")) == sku]


def _normalize_sku(value: Any) -> str:
    text = str(value or "")
    return "".join(text.split())


def post_online_order_event(task_no: str, event_body: Dict[str, Any]) -> None:
    """
    上报在线接单事件（HTTP + 鉴权）。
    """
    normalized_task_no = str(task_no or "").strip()
    response = _request_with_auth(
        "POST",
        BACKEND_ONLINE_ORDER_EVENT_INGEST_URL,
        params={"taskNo": normalized_task_no} if normalized_task_no else None,
        json=event_body,
    )
    _ensure_success(response, "ingest online-order event")


def post_online_order_quotation(task_no: str, payload: Dict[str, Any]) -> None:
    """
    上报在线接单报价单主+明细（HTTP + 鉴权）。
    """
    normalized_task_no = str(task_no or "").strip()
    response = _request_with_auth(
        "POST",
        BACKEND_ONLINE_ORDER_QUOTATION_INGEST_URL,
        params={"taskNo": normalized_task_no} if normalized_task_no else None,
        json=payload,
    )
    _ensure_success(response, "ingest online-order quotation")
