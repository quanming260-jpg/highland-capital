# -*- coding: utf-8 -*-
"""HIGHLAND CAPITAL - 资讯管线第四道：情绪计算 (Sentiment Engine)
严格遵循抖音 CLOVIS 原文数学公式实现：
S = Σ(s * L * c * d) / Σ(L * c * d)
- s: 方向 (+1 利好偏多 / -1 利空偏空 / 0 中性)
- L: 等级权重 (S=5, A=4, B=3, C=2, D=1)
- c: 把握度 / 置信度 (0.0 ~ 1.0)
- d: 时间衰减系数，半衰期默认 12 小时：d = 0.5 ** (Δt / 12)

规则红线：
1. 默认至少 5 个有效样本；
2. ±0.10 为方向分水岭；
3. 多空权重同时偏高时，标记 "分歧大"；
4. 情绪结论是原样进入提示词的文字，而非写死的买卖规则。
"""
import os
import sys
import re
import math
from datetime import datetime
from typing import List, Dict, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    SENTIMENT_HALF_LIFE_HOURS,
    MIN_EFFECTIVE_SAMPLES,
    SENTIMENT_DIRECTION_THRESHOLD,
    DIVERGENCE_RATIO_THRESHOLD,
    LEVEL_WEIGHTS
)

# 利好/偏多特征词
BULLISH_KEYWORDS = [
    "超预期", "大幅增长", "大增", "翻倍", "净流入", "利好", "回购", "增持", "扭亏",
    "降准", "降息", "刺激政策", "战略合作", "中标", "突破", "创新高", "扩产", "提价",
    "分红", "稳健增长", "放量大涨", "鸽派", "获批", "复苏", "景气上行"
]

# 利空/偏空特征词
BEARISH_KEYWORDS = [
    "不及预期", "大幅下降", "大跌", "亏损扩大", "净流出", "利空", "减持", "清仓",
    "暴雷", "立案调查", "违约", "破产", "加征关税", "制裁", "下修", "通缩",
    "警示函", "处罚", "跌停", "承压", "下调评级", "鹰派", "放缓", "衰退"
]

def evaluate_single_sentiment(item: Dict, now_dt: datetime) -> Dict:
    """分析单条资讯的 s(方向)、c(把握度)、d(时间衰减) 与复合权重"""
    title = item.get("title", "")
    content = item.get("content", "")
    text = f"{title} {content}".lower()
    
    # 1. 计算方向 s 与置信度 c
    bull_hits = sum(1 for kw in BULLISH_KEYWORDS if kw in text)
    bear_hits = sum(1 for kw in BEARISH_KEYWORDS if kw in text)
    
    if bull_hits > bear_hits:
        s = 1.0
        # 根据命中密度计算把握度 c (0.6 ~ 0.95)
        c = min(0.95, 0.65 + 0.10 * (bull_hits - bear_hits))
        sentiment_label = "利好"
    elif bear_hits > bull_hits:
        s = -1.0
        c = min(0.95, 0.65 + 0.10 * (bear_hits - bull_hits))
        sentiment_label = "利空"
    else:
        s = 0.0
        c = 0.50
        sentiment_label = "中性"
        
    # 2. 等级权重 L
    level = item.get("level", "C")
    L = item.get("level_weight", LEVEL_WEIGHTS.get(level, 2.0))
    
    # 3. 时间衰减 d (半衰期 12 小时)
    # d = 0.5 ** (Δt / 12)
    ts_str = item.get("timestamp", "")
    try:
        formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"]
        item_dt = None
        for fmt in formats:
            try:
                item_dt = datetime.strptime(ts_str.strip(), fmt)
                break
            except Exception:
                pass
        if not item_dt:
            item_dt = now_dt
        
        delta_hours = max(0.0, (now_dt - item_dt).total_seconds() / 3600.0)
        d = math.pow(0.5, delta_hours / SENTIMENT_HALF_LIFE_HOURS)
    except Exception:
        delta_hours = 0.0
        d = 1.0
        
    composite_weight = L * c * d
    
    item["sentiment_dir"] = s
    item["confidence"] = round(c, 3)
    item["time_decay"] = round(d, 3)
    item["composite_weight"] = round(composite_weight, 4)
    item["sentiment_label"] = sentiment_label
    item["delta_hours"] = round(delta_hours, 1)
    
    return item

