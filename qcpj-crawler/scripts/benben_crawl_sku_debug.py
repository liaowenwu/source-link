from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from core.browser import Browser
from platforms.benben.auth import BenbenAuthManager
from platforms.benben.crawler import BenbenCrawler


def log(message: str) -> None:
    print(message, flush=True)


def normalize_sku(value: str) -> str:
    return "".join(str(value or "").split())


def preview_records(records: List[Dict[str, Any]], count: int) -> List[Dict[str, Any]]:
    rows = []
    for item in records[: max(count, 0)]:
        rows.append(
            {
                "sku": item.get("sku"),
                "brandName": item.get("brandName"),
                "brandOriginId": item.get("brandOriginId"),
                "qualityName": item.get("qualityName"),
                "qualityOriginId": item.get("qualityOriginId"),
                "regionName": item.get("regionName"),
                "regionOriginId": item.get("regionOriginId"),
                "supplierName": item.get("supplierName"),
                "supplierId": item.get("supplierId"),
                "stock": item.get("stock"),
                "price": item.get("price"),
            }
        )
    return rows


def main() -> int:
    # 固定调试参数：直接改这里即可，无需命令行传参
    sku = normalize_sku("A2308300084")
    quality_origin_ids = "4,7,13,1"
    supplier_ids = (
             "宝鑫行,FDD247823EE94043AB12B4F165CE630E,CFBA13733A5C429C8BDE58995A8C4261,6C222856382C435F9D7E3AB2A1AD464F,粤翔,949843E0DEA64A65B63422D3C2736110,0218C3476BC74710B8D3C6ABA0F3B4B8,影富,F605342E5F1E48A09A1850C2A94144AA,CD2CC0B38D3C447B9EC16124F710AFAE,607A4745C97845BCBF11DC97D5AA5CE4,690917147F224B5A8042DBB9251F78DB,596022ED18DB40B9A76915A4E38B3BD7,93E5BA1F867B40B0ADD0C7EFD2872318,E05A9ED27FC740C8B63304E3AEFAE9AB,C3FEEE5F903648A09B0CD8507F689480,FB19747671854FE484F4FBD908543BDE,6F799A07DEEA49EA8161C6612CA22596,176BB0224E4C4A05AF355CA63E8BA3D2,72B728D3C3EA4F9FA7EFBC308AC829EE"

        )
    brand_names = (
           "正厂,爱尔铃,舍弗勒-FAG,ACM,ATE,福斯,曼牌,爱信,法兰乐,博世,马瑞利,纳铁福,费比,海米勒,"
               "萨来力,德纳,舍弗勒-INA,海拉,马勒,采埃孚伦福德,斯凯孚,盖茨,天合,GGT,AMK,BILSTEIN倍适登,"
               "科德宝,采埃孚,布雷博,噶尔法,马牌,森萨塔,岱高,德尔福,天盛,泰明顿,VD0,BWI,巴斯夫,科帝克,"
              "博格,爱斯达克,法雷奥,科尔本,皮尔博格"
        )
    city = ","
    region_origin_ids = ""
    single_sku_max_crawl_count = 20
    show_browser = False
    preview_count = 20
    output = r"D:\project\my\bb-demo\logs\crawl-sku-A2208300284.json"
    task_id = ""

    if not sku:
        raise RuntimeError("sku is required")

    task_id = task_id.strip() or f"CRAWL-SKU-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    log(f"[debug] taskId={task_id}, sku={sku}")
    log(
        "[debug] params "
        f"quality_origin_ids={quality_origin_ids}, "
        f"supplier_ids={supplier_ids}, "
        f"brand_names={brand_names}, region_origin_ids={region_origin_ids}, city={city}"
    )

    browser = Browser(channel="msedge", headless=not show_browser, image=False)
    try:
        context = BenbenAuthManager().get_context(browser, log_fn=lambda m: log(f"[benben] {m}"))
        crawler = BenbenCrawler(
            context=context,
            task_id=task_id,
            city=str(city or ""),
            supplier_ids=str(supplier_ids or ""),
            brand_names=str(brand_names or ""),
            single_sku_max_crawl_count=max(int(single_sku_max_crawl_count or 0), 0),
        )

        if not crawler.prepare_shared_query([sku]):
            raise RuntimeError("prepare_shared_query failed")

        records = crawler.crawl_sku(
            sku=sku,
            quality_origin_ids=str(quality_origin_ids or ""),
            supplier_ids=str(supplier_ids or ""),
            brand_names=str(brand_names or ""),
            region_origin_ids=str(region_origin_ids or ""),
        )
        preview = preview_records(records, preview_count)
        result = {
            "taskId": task_id,
            "sku": sku,
            "request": {
                "qualityOriginIds": quality_origin_ids,
                "supplierIds": supplier_ids,
                "brandNames": brand_names,
                "regionOriginIds": region_origin_ids,
                "city": city,
                "singleSkuMaxCrawlCount": single_sku_max_crawl_count,
            },
            "count": len(records),
            "preview": preview,
            "records": records,
        }

        log(f"[debug] done, count={len(records)}")
        log(json.dumps({"count": len(records), "preview": preview}, ensure_ascii=False, indent=2))
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            log(f"[debug] saved output to {output_path}")
    finally:
        browser.stop()
    return 0


if __name__ == "__main__":
    main()
