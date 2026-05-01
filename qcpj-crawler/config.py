import os

PORT = int(os.getenv("PORT", "5000"))
DEFAULT_PLATFORM = (os.getenv("DEFAULT_PLATFORM", "benben") or "benben").strip().lower()
AUTH_ROOT_DIR = os.getenv("AUTH_ROOT_DIR", "./auth")

# BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://47.120.69.243:10000/bb-api/").rstrip("/")
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8080").rstrip("/")
BACKEND_TASK_CREATE_URL = f"{BACKEND_BASE_URL}/api/sync/tasks"
BACKEND_PRODUCT_LIST_URL = f"{BACKEND_BASE_URL}/api/products"
BACKEND_BENBEN_CRAWLER_CONFIG_URL = f"{BACKEND_BASE_URL}/api/benben/settings/crawler-config"
BACKEND_KAISI_CRAWLER_CONFIG_URL = f"{BACKEND_BASE_URL}/api/kaisi/base-config/crawler-config"
BACKEND_BENBEN_QUALITY_DICTS_URL = f"{BACKEND_BASE_URL}/api/benben/settings/quality-dicts"
BACKEND_KAISI_QUALITY_DICTS_URL = f"{BACKEND_BASE_URL}/api/kaisi/base-config/qualities/options"
BACKEND_ONLINE_ORDER_QUOTATIONS_URL = f"{BACKEND_BASE_URL}/api/online-orders/quotations"
BACKEND_ONLINE_ORDER_QUOTATION_ITEMS_URL_TEMPLATE = (
    f"{BACKEND_BASE_URL}/api/online-orders/quotations/{{quotation_id}}/items"
)
BACKEND_ONLINE_ORDER_QUOTATION_CRAWLER_QUERY_PARAMS_URL_TEMPLATE = (
    f"{BACKEND_BASE_URL}/api/online-orders/quotations/{{quotation_id}}/crawler-query-params"
)
BACKEND_LOGIN_URL = f"{BACKEND_BASE_URL}/api/auth/login"
BACKEND_WS_INGEST_URL = os.getenv("BACKEND_WS_INGEST_URL", f"{BACKEND_BASE_URL.replace('http', 'ws')}/ws/ingest")
BACKEND_ONLINE_ORDER_QUOTATION_INGEST_URL = (
    os.getenv("BACKEND_ONLINE_ORDER_QUOTATION_INGEST_URL", f"{BACKEND_BASE_URL}/api/online-orders/ingest/quotation")
)
BACKEND_ONLINE_ORDER_EVENT_INGEST_URL = (
    os.getenv("BACKEND_ONLINE_ORDER_EVENT_INGEST_URL", f"{BACKEND_BASE_URL}/api/online-orders/ingest/event")
)
BACKEND_USERNAME = os.getenv("BACKEND_USERNAME", "admin")
BACKEND_PASSWORD = os.getenv("BACKEND_PASSWORD", "admin123")

HTTP_TIMEOUT_SECONDS = float(os.getenv("HTTP_TIMEOUT_SECONDS", "8"))
HTTP_CONNECT_TIMEOUT_SECONDS = float(os.getenv("HTTP_CONNECT_TIMEOUT_SECONDS", "3"))
HTTP_RETRY_TIMES = int(os.getenv("HTTP_RETRY_TIMES", "2"))
HTTP_RETRY_BACKOFF_SECONDS = float(os.getenv("HTTP_RETRY_BACKOFF_SECONDS", "0.8"))

REDIS_URL = os.getenv("REDIS_URL", "").strip()
REDIS_HOST = os.getenv("REDIS_HOST", "47.120.69.243").strip()
REDIS_PORT = int(os.getenv("REDIS_PORT", "12345"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "Djwshigezhuhh").strip() or None

ONLINE_ORDER_POLL_INTERVAL_SECONDS = int(
    os.getenv("ONLINE_ORDER_POLL_INTERVAL_SECONDS", "1")
)
ONLINE_ORDER_MAX_ACCEPT_PER_ROUND = int(
    os.getenv("ONLINE_ORDER_MAX_ACCEPT_PER_ROUND", "10")
)
ONLINE_ORDER_QUEUE1_WORKERS = int(os.getenv("ONLINE_ORDER_QUEUE1_WORKERS", "5"))
ONLINE_ORDER_QUEUE2_WORKERS = int(os.getenv("ONLINE_ORDER_QUEUE2_WORKERS", "5"))
ONLINE_ORDER_QUEUE3_WORKERS = int(os.getenv("ONLINE_ORDER_QUEUE3_WORKERS", "5"))
