from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
CRAWLER_ROOT = SCRIPT_DIR.parent
if str(CRAWLER_ROOT) not in sys.path:
    sys.path.insert(0, str(CRAWLER_ROOT))

from core.browser import Browser
from platforms.robot.auth import RobotAuthManager

SEARCH_URL = "https://www.jiqirenai.com/proxy/v1/es/search/product/by_oe"


def log(message: str) -> None:
    print(message, flush=True)


def normalize_sku(value: str) -> str:
    return "".join(str(value or "").split())


def to_int_list(values: Sequence[str]) -> List[int]:
    result: List[int] = []
    for value in values:
        for part in str(value or "").split(","):
            text = part.strip()
            if not text:
                continue
            try:
                result.append(int(text))
            except Exception:
                pass
    return result


def contains_keyword(text: str, keyword: str) -> bool:
    t = str(text or "").strip().lower()
    k = str(keyword or "").strip().lower()
    return bool(k) and k in t


def first_word(text: str) -> str:
    parts = re.split(r"\s+", str(text or "").strip())
    return parts[0] if parts else ""


def build_base_payload(sku: str, company_id: int, page_size: int) -> Dict[str, Any]:
    return {
        "keyword": "",
        "make_ids": [],
        "city_codes": [],
        "quality_ids": [],
        "brand_ids": [],
        "product_company_ids": [],
        "sort_city_code": "440300",
        "has_stock": True,
        "has_price": False,
        "use_default_order": True,
        "sort_field": "",
        "sort_order": "",
        "page_size": max(int(page_size or 2000), 1),
        "is_current_city": False,
        "oe": normalize_sku(sku),
        "is_enquiry": False,
        "is_local_city": None,
        "seller_id": [],
        "insert_history": True,
        "company_id": int(company_id),
        "not_seller_id": [-1],
        "page_number": 1,
    }


def fetch_once(context, payload: Dict[str, Any], retries: int = 3) -> Dict[str, Any]:
    last_error: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        try:
            response = context.request.post(
                url=SEARCH_URL,
                data=payload,
                headers={"Content-Type": "application/json;charset=UTF-8"},
                timeout=7000,
            )
            return response.json() or {}
        except Exception as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(1)
            else:
                raise RuntimeError(f"request failed after {retries} attempts: {exc}") from exc
    raise RuntimeError(last_error or "request failed")


@dataclass
class CaseDef:
    name: str
    description: str
    payload_patch: Dict[str, Any]


def evaluate_case(case: CaseDef, body: Dict[str, Any]) -> Dict[str, Any]:
    rows = body.get("data") or []
    total = int(body.get("total") or 0)
    patch = case.payload_patch
    violations: List[Dict[str, Any]] = []

    seller_filter = {int(x) for x in (patch.get("seller_id") or []) if isinstance(x, int)}
    has_stock = patch.get("has_stock")
    has_price = patch.get("has_price")
    keyword = str(patch.get("keyword") or "").strip()

    for row in rows:
        if not isinstance(row, dict):
            continue
        seller_id = row.get("seller_id")
        quantity = row.get("quantity")
        price = row.get("price")
        oe_number = row.get("oe_number")
        supplier_code = row.get("supplier_code")
        product_name = row.get("product_name")
        search_oe = row.get("search_oe")

        issue: List[str] = []
        if seller_filter and seller_id not in seller_filter:
            issue.append(f"seller_id={seller_id} not in {sorted(seller_filter)}")
        if has_stock is True:
            try:
                if float(quantity or 0) <= 0:
                    issue.append(f"quantity={quantity} <= 0")
            except Exception:
                issue.append(f"quantity={quantity} invalid")
        if has_price is True:
            try:
                if float(price or 0) <= 0:
                    issue.append(f"price={price} <= 0")
            except Exception:
                issue.append(f"price={price} invalid")
        if keyword:
            if not any(
                contains_keyword(v, keyword)
                for v in (oe_number, supplier_code, product_name, search_oe)
            ):
                issue.append(f"keyword={keyword} not found in main text fields")

        if issue:
            violations.append(
                {
                    "seller_id": seller_id,
                    "seller_name": row.get("seller_name"),
                    "oe_number": oe_number,
                    "supplier_code": supplier_code,
                    "product_name": product_name,
                    "quantity": quantity,
                    "price": price,
                    "issues": issue,
                }
            )
            if len(violations) >= 10:
                break

    unverified_fields: List[str] = []
    if patch.get("quality_ids"):
        unverified_fields.append("quality_ids (response中无稳定quality_id字段，已透传请求但无法自动强校验)")
    if patch.get("brand_ids"):
        unverified_fields.append("brand_ids (response中无稳定brand_id字段，已透传请求但无法自动强校验)")
    if patch.get("city_codes"):
        unverified_fields.append("city_codes (response中无稳定city_code字段，已透传请求但无法自动强校验)")
    if patch.get("product_company_ids"):
        unverified_fields.append("product_company_ids (response中无稳定product_company_id字段，已透传请求但无法自动强校验)")

    return {
        "name": case.name,
        "description": case.description,
        "requestPatch": patch,
        "total": total,
        "returned": len(rows),
        "pass": len(violations) == 0,
        "violations": violations,
        "unverifiedFields": unverified_fields,
        "sample": [
            {
                "seller_id": row.get("seller_id"),
                "seller_name": row.get("seller_name"),
                "quality_name": row.get("quality_name"),
                "brand_name": row.get("brand_name"),
                "city_name": row.get("city_name"),
                "quantity": row.get("quantity"),
                "price": row.get("price"),
            }
            for row in rows[:5]
            if isinstance(row, dict)
        ],
    }


