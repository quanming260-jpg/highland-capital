# -*- coding: utf-8 -*-
"""HIGHLAND CAPITAL - 资讯管线第三道：定级制度 (Classification)
等级金字塔：S / A / B / C / D
- S级：顶级宏观/全球央行降准降息/重磅地缘/金融黑天鹅 (Weight=5)
- A级：核心经济数据(CPI/PMI/社融)/战略产业政策/核心龙头财报超预期或暴雷 (Weight=4)
- B级：行业动态/中报预告/资金流向/大宗交易 (Weight=3)
- C级：个股常规公告/高管变动/一般评论 (Weight=2)
- D级：边缘资讯/噪声/弱相关快讯 (Weight=1)

原则：S 和 A 级享有优先上下文权重与首屏推荐，C/D 沉底。
"""
import os
import sys
import re
from typing import Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import LEVEL_WEIGHTS

# S 级核心关键词模式
PATTERN_S = re.compile(
    r"(美联储|降准|降息|加息|加征关税|国常会|中央政治局|金融监管总局|证监会发布|央行重磅|特别国债|印花税|停牌核查|战争爆发|停火协议|核打击|违约破产|系统性风险|流动性枯竭)",
    re.IGNORECASE
)

# A 级核心关键词模式
PATTERN_A = re.compile(
    r"(CPI|PPI|PMI|GDP|社融|M2|非农|失业率|进出口|超预期|暴雷|净利润暴增|大增|大幅增长|亏损扩大|财报公布|战略重组|算力补贴|芯片补贴|产业扶持政策|反垄断调查|汇率破|人民币离岸|离岸汇率|千亿级|万亿级)",
    re.IGNORECASE
)

# B 级核心关键词模式
PATTERN_B = re.compile(
    r"(行业动态|增持|减持|回购计划|北向资金|净流入|净流出|机构调研|大宗交易|合同中标|中标金额|并购重组|景气度|涨价函|供给受限|扩产|定增)",
    re.IGNORECASE
)

# D 级噪声关键词
PATTERN_D = re.compile(
    r"(天气预报|明星八卦|体育赛事|娱乐新闻|抽奖|广告赞助|招聘公告|例行公事|生活小贴士)",
    re.IGNORECASE
)

def classify_news_item(item: Dict) -> Dict:
    """对单条新闻进行五级等级评定，输出 level, weight, 和定级理由"""
    title = item.get("title", "")
    content = item.get("content", "")
    full_text = f"{title} {content}"
    
    # 1. 优先读取上游标注（若上游已有明确加急/S级标注）
    raw_level = str(item.get("raw_impact_level", "")).lower()
    if raw_level in ["urgent", "breaking", "critical", "s"]:
        level = "S"
        reason = "上游加急推送"
    elif raw_level in ["important", "major", "a"]:
        level = "A"
        reason = "上游重要通知"
    # 2. 规则引擎兜底分级
    elif PATTERN_D.search(full_text):
        level = "D"
        reason = "过滤弱相关或噪声"
    elif PATTERN_S.search(full_text):
        match = PATTERN_S.search(full_text).group(0)
        level = "S"
        reason = f"触发宏观/系统级核心词 [{match}]"
    elif PATTERN_A.search(full_text):
        match = PATTERN_A.search(full_text).group(0)
        level = "A"
        reason = f"触发核心宏观数据/重点产业词 [{match}]"
    elif PATTERN_B.search(full_text):
        match = PATTERN_B.search(full_text).group(0)
        level = "B"
        reason = f"触发行业/资金/重要经营动态词 [{match}]"
    else:
        level = "C"
        reason = "常规市场动态或个股资讯"
    
    item["level"] = level
    item["level_weight"] = LEVEL_WEIGHTS.get(level, 1.0)
    item["classify_reason"] = reason
    return item

def classify_all(items: list) -> list:
    """批量定级并排序：S -> A -> B -> C -> D，同级别按时间倒序"""
    classified = [classify_news_item(item) for item in items]
    
    # 排序权重映射
    rank_order = {"S": 0, "A": 1, "B": 2, "C": 3, "D": 4}
    
    sorted_items = sorted(
        classified,
        key=lambda x: (rank_order.get(x["level"], 99), -x.get("level_weight", 0))
    )
    return sorted_items

if __name__ == "__main__":
    sample = [
        {"title": "央行宣布下调金融机构存款准备金率0.5个百分点", "content": "释放长期流动性约1万亿元"},
        {"title": "国家统计局：10月份规模以上工业企业利润同比增长15.2%", "content": "工业经济恢复向好"},
        {"title": "某某股份关于持股5%以上股东减持完成的公告", "content": "累计减持100万股"},
        {"title": "周末某地举办马拉松比赛，天气晴好", "content": "两万人参加"}
    ]
    res = classify_all(sample)
    for r in res:
        print(f"[{r['level']}级 (权重 {r['level_weight']})] {r['title']} -> {r['classify_reason']}")
