# -*- coding: utf-8 -*-
"""HIGHLAND CAPITAL - 资讯管线第五道：成稿与发布 (Publisher)
功能：
1. 组装符合系统契约的标准 brief JSON (含日期、今日倾向、S/A 顶级新闻、中枢大脑三轮推理、两本账概况、时间线、六人日记立场、天气与大盘快照)
2. 保存至 data/brief_YYYY-MM-DD.json 及 data/brief_latest.json (供前端 3D Loft / 看板直接读取)
3. 渲染生成 Markdown 格式的《HIGHLAND CAPITAL 开盘前晨会简报》，存至 reports/brief_YYYY-MM-DD.md
"""
import json
import os
import sys
from datetime import datetime
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATA_DIR, REPORTS_DIR

def build_brief_payload(
    date_str: str,
    sentiment_res: Dict,
    top_items: List[Dict],
    all_items: List[Dict],
    weather_info: Dict,
    market_snapshot: Dict,
    agents_brief: List[Dict] = None,
    brain_reasoning: Dict = None,
    portfolio_overview: Dict = None
) -> dict:
    """构建标准 brief 数据契约对象"""
    # 提取最重要消息 (优先 S/A 级)
    top_news_titles = [item.get("title", "") for item in top_items[:5] if item.get("title")]
    
    # 提取时间线列表 (按时间倒序)
    timeline = []
    for item in all_items[:30]:
        ts = item.get("timestamp", "")
        time_part = ts.split(" ")[1] if " " in ts else ts[-8:]
        timeline.append({
            "time": time_part,
            "text": item.get("title", ""),
            "impact": item.get("sentiment_label", "中性"),
            "level": item.get("level", "C"),
            "weight": item.get("composite_weight", 1.0),
            "source": item.get("source", "")
        })

    payload = {
        "schemaVersion": "v1",
        "date": date_str,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "lean": sentiment_res.get("lean", "中性"),
        "lean_score": sentiment_res.get("score", 0.0),
        "divergence": sentiment_res.get("divergence", False),
        "sample_count": sentiment_res.get("valid_samples", 0),
        "total_news_count": sentiment_res.get("total_analyzed", 0),
        "sentiment_context": sentiment_res.get("human_readable", ""),
        "weather": weather_info,
        "market_snapshot": market_snapshot,
        "top_news": top_news_titles,
        "agents": agents_brief or [],
        "central_brain": brain_reasoning or {},
        "portfolio_overview": portfolio_overview or {},
        "timeline": timeline
    }
    return payload

def save_and_publish_brief(brief_payload: dict) -> tuple:
    """持久化保存 JSON 并生成 Markdown 晨报"""
    date_str = brief_payload["date"]
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. 保存按日期归档的 JSON
    daily_json_path = DATA_DIR / f"brief_{date_str}.json"
    latest_json_path = DATA_DIR / "brief_latest.json"
    
    with open(daily_json_path, "w", encoding="utf-8") as f:
        json.dump(brief_payload, f, ensure_ascii=False, indent=2)
    
    with open(latest_json_path, "w", encoding="utf-8") as f:
        json.dump(brief_payload, f, ensure_ascii=False, indent=2)
        
    # 2. 渲染 Markdown 报告
    md_content = render_markdown_report(brief_payload)
    md_path = REPORTS_DIR / f"brief_{date_str}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
        
    return str(daily_json_path), str(md_path)

