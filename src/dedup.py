# -*- coding: utf-8 -*-
"""HIGHLAND CAPITAL - 资讯管线第二道：去重 (Deduplication)
规则要求（按原文规范严格实现）：
1. 相同 id 幂等覆盖/去重；
2. 24 小时内标题 2-gram Dice 相似度超过 0.8 直接判重，保留信息更全的一条。
"""
import os
import sys
import re
from datetime import datetime
from typing import List, Dict, Set

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DICE_SIMILARITY_THRESHOLD, DEDUP_WINDOW_HOURS

def _clean_title(text: str) -> str:
    """去除特殊符号、空格、标签等，提取核心词元"""
    text = re.sub(r"【.*?】|\[.*?\]|（.*?）|\(.*?\)", "", text)
    text = re.sub(r"[^\w\u4e00-\u9fa5]", "", text)
    return text.strip().lower()

def _get_2grams(text: str) -> Set[str]:
    """生成字符级 2-gram 集合"""
    cleaned = _clean_title(text)
    if len(cleaned) < 2:
        return {cleaned} if cleaned else set()
    return {cleaned[i:i+2] for i in range(len(cleaned) - 1)}

def dice_similarity(text_a: str, text_b: str) -> float:
    """计算两个标题的 2-gram Dice 相似度系数
    Dice = 2 * |A ∩ B| / (|A| + |B|)
    """
    if text_a == text_b:
        return 1.0
    
    grams_a = _get_2grams(text_a)
    grams_b = _get_2grams(text_b)
    
    if not grams_a and not grams_b:
        return 1.0 if text_a == text_b else 0.0
    if not grams_a or not grams_b:
        return 0.0
    
    intersection = len(grams_a.intersection(grams_b))
    total = len(grams_a) + len(grams_b)
    if total == 0:
        return 0.0
    return (2.0 * intersection) / float(total)

def parse_time(ts_str: str) -> datetime:
    """尝试将时间字符串解析为 datetime"""
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%Y/%m/%d %H:%M:%S"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(ts_str.strip(), fmt)
        except Exception:
            pass
    return datetime.now()

def deduplicate_news(items: List[Dict]) -> List[Dict]:
    """对新闻列表执行幂等去重与 24 小时 2-gram Dice 相似度判重
    返回去重后的精炼列表
    """
    # 1. 唯一 ID 幂等去重
    unique_by_id = {}
    for item in items:
        item_id = item.get("id")
        if item_id:
            # 若重复，保留内容更详尽者
            if item_id in unique_by_id:
                if len(item.get("content", "")) > len(unique_by_id[item_id].get("content", "")):
                    unique_by_id[item_id] = item
            else:
                unique_by_id[item_id] = item
        else:
            unique_by_id[str(len(unique_by_id))] = item
            
    sorted_items = sorted(
        unique_by_id.values(),
        key=lambda x: parse_time(x.get("timestamp", "")),
        reverse=True
    )
    
    # 2. 2-gram Dice 语义相似度判重（24小时窗口内）
    deduped: List[Dict] = []
    dropped_count = 0
    
    for item in sorted_items:
        title_curr = item.get("title", "")
        time_curr = parse_time(item.get("timestamp", ""))
        is_duplicate = False
        
        for kept in deduped:
            time_kept = parse_time(kept.get("timestamp", ""))
            hours_diff = abs((time_curr - time_kept).total_seconds()) / 3600.0
            
            # 仅在 24 小时窗口内进行相似度查重
            if hours_diff <= DEDUP_WINDOW_HOURS:
                sim = dice_similarity(title_curr, kept.get("title", ""))
                if sim >= DICE_SIMILARITY_THRESHOLD:
                    is_duplicate = True
                    # 如果当前条目内容更长更详尽，替换已有条目
                    if len(item.get("content", "")) > len(kept.get("content", "")):
                        kept["content"] = item["content"]
                        kept["title"] = item["title"]
                    break
        
        if not is_duplicate:
            deduped.append(item)
        else:
            dropped_count += 1
            
    return deduped

if __name__ == "__main__":
    t1 = "英伟达发布第三季度财报，营收大幅超预期"
    t2 = "英伟达公布Q3财报营收超预期，数据中心强劲"
    t3 = "美联储决议维持利率不变，鲍威尔发表鸽派言论"
    print(f"t1 与 t2 Dice 相似度: {dice_similarity(t1, t2):.3f}")
    print(f"t1 与 t3 Dice 相似度: {dice_similarity(t1, t3):.3f}")
