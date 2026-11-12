# -*- coding: utf-8 -*-
"""HIGHLAND CAPITAL - 交易台中枢大脑 (Central Reasoning Brain)
按原文规范严格实现：
中枢大脑不是六位交易员之一，是独立的系统推理层，固定跑三轮推理：
- R1·市场地图快推：板块动向、多空情绪落点、S/A 级重点资讯聚类
- R2·组合诊断快推：持仓集中度、现金比例、风格匹配度、单一标的超标排查（找“哪里不对”）
- R3·终稿深推：前两轮收敛整合，输出一段专业可执行研判、操作建议、核心理由与关键盯盘条件

红线：严守预检与人工确认原则，AI 绝不创建实盘订单。
"""
import os
import sys
from datetime import datetime
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.llm_client import GLOBAL_LLM
from src.virtual_accounts import VirtualAccountManager

class CentralBrain:
    """中枢大脑三轮推理引擎"""
    def __init__(self):
        self.account_mgr = VirtualAccountManager()

    def run_three_round_reasoning(
        self,
        sentiment_data: dict,
        top_news: List[str],
        recent_diaries: List[dict] = None
    ) -> dict:
        """执行完整三轮推理，返回 R1、R2、R3 的全流程结构化成果"""
        combined_portfolio = self.account_mgr.get_combined_overview()
        a_acc = combined_portfolio["a_share"]
        us_acc = combined_portfolio["us_share"]
        
        # 提取关键组合指标
        a_cash_ratio = a_acc["cash_ratio_pct"]
        a_top1_pct = a_acc["top1_concentration_pct"]
        holdings_summary = [f"{h['name']}({h['weight_pct']}%)" for h in a_acc["holdings"]]
        
        # ==========================================
        # R1: 市场地图快推 (Market Map Fast Reasoning)
        # ==========================================
        score = sentiment_data.get("score", 0.0)
        lean = sentiment_data.get("lean", "中性")
        divergence = sentiment_data.get("divergence", False)
        top_news_text = "\n".join([f"- {t}" for t in top_news[:5]])
        
        r1_prompt = f"""【R1·市场地图快推】
输入数据：
- 隔夜全市场综合情绪分：{score:+.3f}（倾向：{lean}）
- 多空分歧状态：{'存在显著多空分歧' if divergence else '分歧平缓'}
- 核心 S/A 级宏观要闻：
{top_news_text}

任务：请以宏观策略总监口吻，进行快速市场地图推演（100字左右）：
1. 概括今天情绪落点偏向哪边；
2. 提炼核心催化或主要拖累线索。"""

        def _fallback_r1():
            div_note = "但多空分歧需警惕脉冲冲高回落" if divergence else "盘面催化较为一致"
            return (
                f"【市场地图】今日隔夜情绪定格为 {lean} ({score:+.2f})，{div_note}。"
                f"核心线索主要集中在利率预期博弈与科技产业支撑。总体偏多氛围中，资金倾向于在防守和成长之间寻找再平衡。"
            )

        r1_output = GLOBAL_LLM.query(
            [{"role": "user", "content": r1_prompt}],
            fallback_fn=_fallback_r1
        ).strip()

        # ==========================================
        # R2: 组合诊断快推 (Portfolio Diagnosis)
        # ==========================================
        r2_prompt = f"""【R2·组合诊断快推】
当前账户结构事实：
- A 股总资产：{a_acc['total_assets']} CNY，现金比例：{a_cash_ratio}%
- 当前持仓：{', '.join(holdings_summary)}
- 单一持仓最高权重：{a_top1_pct}%
- 美股现金比例：{us_acc['cash_ratio_pct']}%

任务：请从风控与组合管理角度，快速诊断“哪里不对”（100字左右）：
1. 评估现金比例是否合理（偏高、适中还是流动性不足）；
2. 检查持仓集中度与行业风格匹配度是否存在单一过度暴露。"""

        def _fallback_r2():
            critique = []
            if a_cash_ratio > 35:
                critique.append(f"现金比例达到 {a_cash_ratio}%，防御厚度充足但可能面临右侧上行时的踏空摩擦。")
            if a_top1_pct > 30:
                critique.append(f"单一标的最高权重占 {a_top1_pct}%，集中度略显偏高，需警惕单一板块黑天鹅。")
            if not critique:
                critique.append("当前组合资产与现金配比保持在稳健安全边界内。")
            return "【组合诊断】" + " ".join(critique)

        r2_output = GLOBAL_LLM.query(
            [{"role": "user", "content": r2_prompt}],
            fallback_fn=_fallback_r2
        ).strip()

        # ==========================================
        # R3: 终稿深推 (Final Executive Synthesis)
        # ==========================================
        r3_prompt = f"""【R3·终稿深推】
前序推演：
- R1 市场地图结论：{r1_output}
- R2 组合诊断结论：{r2_output}

任务：综合上述两轮推演，生成一段可执行的最终操盘研判总纲（150字左右）：
1. 给出今日总基调；
2. 提出明确的组合应对建议（持股观望/择机右侧分批/维持防守）；
3. 明确列出今天需要密切盯紧的 2 个核心观察条件。
严格红线：只给出策略建议，严禁生成任何下单指令。"""

        def _fallback_r3():
            return (
                f"【操盘终稿研判】结合 R1 市场地图与 R2 组合诊断，今日维持‘轻度观望、重在结构’总基调。"
                f"建议策略：现有红利与消费底仓不动，保留现金储备，避免在早盘脉冲中激进追高；"
                f"待盯紧条件：① 关注 14:30 成交量窗口是否出现全市场合力放量；② 观察领涨科技龙头的封板与承接动能。"
            )

        r3_output = GLOBAL_LLM.query(
            [{"role": "user", "content": r3_prompt}],
            fallback_fn=_fallback_r3
        ).strip()

        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "r1_market_map": r1_output,
            "r2_portfolio_diag": r2_output,
            "r3_executive_synthesis": r3_output,
            "portfolio_context": {
                "a_share_total": a_acc["total_assets"],
                "a_cash_ratio_pct": a_cash_ratio,
                "top1_concentration_pct": a_top1_pct
            }
        }

if __name__ == "__main__":
    brain = CentralBrain()
    sample_sentiment = {
        "score": 0.153,
        "lean": "偏多",
        "divergence": False
    }
    sample_top_news = [
        "华尔街紧急上调利率预期！美股最大风险变成美联储？",
        "算力需求再添硬证据，云服务商上调全年营收",
        "证监会：进一步拓宽中长期资金来源、渠道和入市方式"
    ]
    res = brain.run_three_round_reasoning(sample_sentiment, sample_top_news)
    print("=== 中枢大脑三轮推理结果 ===")
    print("R1:", res["r1_market_map"])
    print("\nR2:", res["r2_portfolio_diag"])
    print("\nR3:", res["r3_executive_synthesis"])
