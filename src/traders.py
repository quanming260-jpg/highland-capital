# -*- coding: utf-8 -*-
"""HIGHLAND CAPITAL - 六位独立风格交易员 (Six Traders)
按原文规范严格实现：
- 不是按“基本面/技术面/情绪”职能分工！
- 六人是六位有作息的 AI 交易员，共用统一交易框架，核心区别在【策略期限】和【投资风格】。
- 共同读同一本情绪账本，各自分别对接不同的免费主数据源。
- 严守红线：只给参考研判，绝不下单、不创建交易指令。
"""
import os
import sys
from typing import Dict, List
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TRADERS_CONFIG
from src.llm_client import GLOBAL_LLM
from src.fallback_corpus import generate_fallback_diary

class TraderAgent:
    """单个 AI 交易员实体"""
    def __init__(self, trader_id: str):
        self.cfg = TRADERS_CONFIG.get(trader_id, {})
        self.trader_id = trader_id
        self.name = self.cfg.get("name", trader_id)
        self.alias = self.cfg.get("alias", trader_id)
        self.horizon = self.cfg.get("horizon", "中短线")
        self.style = self.cfg.get("style", "均衡")
        self.primary_source = self.cfg.get("primary_source", "")
        self.focus = self.cfg.get("focus", "")
        self.enabled = self.cfg.get("enabled", True)

    def build_system_prompt(self, sentiment_context: str) -> str:
        """构建交易员个性系统提示词（情绪账本结论原样送入提示词）"""
        prompt = f"""你现在是 HIGHLAND CAPITAL 虚拟交易工作室的交易员：【{self.name}】（{self.alias}）。
你的策略期限：【{self.horizon}】。
你的投资风格：【{self.style}】。
你的专属主数据源：【{self.primary_source}】。
你的观察重心：【{self.focus}】。

【全工作室共享情绪账本（原样事实输入）】
{sentiment_context}

【你的行为与原则准则】
1. 始终严格遵照你的投资风格与期限说话，不要抢其他人的风格；
2. 你只给出专业参考意见与逻辑推演，严禁生成任何下单指令、不创建订单；
3. 所有提及的价格涨跌数字必须来自输入中的客观事实，没有数据明确说“未提供”，严禁编造任何数字；
4. 言辞专业、犀利、克制，直切要害。"""
        return prompt.strip()

    def write_diary(self, session: str, sentiment_data: dict, market_snapshot: dict) -> dict:
        """根据当前时段写交易日记 (session: morning | midday | closing)"""
        if not self.enabled:
            return {
                "trader_id": self.trader_id,
                "trader_name": self.name,
                "status": "disabled",
                "content": f"{self.name} 当前处于停用休假状态。"
            }

        sentiment_context = sentiment_data.get("sentiment_context", "")
        sentiment_score = sentiment_data.get("score", 0.0)
        lean = sentiment_data.get("lean", "中性")
        sys_prompt = self.build_system_prompt(sentiment_context)
        
        session_names = {
            "morning": "【开盘前日记：今天看什么】",
            "midday": "【午间复盘日记：上午发生了什么、要不要改】",
            "closing": "【收盘前日记：今天做没做、为什么】"
        }
        session_title = session_names.get(session, "【交易日记】")
        
        user_prompt = f"""现在是交易日【{session_title}】时段。
当前市场大盘真实快照：{market_snapshot}
当前全市场综合情绪得分：{sentiment_score:+.3f}（倾向：{lean}）。
请从你【{self.horizon} · {self.style}】的独特视角，写一段简短精炼的今日交易日记（150字以内）。
要求包含：今天核心关注点、你的研判倾向（偏多/中性/偏空）与应对逻辑。"""

        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # 兜底函数
        def _fallback():
            return generate_fallback_diary(self.trader_id, session, {
                "sentiment_score": sentiment_score,
                "sentiment_lean": lean,
                "pos_ratio": sentiment_data.get("pos_ratio", 0.18),
                "neg_ratio": sentiment_data.get("neg_ratio", 0.03),
                "divergence": sentiment_data.get("divergence", False)
            })["content"]

        diary_text = GLOBAL_LLM.query(messages, fallback_fn=_fallback)

        return {
            "trader_id": self.trader_id,
            "trader_name": self.name,
            "alias": self.alias,
            "horizon": self.horizon,
            "style": self.style,
            "session": session,
            "session_title": session_title,
            "lean": lean,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "content": diary_text.strip()
        }

class TraderTeam:
    """管理六位交易员的团队调度器"""
    def __init__(self):
        self.traders = {t_id: TraderAgent(t_id) for t_id in TRADERS_CONFIG.keys()}

    def get_trader(self, trader_id: str) -> TraderAgent:
        return self.traders.get(trader_id)

    def generate_all_diaries(self, session: str, sentiment_data: dict, market_snapshot: dict) -> List[dict]:
        """按顺序调用全部 6 位交易员记录日记"""
        diaries = []
        for trader_id, agent in self.traders.items():
            if agent.enabled:
                d = agent.write_diary(session, sentiment_data, market_snapshot)
                diaries.append(d)
        return diaries

if __name__ == "__main__":
    team = TraderTeam()
    sample_sentiment = {
        "score": 0.153,
        "lean": "偏多",
        "divergence": False,
        "sentiment_context": "综合情绪显著偏多 (+0.15)，积极催化占优，多方动能占主导。"
    }
    sample_market = {"上证指数": {"price": 3665.36, "chg_pct": -0.42}}
    diaries = team.generate_all_diaries("morning", sample_sentiment, sample_market)
    print(f"成功调用 {len(diaries)} 位交易员生成早盘日记：")
    for d in diaries[:2]:
        print(f"\n[{d['trader_name']} | {d['style']}] {d['session_title']}:\n{d['content']}")
