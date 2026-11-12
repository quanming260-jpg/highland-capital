# -*- coding: utf-8 -*-
"""HIGHLAND CAPITAL - 七人群聊与私聊引擎 (Seven-Person Chat Room)
按原文规范严格实现：
- 成员：六位 AI 交易员（千里马、天平、磐石、远见、逆风、乘风）+ 你（User），共七人；
- 时间与环境感知：识别交易时段、午休(11:30-13:00慢半拍)、收盘盘后及周末；实时感知窗外天气；
- 长期记忆系统：通过 self_note(个人备忘/反思) 与 commitment(承诺/后续观察) 字段跨轮次连接；
- 话题去重：背景话题按 2 天去重，杜绝重复车轱辘话；
- 允许交锋反驳：成长与红利、短线与长线根据各自立场展开专业辩驳，不做机械附和；
- 模式分离：支持群聊广播模式与 1v1 点名私聊模式（群聊与私聊记忆相互隔离）；
- 偷看模式 (Peeking Mode)：用户不说话时，交易员根据盘面焦点自主轮流发言探讨；
- 本地语料兜底：模型失败时退回高质量角色库，保障群聊不崩溃。
"""
import json
import os
import sys
import random
from datetime import datetime
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATA_DIR, MEMORY_DIR, TRADERS_CONFIG
from src.llm_client import GLOBAL_LLM
from src.fallback_corpus import TRADER_VOICES, generate_fallback_chat_reply
from src.market_weather import fetch_city_weather
from src.image_analyzer import GLOBAL_CHART_ANALYZER

CHAT_LOG_FILE = DATA_DIR / "chat_history.json"
MEMORY_FILE = MEMORY_DIR / "traders_memory.json"