def render_markdown_report(data: dict) -> str:
    """将结构化简报渲染成专业易读的 Markdown 晨报"""
    date = data["date"]
    lean = data["lean"]
    score = data["lean_score"]
    divergence_str = "⚠️ 多空分歧显著" if data.get("divergence") else "✅ 多空分歧平缓"
    context = data.get("sentiment_context", "")
    weather = data.get("weather", {}).get("beijing", {})
    market = data.get("market_snapshot", {})
    brain = data.get("central_brain", {})
    portfolio = data.get("portfolio_overview", {})
    
    md = []
    md.append(f"# HIGHLAND CAPITAL 开盘前晨会简报 ({date})")
    md.append(f"> 抓取与计算时间：{data['timestamp']} | 契约版本：`schemaVersion={data['schemaVersion']}`")
    md.append(f"> 真实天气：北京 {weather.get('weather_desc', '晴')} {weather.get('temperature', '-')}°C | 风速 {weather.get('windspeed', '-')} km/h")
    md.append("")
    
    # 今日倾向总览
    md.append("## 一、今日盘前倾向与情绪总览")
    md.append(f"- **综合倾向**：`{lean}` (得分: `{score:+.3f}`，方向阈值 ±0.10)")
    md.append(f"- **分歧状态**：{divergence_str}")
    md.append(f"- **样本规模**：共清洗过滤 {data.get('total_news_count', 0)} 条资讯，其中 {data.get('sample_count', 0)} 条有效进入多空加权计算")
    md.append(f"- **情绪账本结论（原样送入提示词）**：\n  > {context}")
    md.append("")

    # 中枢大脑三轮推理
    if brain:
        md.append("## 二、交易台中枢大脑·固定三轮推理")
        md.append(f"### R1·市场地图快推\n{brain.get('r1_market_map', '未生成')}\n")
        md.append(f"### R2·组合诊断快推\n{brain.get('r2_portfolio_diag', '未生成')}\n")
        md.append(f"### R3·终稿深推\n> **核心研判**：{brain.get('r3_executive_synthesis', '未生成')}\n")

    # 虚拟账户两本账概况
    if portfolio:
        a_acc = portfolio.get("a_share", {})
        us_acc = portfolio.get("us_share", {})
        comb = portfolio.get("combined", {})
        md.append("## 三、账户与持仓两本账（折算监控）")
        md.append(f"- **两账折算总资产**：`{comb.get('total_assets_cny', 0.0)} CNY`（综合现金率：`{comb.get('overall_cash_ratio_pct', 0.0)}%`）")
        md.append(f"- **A 股账户**：资产 `{a_acc.get('total_assets', 0.0)} CNY`，现金 `{a_acc.get('cash', 0.0)} CNY` ({a_acc.get('cash_ratio_pct', 0.0)}%)，Top1集中度 `{a_acc.get('top1_concentration_pct', 0.0)}%`")
        md.append(f"- **美股账户**：资产 `{us_acc.get('total_assets', 0.0)} USD`，现金 `{us_acc.get('cash', 0.0)} USD` ({us_acc.get('cash_ratio_pct', 0.0)}%)")
        md.append("")
    
    # 昨日收盘真实行情
    md.append("## 四、昨日收盘真实行情快照（基准数据源）")
    md.append("| 指数名称 | 代码 | 最新价格 | 涨跌幅 | 涨跌点数 | 成交额(亿元) |")
    md.append("|---|---|---|---|---|---|")
    for name, m in market.items():
        if name.startswith("_"):
            continue
        p = m.get("price", "未提供")
        chg = f"{m.get('chg_pct', 0.0):+.2f}%" if isinstance(m.get('chg_pct'), (int, float)) else "未提供"
        pts = f"{m.get('chg_pts', 0.0):+.2f}" if isinstance(m.get('chg_pts'), (int, float)) else "未提供"
        amt = m.get("amount_yi", "未提供")
        code = m.get("code", "")
        md.append(f"| **{name}** | `{code}` | {p} | {chg} | {pts} | {amt} |")
    md.append("")
    
    # 核心 S / A 级隔夜要闻
    md.append("## 五、今日核心隔夜要闻 (S / A 级等级过滤)")
    for i, title in enumerate(data.get("top_news", []), 1):
        md.append(f"{i}. {title}")
    md.append("")
    
    # 六位交易员盘前日记
    md.append("## 六、六位交易员开盘前日记 (不同期限与投资风格)")
    md.append("| 交易员 | 风格与期限 | 主数据源 | 倾向 | 盘前开盘日记正文 |")
    md.append("|---|---|---|---|---|")
    for ag in data.get("agents", []):
        name = ag.get("name") or ag.get("trader_name", "")
        style = ag.get("style", "")
        src = ag.get("primary_source", "专属免费源")
        stance = ag.get("stance") or ag.get("lean", "中性")
        summ = ag.get("summary") or ag.get("content", "")
        md.append(f"| **{name}** | {style} | {src} | `{stance}` | {summ} |")
    md.append("")
    
    # 隔夜资讯流
    md.append("## 七、隔夜资讯时间线流 (最新 15 条)")
    md.append("| 时间 | 级别 | 方向 | 标题 | 来源 |")
    md.append("|---|---|---|---|---|")
    for t in data.get("timeline", [])[:15]:
        tm = t.get("time", "")
        lvl = t.get("level", "C")
        imp = t.get("impact", "中性")
        txt = t.get("text", "")
        src = t.get("source", "")
        md.append(f"| {tm} | `{lvl}` | {imp} | {txt} | {src} |")
    md.append("")
    
    md.append("---")
    md.append("> **纪律红线**：本简报仅供量化研判与参考，绝不下单、不生成交易指令；所有行情数据均来自真实数据源。")
    return "\n".join(md)
