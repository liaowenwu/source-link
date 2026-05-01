-- 开思平台基础配置建表脚本（PostgreSQL）
-- 说明：仅建表和索引，不包含初始化数据。

CREATE TABLE IF NOT EXISTS kaisi_brand (
    id              BIGINT PRIMARY KEY,
    tenant_id       VARCHAR(20),
    brand_name      VARCHAR(128) NOT NULL,
    brand_origin_id VARCHAR(64) NOT NULL,
    status          INT2 DEFAULT 1,
    create_dept     BIGINT,
    create_by       BIGINT,
    create_time     TIMESTAMP,
    update_by       BIGINT,
    update_time     TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS uk_kaisi_brand_origin_id
    ON kaisi_brand (brand_origin_id);

CREATE UNIQUE INDEX IF NOT EXISTS uk_kaisi_brand_name
    ON kaisi_brand (brand_name);

CREATE INDEX IF NOT EXISTS idx_kaisi_brand_status
    ON kaisi_brand (status);


CREATE TABLE IF NOT EXISTS kaisi_quality (
    id                BIGINT PRIMARY KEY,
    tenant_id         VARCHAR(20),
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

CREATE UNIQUE INDEX IF NOT EXISTS uk_kaisi_quality_origin_id
    ON kaisi_quality (quality_origin_id);

CREATE UNIQUE INDEX IF NOT EXISTS uk_kaisi_quality_code
    ON kaisi_quality (quality_code);

CREATE INDEX IF NOT EXISTS idx_kaisi_quality_status
    ON kaisi_quality (status);

CREATE INDEX IF NOT EXISTS idx_kaisi_quality_order
    ON kaisi_quality (order_num, quality_code);


CREATE TABLE IF NOT EXISTS link_kaisi_quality_brand (
    id                BIGINT PRIMARY KEY,
    tenant_id         VARCHAR(20),
    kaisi_quality_id  BIGINT NOT NULL,
    kaisi_brand_id    BIGINT NOT NULL,
    quality_code      VARCHAR(64),
    quality_name      VARCHAR(128),
    quality_origin_id VARCHAR(64),
    brand_name        VARCHAR(128),
    brand_origin_id   VARCHAR(64),
    status            INT2 DEFAULT 1,
    create_dept       BIGINT,
    create_by         BIGINT,
    create_time       TIMESTAMP,
    update_by         BIGINT,
    update_time       TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS uk_link_kaisi_quality_brand
    ON link_kaisi_quality_brand (kaisi_quality_id, kaisi_brand_id);

CREATE INDEX IF NOT EXISTS idx_link_kaisi_quality_brand_status
    ON link_kaisi_quality_brand (status);

CREATE INDEX IF NOT EXISTS idx_link_kaisi_quality_brand_quality
    ON link_kaisi_quality_brand (quality_code, quality_name);

CREATE INDEX IF NOT EXISTS idx_link_kaisi_quality_brand_brand
    ON link_kaisi_quality_brand (brand_name, brand_origin_id);

