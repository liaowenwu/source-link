-- 开思工作台模块建表脚本（PostgreSQL）
-- 说明：仅包含结构，不包含初始化数据。

CREATE TABLE IF NOT EXISTS online_order_kaisi_task (
    id                  BIGINT PRIMARY KEY,
    tenant_id           VARCHAR(20),
    task_no             VARCHAR(64) NOT NULL,
    task_type           VARCHAR(32),
    biz_type            VARCHAR(64),
    trigger_by          VARCHAR(32),
    service_status      VARCHAR(32),
    total_count         INT4 DEFAULT 0,
    success_count       INT4 DEFAULT 0,
    fail_count          INT4 DEFAULT 0,
    today_catch_count   INT4 DEFAULT 0,
    today_price_count   INT4 DEFAULT 0,
    today_submit_count  INT4 DEFAULT 0,
    current_node_code   VARCHAR(64),
    current_node_name   VARCHAR(128),
    current_message     TEXT,
    error_message       TEXT,
    started_at          TIMESTAMP,
    stopped_at          TIMESTAMP,
    create_dept         BIGINT,
    create_by           BIGINT,
    create_time         TIMESTAMP,
    update_by           BIGINT,
    update_time         TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS uk_online_order_kaisi_task_task_no
    ON online_order_kaisi_task (task_no);

CREATE TABLE IF NOT EXISTS online_order_kaisi_task_log (
    id                  BIGINT PRIMARY KEY,
    tenant_id           VARCHAR(20),
    task_no             VARCHAR(64) NOT NULL,
    event_code          VARCHAR(64),
    event_type          VARCHAR(64),
    event_level         VARCHAR(16),
    display_title       VARCHAR(255),
    display_content     TEXT,
    quotation_id        VARCHAR(64),
    store_id            VARCHAR(64),
    raw_payload         TEXT,
    create_dept         BIGINT,
    create_by           BIGINT,
    create_time         TIMESTAMP,
    update_by           BIGINT,
    update_time         TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_online_order_kaisi_task_log_task_time
    ON online_order_kaisi_task_log (task_no, create_time DESC);

CREATE TABLE IF NOT EXISTS online_order_kaisi_quotation (
    id                        BIGINT PRIMARY KEY,
    tenant_id                 VARCHAR(20),
    quotation_id              VARCHAR(64) NOT NULL,
    inquiry_id                VARCHAR(64),
    store_id                  VARCHAR(64),
    supplier_company_id       VARCHAR(64),
    status_id                 VARCHAR(32),
    status_id_desc            VARCHAR(64),
    flow_status               VARCHAR(32),
    process_status            VARCHAR(32),
    current_node_code         VARCHAR(64),
    current_node_name         VARCHAR(128),
    manual_price_fill_enabled BOOLEAN DEFAULT TRUE,
    auto_submit_enabled       BOOLEAN DEFAULT FALSE,
    item_count                INT4 DEFAULT 0,
    quoted_item_count         INT4 DEFAULT 0,
    unquote_item_count        INT4 DEFAULT 0,
    submitted_item_count      INT4 DEFAULT 0,
    exception_item_count      INT4 DEFAULT 0,
    need_manual_handle        BOOLEAN DEFAULT FALSE,
    need_alert                BOOLEAN DEFAULT FALSE,
    assigned_user_id          BIGINT,
    last_message              TEXT,
    error_message             TEXT,
    raw_payload               TEXT,
    last_log_time             TIMESTAMP,
    create_dept               BIGINT,
    create_by                 BIGINT,
    create_time               TIMESTAMP,
    update_by                 BIGINT,
    update_time               TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS uk_online_order_kaisi_quotation
    ON online_order_kaisi_quotation (quotation_id, store_id);

CREATE INDEX IF NOT EXISTS idx_online_order_kaisi_quotation_status
    ON online_order_kaisi_quotation (flow_status, process_status, last_log_time DESC);

CREATE TABLE IF NOT EXISTS online_order_kaisi_quote_item (
    id                    BIGINT PRIMARY KEY,
    tenant_id             VARCHAR(20),
    quotation_id          VARCHAR(64) NOT NULL,
    store_id              VARCHAR(64),
    online_order_item_id  VARCHAR(64),
    resolve_result_id     VARCHAR(128),
    parts_num             VARCHAR(128),
    parts_name            VARCHAR(255),
    brand_name            VARCHAR(255),
    parts_brand_quality   VARCHAR(64),
    store_service_area    VARCHAR(64),
    quantity              INT4,
    suggested_price       NUMERIC(12, 2),
    final_price           NUMERIC(12, 2),
    item_process_status   VARCHAR(32),
    unmatched_reason      TEXT,
    remark                TEXT,
    raw_payload           TEXT,
    create_dept           BIGINT,
    create_by             BIGINT,
    create_time           TIMESTAMP,
    update_by             BIGINT,
    update_time           TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_online_order_kaisi_quote_item_qid
    ON online_order_kaisi_quote_item (quotation_id, store_id);

CREATE TABLE IF NOT EXISTS online_order_kaisi_execution_log (
    id                  BIGINT PRIMARY KEY,
    tenant_id           VARCHAR(20),
    task_no             VARCHAR(64),
    quotation_id        VARCHAR(64),
    store_id            VARCHAR(64),
    flow_status         VARCHAR(32),
    process_status      VARCHAR(32),
    current_node_code   VARCHAR(64),
    current_node_name   VARCHAR(128),
    event_type          VARCHAR(64),
    log_level           VARCHAR(16),
    message             TEXT,
    raw_payload         TEXT,
    create_dept         BIGINT,
    create_by           BIGINT,
    create_time         TIMESTAMP,
    update_by           BIGINT,
    update_time         TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_online_order_kaisi_execution_log_qid
    ON online_order_kaisi_execution_log (quotation_id, store_id, create_time DESC);

CREATE TABLE IF NOT EXISTS online_order_kaisi_submit_item (
    id                  BIGINT PRIMARY KEY,
    tenant_id           VARCHAR(20),
    task_no             VARCHAR(64),
    quotation_id        VARCHAR(64),
    store_id            VARCHAR(64),
    resolve_result_id   VARCHAR(128),
    parts_num           VARCHAR(128),
    parts_name          VARCHAR(255),
    submit_status       VARCHAR(32),
    submit_request      TEXT,
    submit_response     TEXT,
    error_message       TEXT,
    submitted_at        TIMESTAMP,
    create_dept         BIGINT,
    create_by           BIGINT,
    create_time         TIMESTAMP,
    update_by           BIGINT,
    update_time         TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_online_order_kaisi_submit_item_qid
    ON online_order_kaisi_submit_item (quotation_id, store_id, submitted_at DESC);

