"""
同步开思管理员基础配置数据。

用途：
1. 从源库 benben.bb 同步 kaisi_brand/kais_brand、kaisi_quality/kais_quality、link_kaisi_* 表。
2. 写入目标库 ry.public，同名表按 id 做 upsert。
3. 管理员配置不绑定租户，目标 tenant_id 统一写入 NULL。

连接信息默认使用当前开发库配置，也可以通过环境变量覆盖。
"""

from __future__ import annotations

import os
from typing import Dict, Iterable, List, Sequence, Tuple

import psycopg2
from psycopg2.extras import execute_values


DB_HOST = os.getenv("KAISI_SYNC_DB_HOST", "47.120.69.243")
DB_PORT = int(os.getenv("KAISI_SYNC_DB_PORT", "15432"))
DB_USER = os.getenv("KAISI_SYNC_DB_USER", "postgres")
DB_PASSWORD = os.getenv("KAISI_SYNC_DB_PASSWORD", "Djwshigezhuhh")

SOURCE_DB = os.getenv("KAISI_SYNC_SOURCE_DB", "benben")
SOURCE_SCHEMA = os.getenv("KAISI_SYNC_SOURCE_SCHEMA", "bb")
TARGET_DB = os.getenv("KAISI_SYNC_TARGET_DB", "ry")
TARGET_SCHEMA = os.getenv("KAISI_SYNC_TARGET_SCHEMA", "public")

BASE_TABLES = {"kaisi_brand", "kaisi_quality", "kais_brand", "kais_quality"}
LINK_TABLE_PREFIX = "link_kaisi_"
SOURCE_TARGET_TABLE_ALIASES = {
    "kais_brand": "kaisi_brand",
    "kais_quality": "kaisi_quality",
}

# 兼容旧库字段命名，目标库统一使用 RuoYi Plus 的审计字段。
SOURCE_COLUMN_ALIASES = {
    "create_time": ("create_time", "created_at"),
    "update_time": ("update_time", "updated_at"),
    "create_by": ("create_by", "created_by"),
    "update_by": ("update_by", "updated_by"),
}


def connect(db_name: str):
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=db_name,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=10,
    )


def quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def list_tables(conn, schema: str) -> List[str]:
    with conn.cursor() as cur:
        cur.execute(
            """
            select tablename
            from pg_tables
            where schemaname = %s
              and (tablename = any(%s) or tablename like %s)
            order by tablename
            """,
            (schema, list(BASE_TABLES), f"{LINK_TABLE_PREFIX}%"),
        )
        return [row[0] for row in cur.fetchall()]


def resolve_target_table(source_table: str, target_tables: Iterable[str]) -> str | None:
    target_table = SOURCE_TARGET_TABLE_ALIASES.get(source_table, source_table)
    if target_table in target_tables:
        return target_table
    return None


def list_columns(conn, schema: str, table: str) -> List[str]:
    with conn.cursor() as cur:
        cur.execute(
            """
            select column_name
            from information_schema.columns
            where table_schema = %s
              and table_name = %s
            order by ordinal_position
            """,
            (schema, table),
        )
        return [row[0] for row in cur.fetchall()]


def resolve_source_column(target_column: str, source_columns: Sequence[str]) -> str | None:
    if target_column == "tenant_id":
        return None
    candidates = SOURCE_COLUMN_ALIASES.get(target_column, (target_column,))
    for column in candidates:
        if column in source_columns:
            return column
    return None


def build_column_mapping(source_columns: Sequence[str], target_columns: Sequence[str]) -> List[Tuple[str, str | None]]:
    mapping: List[Tuple[str, str | None]] = []
    for target_column in target_columns:
        if target_column == "tenant_id":
            mapping.append((target_column, None))
            continue
        source_column = resolve_source_column(target_column, source_columns)
        if source_column:
            mapping.append((target_column, source_column))
    return mapping


def fetch_rows(conn, table: str, mapping: Sequence[Tuple[str, str | None]]) -> List[Tuple]:
    select_exprs = []
    for target_column, source_column in mapping:
        if source_column is None:
            select_exprs.append("NULL")
        else:
            select_exprs.append(quote_ident(source_column))

    sql = (
        f"select {', '.join(select_exprs)} "
        f"from {quote_ident(SOURCE_SCHEMA)}.{quote_ident(table)} "
        f"order by {quote_ident('id')}"
    )
    with conn.cursor() as cur:
        cur.execute(sql)
        return cur.fetchall()


def upsert_rows(conn, table: str, target_columns: Sequence[str], rows: Iterable[Tuple]) -> int:
    rows = list(rows)
    if not rows:
        return 0

    columns_sql = ", ".join(quote_ident(column) for column in target_columns)
    update_columns = [column for column in target_columns if column != "id"]
    update_sql = ", ".join(
        f"{quote_ident(column)} = excluded.{quote_ident(column)}" for column in update_columns
    )
    sql = (
        f"insert into {quote_ident(TARGET_SCHEMA)}.{quote_ident(table)} ({columns_sql}) values %s "
        f"on conflict ({quote_ident('id')}) do update set {update_sql}"
    )
    with conn.cursor() as cur:
        execute_values(cur, sql, rows, page_size=1000)
    return len(rows)


def sync_table(source_conn, target_conn, source_table: str, target_table: str) -> int:
    source_columns = list_columns(source_conn, SOURCE_SCHEMA, source_table)
    target_columns = list_columns(target_conn, TARGET_SCHEMA, target_table)
    if "id" not in source_columns or "id" not in target_columns:
        print(f"跳过 {source_table}: 缺少 id 主键字段")
        return 0

    mapping = build_column_mapping(source_columns, target_columns)
    mapped_target_columns = [target_column for target_column, _ in mapping]
    if "id" not in mapped_target_columns:
        print(f"跳过 {source_table}: 字段映射后缺少 id")
        return 0

    rows = fetch_rows(source_conn, source_table, mapping)
    count = upsert_rows(target_conn, target_table, mapped_target_columns, rows)
    if source_table == target_table:
        print(f"已同步 {target_table}: {count} 行")
    else:
        print(f"已同步 {source_table} -> {target_table}: {count} 行")
    return count


def main() -> None:
    source_conn = connect(SOURCE_DB)
    target_conn = connect(TARGET_DB)
    try:
        source_tables = list_tables(source_conn, SOURCE_SCHEMA)
        target_tables = set(list_tables(target_conn, TARGET_SCHEMA))
        table_pairs = []
        for source_table in source_tables:
            target_table = resolve_target_table(source_table, target_tables)
            if target_table:
                table_pairs.append((source_table, target_table))

        if not table_pairs:
            print("没有找到可同步的 kaisi/link_kaisi 表")
            return

        total = 0
        for source_table, target_table in table_pairs:
            total += sync_table(source_conn, target_conn, source_table, target_table)
        target_conn.commit()
        print(f"同步完成，共处理 {len(table_pairs)} 张表，{total} 行")
    except Exception:
        target_conn.rollback()
        raise
    finally:
        source_conn.close()
        target_conn.close()


if __name__ == "__main__":
    main()