def build_default_suite(baseline_rows: List[Dict[str, Any]], args: argparse.Namespace) -> List[CaseDef]:
    cases: List[CaseDef] = []
    cases.append(
        CaseDef(
            name="baseline",
            description="基线查询（仅按OE号）",
            payload_patch={},
        )
    )
    cases.append(
        CaseDef(
            name="has_stock_true",
            description="库存过滤：has_stock=true",
            payload_patch={"has_stock": True},
        )
    )
    cases.append(
        CaseDef(
            name="has_price_true",
            description="价格过滤：has_price=true",
            payload_patch={"has_price": True},
        )
    )

    if baseline_rows:
        first = baseline_rows[0]
        seller_id = first.get("seller_id")
        if isinstance(seller_id, int):
            cases.append(
                CaseDef(
                    name="seller_id_first",
                    description=f"按首条seller_id过滤: {seller_id}",
                    payload_patch={"seller_id": [seller_id]},
                )
            )

        keyword = first_word(first.get("product_name") or "") or normalize_sku(args.sku)
        if keyword:
            cases.append(
                CaseDef(
                    name="keyword_first_word",
                    description=f"按关键字过滤: {keyword}",
                    payload_patch={"keyword": keyword},
                )
            )

    if args.seller_id:
        cases.append(
            CaseDef(
                name="seller_id_manual",
                description="手工 seller_id 条件",
                payload_patch={"seller_id": to_int_list(args.seller_id)},
            )
        )
    if args.quality_id:
        cases.append(
            CaseDef(
                name="quality_id_manual",
                description="手工 quality_ids 条件",
                payload_patch={"quality_ids": to_int_list(args.quality_id)},
            )
        )
    if args.brand_id:
        cases.append(
            CaseDef(
                name="brand_id_manual",
                description="手工 brand_ids 条件",
                payload_patch={"brand_ids": to_int_list(args.brand_id)},
            )
        )
    if args.city_code:
        cases.append(
            CaseDef(
                name="city_code_manual",
                description="手工 city_codes 条件",
                payload_patch={"city_codes": to_int_list(args.city_code)},
            )
        )
    if args.product_company_id:
        cases.append(
            CaseDef(
                name="product_company_manual",
                description="手工 product_company_ids 条件",
                payload_patch={"product_company_ids": to_int_list(args.product_company_id)},
            )
        )
    if args.keyword:
        cases.append(
            CaseDef(
                name="keyword_manual",
                description=f"手工关键字条件: {args.keyword}",
                payload_patch={"keyword": args.keyword},
            )
        )
    return cases


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Robot 零件查询条件判断测试脚本")
    parser.add_argument("--sku", default="51745A218F7", help="要查询的OE号/零件号")
    parser.add_argument("--company-id", type=int, default=9394, help="请求体company_id")
    parser.add_argument("--page-size", type=int, default=2000, help="请求体page_size")
    parser.add_argument("--show-browser", action="store_true", help="显示浏览器，便于手动登录")
    parser.add_argument("--output", default="", help="保存JSON报告路径")

    parser.add_argument("--seller-id", action="append", default=[], help="附加 seller_id 条件（可重复/逗号分隔）")
    parser.add_argument("--quality-id", action="append", default=[], help="附加 quality_ids 条件（可重复/逗号分隔）")
    parser.add_argument("--brand-id", action="append", default=[], help="附加 brand_ids 条件（可重复/逗号分隔）")
    parser.add_argument("--city-code", action="append", default=[], help="附加 city_codes 条件（可重复/逗号分隔）")
    parser.add_argument(
        "--product-company-id",
        action="append",
        default=[],
        help="附加 product_company_ids 条件（可重复/逗号分隔）",
    )
    parser.add_argument("--keyword", default="", help="附加 keyword 条件")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    sku = normalize_sku(args.sku)
    if not sku:
        raise RuntimeError("sku is required")

    base_payload = build_base_payload(sku=sku, company_id=args.company_id, page_size=args.page_size)
    log(f"[robot-test] base payload oe={sku}, company_id={args.company_id}, page_size={args.page_size}")

    browser = Browser(channel="msedge", headless=not args.show_browser, image=False)
    try:
        context = RobotAuthManager().get_context(browser, log_fn=lambda msg: log(f"[robot-auth] {msg}"))
        baseline_body = fetch_once(context, base_payload)
        baseline_rows = baseline_body.get("data") or []
        log(f"[robot-test] baseline returned={len(baseline_rows)}, total={int(baseline_body.get('total') or 0)}")

        cases = build_default_suite(baseline_rows, args)
        results: List[Dict[str, Any]] = []
        for idx, case in enumerate(cases, start=1):
            payload = dict(base_payload)
            payload.update(case.payload_patch)
            body = fetch_once(context, payload)
            case_result = evaluate_case(case, body)
            results.append(case_result)

            status = "PASS" if case_result["pass"] else "FAIL"
            log(
                f"[{idx:02d}/{len(cases):02d}] {case.name} => {status}, "
                f"returned={case_result['returned']}, total={case_result['total']}, "
                f"violations={len(case_result['violations'])}"
            )

        summary = {
            "sku": sku,
            "companyId": args.company_id,
            "pageSize": args.page_size,
            "caseCount": len(results),
            "passCount": sum(1 for item in results if item.get("pass")),
            "failCount": sum(1 for item in results if not item.get("pass")),
            "results": results,
        }

        text = json.dumps(summary, ensure_ascii=False, indent=2)
        log(text)
        if args.output:
            output = Path(args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(text, encoding="utf-8")
            log(f"[robot-test] saved output to {output}")
    finally:
        browser.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

