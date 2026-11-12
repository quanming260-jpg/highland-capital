# -*- coding: utf-8 -*-
"""HIGHLAND CAPITAL - 资讯管线第一道：资讯接入 (Ingestion)
契约要求：
- schemaVersion=v1 格式校验
- 聚合主流免费源：财联社电报 (cls) + 东财全球资讯 (eastmoney)
- 每个批次写入 data/raw/batch_YYYYMMDD_HHMMSS.json 单独归档
"""
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path
import akshare as ak

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SCHEMA_VERSION, RAW_DATA_DIR

def _generate_news_id(source: str, title: str, timestamp: str) -> str:
    """生成唯一确定性 ID，保证幂等去重"""
    raw = f"{source}_{title}_{timestamp}".encode("utf-8")
    return hashlib.md5(raw).hexdigest()[:16]

def fetch_cls_news() -> list:
    """抓取财联社全球快讯 (分钟级)"""
    items = []
    try:
        df = ak.stock_info_global_cls()
        for _, row in df.iterrows():
            title = str(row.get("标题", "")).strip()
            content = str(row.get("内容", "")).strip()
            pub_date = str(row.get("发布日期", "")).strip()
            pub_time = str(row.get("发布时间", "")).strip()
            
            ts_str = f"{pub_date} {pub_time}".strip()
            if not ts_str:
                ts_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 若标题为空，则以内容前30字符作为标题
            if not title and content:
                title = content[:30] + ("..." if len(content) > 30 else "")
            
            if not title and not content:
                continue
            
            item_id = _generate_news_id("cls", title, ts_str)
            items.append({
                "id": item_id,
                "title": title,
                "content": content,
                "timestamp": ts_str,
                "source": "财联社电报",
                "source_code": "cls",
                "url": "",
                "raw_impact_level": "normal"
            })
    except Exception as e:
        print(f"[Warn] 抓取财联社资讯异常: {e}")
    return items

def fetch_eastmoney_news() -> list:
    """抓取东财 7x24 全球快讯"""
    items = []
    try:
        df = ak.stock_info_global_em()
        for _, row in df.iterrows():
            title = str(row.get("标题", "")).strip()
            content = str(row.get("摘要", "")).strip()
            ts_str = str(row.get("发布时间", "")).strip()
            url = str(row.get("链接", "")).strip()
            
            if not ts_str:
                ts_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if not title and content:
                title = content[:30] + ("..." if len(content) > 30 else "")
            
            if not title and not content:
                continue
            
            item_id = _generate_news_id("em", title, ts_str)
            items.append({
                "id": item_id,
                "title": title,
                "content": content,
                "timestamp": ts_str,
                "source": "东财全球资讯",
                "source_code": "eastmoney",
                "url": url,
                "raw_impact_level": "normal"
            })
    except Exception as e:
        print(f"[Warn] 抓取东财资讯异常: {e}")
    return items

def ingest_batch() -> dict:
    """聚合多源并生成符合 schemaVersion=v1 规范的归档批次"""
    cls_items = fetch_cls_news()
    em_items = fetch_eastmoney_news()
    
    # 初步按 id 幂等合并
    merged_map = {}
    for item in cls_items + em_items:
        merged_map[item["id"]] = item
    
    all_items = list(merged_map.values())
    
    # 构造标准批次对象
    batch_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    batch_slug = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    batch_payload = {
        "schemaVersion": SCHEMA_VERSION,
        "batchId": f"batch_{batch_slug}",
        "collectedAt": batch_time,
        "totalItems": len(all_items),
        "sources": {
            "cls_count": len(cls_items),
            "eastmoney_count": len(em_items)
        },
        "items": all_items
    }
    
    # 归档到 data/raw/
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    archive_path = RAW_DATA_DIR / f"batch_{batch_slug}.json"
    with open(archive_path, "w", encoding="utf-8") as f:
        json.dump(batch_payload, f, ensure_ascii=False, indent=2)
    
    return batch_payload

if __name__ == "__main__":
    res = ingest_batch()
    print(f"接入完成: 批次 {res['batchId']}, 共拉取 {res['totalItems']} 条资讯，归档完成。")
