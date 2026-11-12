# -*- coding: utf-8 -*-
"""HIGHLAND CAPITAL - 资讯管线总调度入口 (Pipeline Orchestrator)
按顺序串接全流程：
1. [资讯管线] 接入 (ingest) -> 去重 (dedup) -> 定级 (classify) -> 情绪 (sentiment)
2. [环境感知] 真实天气 (Open-Meteo) 与真实大盘行情 (Tencent/AkShare)
3. [六位交易员] 依据各自期限与投资风格，读取同一情绪账本，写开盘前交易日记留痕
4. [中枢大脑] 固定三轮推理 (R1 市场地图 -> R2 组合诊断 -> R3 终稿深推)
5. [两本账户] A 股与美股虚拟账户诊断与统一折算
6. [成稿发布] 统一生成标准契约 JSON 与人类可读 Markdown 晨报
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.ingest import ingest_batch
from src.dedup import deduplicate_news
from src.classify import classify_all
from src.sentiment import calculate_aggregate_sentiment
from src.market_weather import fetch_all_cities_weather, fetch_market_indices
from src.virtual_accounts import VirtualAccountManager
from src.traders import TraderTeam
from src.central_brain import CentralBrain
from src.diaries import DiaryManager
from src.publisher import build_brief_payload, save_and_publish_brief

def run_pipeline() -> dict:
    """运行完整盘前资讯管线与智能交易员研判全流程"""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    print(f"[{now.strftime('%H:%M:%S')}] ===== HIGHLAND CAPITAL 盘前全管线启动 =====")
    
    # 1. 资讯接入
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [1/6 接入] 正在从财联社与东财聚合隔夜快讯...")
    batch_raw = ingest_batch()
    raw_items = batch_raw.get("items", [])
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [1/6 接入] 原始拉取 {len(raw_items)} 条资讯。")
    
    # 2. 去重
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [2/6 去重] 正在执行 24 小时 2-gram Dice 相似度过滤...")
    deduped_items = deduplicate_news(raw_items)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [2/6 去重] 过滤冗余后保留 {len(deduped_items)} 条独特资讯。")
    
    # 3. 定级
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [3/6 定级] 正在执行 S/A/B/C/D 五级金字塔影响度定级...")
    classified_items = classify_all(deduped_items)
    s_count = sum(1 for it in classified_items if it.get("level") == "S")
    a_count = sum(1 for it in classified_items if it.get("level") == "A")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [3/6 定级] 完成。核心 S/A 级共 {s_count + a_count} 条。")
    
    # 4. 情绪计算
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [4/6 情绪] 正在依据公式 S=Σ(s*L*c*d)/Σ(L*c*d) 计算情绪分与衰减...")
    sentiment_res = calculate_aggregate_sentiment(classified_items)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [4/6 情绪] 得分: {sentiment_res['score']:+.3f} | 倾向: {sentiment_res['lean']} | 分歧: {sentiment_res['divergence']}")
    
    # 外部环境：真实天气与真实市场
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [外部数据] 获取 Open-Meteo 天气与真实市场行情快照...")
    weather_info = fetch_all_cities_weather()
    market_snapshot = fetch_market_indices()
    
    # 提取 S/A 重点新闻
    top_items = [it for it in sentiment_res["processed_items"] if it.get("level") in ["S", "A"]]
    if len(top_items) < 3:
        top_items = sentiment_res["processed_items"][:5]
    top_news_titles = [it.get("title", "") for it in top_items[:5]]
    
    # 5. 虚拟账户诊断
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [账户诊断] 正在统计 A 股与美股两本账持仓与集中度...")
    account_mgr = VirtualAccountManager()
    portfolio_overview = account_mgr.get_combined_overview()
    
    # 6. 六位交易员写早盘日记
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [交易员日记] 触发六位交易员开盘前撰写【今天看什么】日记留痕...")
    diary_mgr = DiaryManager()
    diaries_res = diary_mgr.record_session_diaries("morning", "A股", date_str)
    morning_diaries = diaries_res["sessions"]["morning"]
    
    # 7. 中枢大脑三轮推理
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [中枢大脑] 正在执行三轮推理 (R1地图 -> R2诊断 -> R3深推)...")
    brain = CentralBrain()
    brain_res = brain.run_three_round_reasoning(sentiment_res, top_news_titles, morning_diaries)
    
    # 8. 成稿与发布
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [成稿发布] 组装标准化数据契约并生成 Markdown 晨报...")
    brief_payload = build_brief_payload(
        date_str=date_str,
        sentiment_res=sentiment_res,
        top_items=top_items,
        all_items=sentiment_res["processed_items"],
        weather_info=weather_info,
        market_snapshot=market_snapshot,
        agents_brief=morning_diaries,
        brain_reasoning=brain_res,
        portfolio_overview=portfolio_overview
    )
    
    json_path, md_path = save_and_publish_brief(brief_payload)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [成稿发布] 发布完成！")
    print(f"  - 数据 JSON: {json_path}")
    print(f"  - 晨报 Markdown: {md_path}")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ===== 全流程执行完毕 =====")
    
    return brief_payload

if __name__ == "__main__":
    run_pipeline()
