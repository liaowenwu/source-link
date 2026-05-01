-- 开思平台与用户抓价配置建表脚本（PostgreSQL）
-- 覆盖设计文档 8.1.6 ~ 8.1.8（含 user_part_crawler_platform_config）
-- 说明：仅建表和索引，不包含初始化数据。

CREATE TABLE IF NOT EXISTS t_part_crawler_platform (
    id            BIGINT PRIMARY KEY,
    tenant_id     VARCHAR(20),
    platform_code VARCHAR(64) NOT NULL,
    platform_name VARCHAR(128) NOT NULL,
    status        INT2 DEFAULT 1,
    create_dept   BIGINT,
    create_by     BIGINT,
    create_time   TIMESTAMP,
    update_by     BIGINT,
    update_time   TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS uk_t_part_crawler_platform_code
    ON t_part_crawler_platform (platform_code);

CREATE INDEX IF NOT EXISTS idx_t_part_crawler_platform_status
    ON t_part_crawler_platform (status);


CREATE TABLE IF NOT EXISTS t_part_crawler_platform_brand (
    id              BIGINT PRIMARY KEY,
    tenant_id       VARCHAR(20),
    platform_id     BIGINT NOT NULL,
    brand_name      VARCHAR(128) NOT NULL,
    brand_origin_id VARCHAR(64) NOT NULL,
    status          INT2 DEFAULT 1,
    create_dept     BIGINT,
    create_by       BIGINT,
    create_time     TIMESTAMP,
    update_by       BIGINT,
    update_time     TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS uk_t_part_crawler_platform_brand_pid_origin
    ON t_part_crawler_platform_brand (platform_id, brand_origin_id);

CREATE INDEX IF NOT EXISTS idx_t_part_crawler_platform_brand_status
    ON t_part_crawler_platform_brand (status);


CREATE TABLE IF NOT EXISTS t_part_crawler_platform_quality (
    id                BIGINT PRIMARY KEY,
    tenant_id         VARCHAR(20),
    platform_id       BIGINT NOT NULL,
    quality_code      VARCHAR(64) NOT NULL,
    quality_name      VARCHAR(128) NOT NULL,
    quality_origin_id VARCHAR(64) NOT NULL,
    quality_type      INT2 DEFAULT 0,
    order_num         INT4 DEFAULT 0,
    status            INT2 DEFAULT 1,
    create_dept       BIGINT,
    create_by         BIGINT,
    create_time       TIMESTAMP,
    update_by         BIGINT,
    update_time       TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS uk_t_part_crawler_platform_quality_pid_origin
    ON t_part_crawler_platform_quality (platform_id, quality_origin_id);

CREATE INDEX IF NOT EXISTS idx_t_part_crawler_platform_quality_status
    ON t_part_crawler_platform_quality (status);


CREATE TABLE IF NOT EXISTS t_part_crawler_platform_region (
    id               BIGINT PRIMARY KEY,
    tenant_id        VARCHAR(20),
    platform_id      BIGINT NOT NULL,
    region_name      VARCHAR(128) NOT NULL,
    region_origin_id VARCHAR(64) NOT NULL,
    status           INT2 DEFAULT 1,
    create_dept      BIGINT,
    create_by        BIGINT,
    create_time      TIMESTAMP,
    update_by        BIGINT,
    update_time      TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS uk_t_part_crawler_platform_region_pid_origin
    ON t_part_crawler_platform_region (platform_id, region_origin_id);

CREATE INDEX IF NOT EXISTS idx_t_part_crawler_platform_region_status
    ON t_part_crawler_platform_region (status);


CREATE TABLE IF NOT EXISTS t_part_crawler_platform_supplier (
    id                 BIGINT PRIMARY KEY,
    tenant_id          VARCHAR(20),
    platform_id        BIGINT NOT NULL,
    supplier_name      VARCHAR(255) NOT NULL,
    supplier_origin_id VARCHAR(64) NOT NULL,
    region_id          BIGINT,
    region_name        VARCHAR(128),
    status             INT2 DEFAULT 1,
    create_dept        BIGINT,
    create_by          BIGINT,
    create_time        TIMESTAMP,
    update_by          BIGINT,
    update_time        TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS uk_t_part_crawler_platform_supplier_pid_origin
    ON t_part_crawler_platform_supplier (platform_id, supplier_origin_id);

CREATE INDEX IF NOT EXISTS idx_t_part_crawler_platform_supplier_status
    ON t_part_crawler_platform_supplier (status);


CREATE TABLE IF NOT EXISTS link_kaisi_part_crawler_platform_brand (
    id                BIGINT PRIMARY KEY,
    tenant_id         VARCHAR(20),
    kaisi_brand_id    BIGINT NOT NULL,
    platform_brand_id BIGINT NOT NULL,
    create_dept       BIGINT,
    create_by         BIGINT,
    create_time       TIMESTAMP,
    update_by         BIGINT,
    update_time       TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS uk_link_kaisi_platform_brand
    ON link_kaisi_part_crawler_platform_brand (kaisi_brand_id, platform_brand_id);


CREATE TABLE IF NOT EXISTS link_kaisi_part_crawler_platform_quality (
    id                  BIGINT PRIMARY KEY,
    tenant_id           VARCHAR(20),
    kaisi_quality_id    BIGINT NOT NULL,
    platform_quality_id BIGINT NOT NULL,
    create_dept         BIGINT,
    create_by           BIGINT,
    create_time         TIMESTAMP,
    update_by           BIGINT,
    update_time         TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS uk_link_kaisi_platform_quality
    ON link_kaisi_part_crawler_platform_quality (kaisi_quality_id, platform_quality_id);


CREATE TABLE IF NOT EXISTS user_part_crawler_platform_config (
    id                                       BIGINT PRIMARY KEY,
    tenant_id                                VARCHAR(20),
    user_id                                  BIGINT,
    platform_id                              BIGINT,
    platform_code                            VARCHAR(64) NOT NULL,
    default_city                             VARCHAR(128),
    price_advantage_rate                     NUMERIC(10, 4) DEFAULT 5,
    region_extra_days_json                   TEXT,
    single_sku_max_crawl_count               INT4 DEFAULT 0,
    quality_origin_ids_json                  TEXT,
    brand_origin_ids_json                    TEXT,
    region_origin_ids_json                   TEXT,
    supplier_configs_json                    TEXT,
    default_markup_rate                      NUMERIC(10, 4) DEFAULT 0,
    default_transfer_days                    INT4 DEFAULT 0,
    crawl_strategy_type                      VARCHAR(32) DEFAULT 'FULL_SELECTED',
    crawl_strategy_selected_platform_codes_json TEXT,
    crawl_strategy_priority_platform_codes_json TEXT,
    crawl_strategy_stop_on_hit               BOOLEAN DEFAULT FALSE,
    create_dept                              BIGINT,
    create_by                                BIGINT,
    create_time                              TIMESTAMP,
    update_by                                BIGINT,
    update_time                              TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS uk_user_part_crawler_platform_config_user_platform
    ON user_part_crawler_platform_config (user_id, platform_code);

CREATE INDEX IF NOT EXISTS idx_user_part_crawler_platform_config_platform
    ON user_part_crawler_platform_config (platform_code);


CREATE TABLE IF NOT EXISTS t_user_kaisi_config (
    id                                  BIGINT PRIMARY KEY,
    tenant_id                           VARCHAR(20),
    user_id                             BIGINT NOT NULL,
    selected_platform_codes_json        TEXT,
    crawl_strategy_type                 VARCHAR(32) DEFAULT 'ALL',
    auto_price_enabled                  BOOLEAN DEFAULT TRUE,
    auto_submit_enabled                 BOOLEAN DEFAULT FALSE,
    quotation_crawl_concurrency         INT4 DEFAULT 1,
    price_concurrency                   INT4 DEFAULT 1,
    request_timeout_ms                  INT4 DEFAULT 30000,
    retry_times                         INT4 DEFAULT 3,
    max_quotation_process_count         INT4 DEFAULT 0,
    manual_price_fill_enabled           BOOLEAN DEFAULT FALSE,
    create_dept                         BIGINT,
    create_by                           BIGINT,
    create_time                         TIMESTAMP,
    update_by                           BIGINT,
    update_time                         TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS uk_t_user_kaisi_config_user
    ON t_user_kaisi_config (user_id);

CREATE INDEX IF NOT EXISTS idx_t_user_kaisi_config_strategy
    ON t_user_kaisi_config (crawl_strategy_type);