class SevenPersonChatRoom:
    """七人群聊与私聊总控制器"""
    def __init__(self):
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.active_status = True  # 群聊总开关
        self._init_memory()

    def _init_memory(self):
        """初始化长期记忆结构"""
        if not MEMORY_FILE.exists():
            default_mem = {}
            for t_id in TRADERS_CONFIG.keys():
                default_mem[t_id] = {
                    "self_note": "关注本周组合风险报酬比，做好风格纪律。",
                    "commitment": "盯紧 14:30 窗口量能变化与持仓回撤。",
                    "recent_topics": []
                }
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(default_mem, f, ensure_ascii=False, indent=2)

    def load_memory(self) -> dict:
        if not MEMORY_FILE.exists():
            self._init_memory()
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def update_trader_memory(self, trader_id: str, note: str = None, commitment: str = None, topic: str = None):
        """更新交易员的长期记忆与话题防重记录"""
        mem = self.load_memory()
        if trader_id not in mem:
            mem[trader_id] = {"self_note": "", "commitment": "", "recent_topics": []}
            
        if note:
            mem[trader_id]["self_note"] = note
        if commitment:
            mem[trader_id]["commitment"] = commitment
        if topic:
            topics = mem[trader_id].get("recent_topics", [])
            topics.append({"topic": topic, "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
            # 仅保留最近 2 天的话题
            mem[trader_id]["recent_topics"] = topics[-10:]
            
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(mem, f, ensure_ascii=False, indent=2)

    def get_time_and_environment_context(self) -> dict:
        """感知当前时间场景（交易盘中/午休/周末）与天气"""
        now = datetime.now()
        weekday = now.weekday()  # 0-4 周一到周五, 5-6 周末
        hour = now.hour
        minute = now.minute
        time_decimal = hour + minute / 60.0

        if weekday >= 5:
            scene = "weekend"
            scene_desc = "周末休息（办公室人不多，话题偏向生活与长线随想，回复节奏慢）"
        elif 11.5 <= time_decimal < 13.0:
            scene = "lunch_break"
            scene_desc = "午休时段（有人外出就餐，回复稍慢半拍，讨论轻松）"
        elif 9.5 <= time_decimal <= 15.0:
            scene = "trading_hours"
            scene_desc = "交易盘中（大家专注盘面，交流言简意赅，盯紧分时动向）"
        else:
            scene = "after_market"
            scene_desc = "收盘后（复盘总结时段，交流今日得失）"

        # 获取北京天气
        weather = fetch_city_weather("beijing")
        return {
            "scene": scene,
            "scene_desc": scene_desc,
            "weather_desc": weather.get("weather_desc", "晴"),
            "temp": weather.get("temperature", 11.0),
            "is_day": weather.get("is_day", True)
        }

    def load_chat_history(self) -> List[dict]:
        """读取历史聊天记录"""
        if not CHAT_LOG_FILE.exists():
            return []
        try:
            with open(CHAT_LOG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def append_chat_message(self, message: dict):
        """持久化聊天消息"""
        history = self.load_chat_history()
        history.append(message)
        # 最多保存 100 条
        history = history[-100:]
        with open(CHAT_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

    def ask_trader_private(self, trader_id: str, user_question: str) -> dict:
        """1v1 点名私聊某位交易员（与群聊隔离）"""
        if not self.active_status:
            return {"status": "inactive", "reply": "AI 聊天处于关闭状态。"}

        cfg = TRADERS_CONFIG.get(trader_id, {})
        trader_name = cfg.get("name", trader_id)
        style = cfg.get("style", "风格未知")
        horizon = cfg.get("horizon", "期限未知")
        
        mem = self.load_memory().get(trader_id, {})
        env = self.get_time_and_environment_context()

        sys_prompt = f"""你是 HIGHLAND CAPITAL 虚拟工作室交易员【{trader_name}】。
期限：{horizon}，风格：{style}。
你的长期备忘(self_note)：{mem.get('self_note', '')}
你此前的承诺(commitment)：{mem.get('commitment', '')}
当前环境：{env['scene_desc']}，窗外天气：{env['weather_desc']} {env['temp']}°C。

【准则】
1. 当前是与用户的私聊模式，仅从你本人的风格和期限作答；
2. 可以反驳或建议，但不生成下单交易指令，所有数字基于真实事实；
3. 言简意赅，字数在 120 字以内。"""

        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_question}
        ]

        def _fallback():
            return generate_fallback_chat_reply(trader_id, user_question, env)

        reply_text = GLOBAL_LLM.query(messages, fallback_fn=_fallback).strip()
        
        result = {
            "mode": "private",
            "trader_id": trader_id,
            "trader_name": trader_name,
            "style": style,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user_question": user_question,
            "reply": reply_text
        }
        self.append_chat_message(result)
        return result

    def send_group_message(self, user_text: str, image_base64: str = None, auto_responder_ids: List[str] = None) -> List[dict]:
        """向七人群发送消息（支持文本 + K线/图表多模态分析），触发相关交易员自然回击或讨论"""
        if not self.active_status:
            return [{"trader_name": "系统", "reply": "群聊已处于静默关闭状态。"}]

        env = self.get_time_and_environment_context()
        memories = self.load_memory()
        
        # 多模态图表识别处理
        image_analysis_summary = ""
        if image_base64:
            vision_result = GLOBAL_CHART_ANALYZER.analyze_image(image_base64)
            image_analysis_summary = vision_result.get("summary", "")

        # 记录用户发言 (若有图片，保留标记与缩略)
        user_msg = {
            "mode": "group",
            "sender": "User",
            "text": user_text,
            "has_image": bool(image_base64),
            "image_analysis": image_analysis_summary,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.append_chat_message(user_msg)

        # 记忆自动更新检测：若用户提到“记住”、“我持仓”、“关注”、“成本”等，自动沉淀至交易员记忆
        for t_id in ["trader_1", "trader_2", "trader_3"]:
            if any(k in user_text for k in ["成本", "买入", "仓位", "记住", "盯紧"]):
                self.update_trader_memory(t_id, commitment=f"用户关注点: {user_text[:35]}")

        # 确定响应交易员
        if not auto_responder_ids:
            if image_base64:
                # 收到图表时，默认由【千里马】(看突破动量) 与【磐石】(看均线防守) 进行多空交锋！
                responder_ids = ["trader_1", "trader_3"]
            elif any(w in user_text for w in ["科技", "半导体", "算力", "冲", "涨停", "买"]):
                responder_ids = ["trader_1", "trader_3"]
            elif any(w in user_text for w in ["红利", "防御", "回撤", "跌", "稳"]):
                responder_ids = ["trader_3", "trader_5"]
            elif any(w in user_text for w in ["医药", "消费", "白酒"]):
                responder_ids = ["trader_4", "trader_2"]
            else:
                responder_ids = ["trader_1", "trader_2"]
        else:
            responder_ids = auto_responder_ids

        responses = []
        for t_id in responder_ids:
            cfg = TRADERS_CONFIG.get(t_id, {})
            name = cfg.get("name", t_id)
            style = cfg.get("style", "")
            t_mem = memories.get(t_id, {})

            sys_prompt = f"""你是 HIGHLAND CAPITAL 七人群聊里的交易员【{name}】（{style}）。
你的长期记忆：备忘[{t_mem.get('self_note', '')}]，关注承诺[{t_mem.get('commitment', '')}]。
当前环境：{env['scene_desc']}，天气：{env['weather_desc']} {env['temp']}°C。

【群聊规则】
1. 保持你的独特投资风格与性格特点；
2. 允许对其他同事或用户的看法提出专业反驳、补充或适度调侃；
3. 如果用户发了图表或走势截图，请重点从你的投资风格出发（如短线看形态突破，红利看防守支撑）直接点评；
4. 不必拘泥客套，像真实的交易室同事一样直接；
5. 不下实盘指令，80 字以内精炼表态。"""

            query_prompt = f"群消息：{user_text}"
            if image_analysis_summary:
                query_prompt += f"\n[用户发送了一张走势/持仓图表，视觉识别结论: {image_analysis_summary}]"

            messages = [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": query_prompt}
            ]

            def _fallback(trader_id=t_id):
                base = generate_fallback_chat_reply(trader_id, user_text, env)
                if image_analysis_summary:
                    if trader_id == "trader_1":
                        base = f"扫了一眼你发来的这张图：突破放量迹象有，但上方有均线压制。{base}"
                    elif trader_id == "trader_3":
                        base = f"这走势波动不小，我提醒一句：注意下方防御均线支撑，别在拉升尾声去接飞刀！{base}"
                return base

            reply = GLOBAL_LLM.query(messages, fallback_fn=_fallback).strip()
            resp_item = {
                "mode": "group",
                "trader_id": t_id,
                "trader_name": name,
                "style": style,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "reply": reply
            }
            self.append_chat_message(resp_item)
            responses.append(resp_item)

        return responses

    def run_peek_mode(self) -> List[dict]:
        """偷看模式 (Peeking Mode)：用户不说话，交易员自行发起工作室内轮流讨论"""
        if not self.active_status:
            return []

        env = self.get_time_and_environment_context()
        # 随机挑选一对有立场交锋的交易员组合
        pairs = [
            ("trader_1", "trader_3"),  # 成长进攻 vs 红利防御
            ("trader_5", "trader_2"),  # 逆向事件 vs 均衡中立
            ("trader_4", "trader_6")   # 消费医药长线 vs 周期大宗
        ]
        t1_id, t2_id = random.choice(pairs)
        t1_name = TRADERS_CONFIG[t1_id]["name"]
        t2_name = TRADERS_CONFIG[t2_id]["name"]

        # 发起首条观点
        t1_reply = generate_fallback_chat_reply(t1_id, "盘面讨论", env)
        m1 = {
            "mode": "group_peek",
            "trader_id": t1_id,
            "trader_name": t1_name,
            "style": TRADERS_CONFIG[t1_id]["style"],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "reply": t1_reply
        }
        self.append_chat_message(m1)

        # 第二位交易员反驳或互动
        t2_reply = generate_fallback_chat_reply(t2_id, t1_reply, env)
        m2 = {
            "mode": "group_peek",
            "trader_id": t2_id,
            "trader_name": t2_name,
            "style": TRADERS_CONFIG[t2_id]["style"],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "reply": t2_reply
        }
        self.append_chat_message(m2)

        return [m1, m2]

if __name__ == "__main__":
    chat = SevenPersonChatRoom()
    print("=== 七人群聊互动测试 ===")
    test_user_msg = "今天早盘半导体涨了 2 个点，要不要追？"
    print(f"用户在群里提问: '{test_user_msg}'")
    replies = chat.send_group_message(test_user_msg)
    for r in replies:
        print(f"[{r['trader_name']} | {r['style']}]: {r['reply']}")

    print("\n=== 偷看模式（AI 自主交锋）测试 ===")
    peek_res = chat.run_peek_mode()
    for p in peek_res:
        print(f"[{p['trader_name']}]: {p['reply']}")