def calculate_aggregate_sentiment(items: List[Dict]) -> Dict:
    """按全局公式计算加权情绪综合得分及分歧度"""
    now_dt = datetime.now()
    
    processed_items = [evaluate_single_sentiment(it, now_dt) for it in items]
    
    total_numerator = 0.0    # Σ(s * L * c * d)
    total_denominator = 0.0  # Σ(L * c * d)
    
    pos_weight = 0.0         # 多头权重
    neg_weight = 0.0         # 空头权重
    neutral_weight = 0.0     # 中性权重
    
    valid_count = 0
    
    for it in processed_items:
        s = it["sentiment_dir"]
        cw = it["composite_weight"]
        
        total_numerator += (s * cw)
        total_denominator += cw
        
        if s > 0:
            pos_weight += cw
            valid_count += 1
        elif s < 0:
            neg_weight += cw
            valid_count += 1
        else:
            neutral_weight += cw
            
    # 计算加权综合分 S
    if total_denominator > 0:
        raw_score = total_numerator / total_denominator
    else:
        raw_score = 0.0
        
    score = round(raw_score, 4)
    
    # 分歧度判定：多头和空头各自占比是否均达到阈值
    is_divergence = False
    if total_denominator > 0:
        pos_ratio = pos_weight / total_denominator
        neg_ratio = neg_weight / total_denominator
        if pos_ratio >= DIVERGENCE_RATIO_THRESHOLD and neg_ratio >= DIVERGENCE_RATIO_THRESHOLD:
            is_divergence = True
    else:
        pos_ratio = 0.0
        neg_ratio = 0.0
        
    # 判断基本倾向方向
    if valid_count < MIN_EFFECTIVE_SAMPLES:
        lean_status = "样本不足（中性）"
        human_readable = f"有效多空样本较少({valid_count}条)，信号偏弱，建议轻度观望。"
    elif score > SENTIMENT_DIRECTION_THRESHOLD:
        lean_status = "偏多"
        if is_divergence:
            human_readable = f"综合情绪偏多 (+{score:.2f})，但多空分歧显著(多占{pos_ratio*100:.0f}%, 空占{neg_ratio*100:.0f}%)，警惕冲高回落。"
        else:
            human_readable = f"综合情绪显著偏多 (+{score:.2f})，积极催化占优，多方动能占主导。"
    elif score < -SENTIMENT_DIRECTION_THRESHOLD:
        lean_status = "偏空"
        if is_divergence:
            human_readable = f"综合情绪偏空 ({score:.2f})，且存在多空分歧，防守防御为先。"
        else:
            human_readable = f"综合情绪明显承压 ({score:.2f})，负面消息集中释放，维持防卫状态。"
    else:
        lean_status = "中性"
        if is_divergence:
            human_readable = f"综合情绪平衡 ({score:+.2f})，但多空分歧激烈，静待方向突破。"
        else:
            human_readable = f"综合情绪温和平衡 ({score:+.2f})，隔夜消息面整体平稳。"
            
    return {
        "score": score,
        "lean": lean_status,
        "divergence": is_divergence,
        "valid_samples": valid_count,
        "total_analyzed": len(processed_items),
        "pos_ratio": round(pos_ratio, 3),
        "neg_ratio": round(neg_ratio, 3),
        "human_readable": human_readable,
        "processed_items": processed_items
    }

if __name__ == "__main__":
    test_data = [
        {"title": "芯片板块迎来重大利好，万亿扶持政策出台", "content": "全面支持芯片研发与算力基础设施", "level": "S", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        {"title": "某白酒龙头三季报净利润大增30%，超市场预期", "content": "现金流充沛", "level": "A", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        {"title": "外部突发加征关税言论，外围市场全线承压暴跌", "content": "避险情绪升温", "level": "S", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        {"title": "10月CPI数据温和微涨，物价总体平稳", "content": "符合预期", "level": "A", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        {"title": "某软件公司股东拟减持不超过2%股份", "content": "日常减持", "level": "B", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
    ]
    res = calculate_aggregate_sentiment(test_data)
    print("情绪打分测试结果:")
    print(f"得分: {res['score']}, 倾向: {res['lean']}, 分歧: {res['divergence']}")
    print(f"结论文字 (原样入提示词): {res['human_readable']}")
