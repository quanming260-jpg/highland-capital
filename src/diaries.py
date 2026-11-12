# -*- coding: utf-8 -*-
"""HIGHLAND CAPITAL - 交易日记系统 (Trading Diaries)
按原文规范严格实现：
- 一天三次判断留痕：
  1. 开盘前 (morning): “今天看什么”
  2. 午间 (midday): “上午发生了什么、要不要改”
  3. 收盘前 (closing): “今天做没做、为什么”
- A 股与美股两本账分开记，每条均带时间戳、市场、倾向与判断正文；
- 日记只读留痕：由程序自动写入 data/diaries/YYYY-MM-DD.json，不可手动修改；
- 三层用途：给自己看、给复盘对照（第 5 / 20 个交易日）、给 AI 中枢大脑作为长期记忆上下文。
"""
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DIARIES_DIR, DATA_DIR
from src.traders import TraderTeam

class DiaryManager:
    """交易日记管理器"""
    def __init__(self):
        DIARIES_DIR.mkdir(parents=True, exist_ok=True)
        self.team = TraderTeam()

    def get_diary_file(self, date_str: str) -> str:
        return DIARIES_DIR / f"diaries_{date_str}.json"

    def load_diaries(self, date_str: str) -> dict:
        """加载指定日期的日记文档"""
        path = self.get_diary_file(date_str)
        if not path.exists():
            return {
                "date": date_str,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "sessions": {
                    "morning": [],
                    "midday": [],
                    "closing": []
                }
            }
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def record_session_diaries(
        self,
        session: str,
        market: str = "A股",
        custom_date: str = None
    ) -> dict:
        """录入某个时段的交易日记 (session: morning | midday | closing)"""
        now = datetime.now()
        date_str = custom_date or now.strftime("%Y-%m-%d")
        diary_data = self.load_diaries(date_str)
        
        # 读取当天最新简报中的情绪分与大盘数据
        brief_file = DATA_DIR / f"brief_{date_str}.json"
        if not brief_file.exists():
            brief_file = DATA_DIR / "brief_latest.json"
            
        sentiment_data = {"score": 0.0, "lean": "中性", "sentiment_context": "暂无隔夜情绪背景"}
        market_snapshot = {}
        if brief_file.exists():
            try:
                with open(brief_file, "r", encoding="utf-8") as f:
                    b_json = json.load(f)
                    sentiment_data = {
                        "score": b_json.get("lean_score", 0.0),
                        "lean": b_json.get("lean", "中性"),
                        "sentiment_context": b_json.get("sentiment_context", ""),
                        "divergence": b_json.get("divergence", False)
                    }
                    market_snapshot = b_json.get("market_snapshot", {})
            except Exception:
                pass

        # 触发 6 位交易员记录日记
        new_entries = self.team.generate_all_diaries(session, sentiment_data, market_snapshot)
        for entry in new_entries:
            entry["market"] = market

        # 写入对应时段槽位
        if session not in diary_data["sessions"]:
            diary_data["sessions"][session] = []
        diary_data["sessions"][session] = new_entries
        diary_data["last_updated"] = now.strftime("%Y-%m-%d %H:%M:%S")

        out_path = self.get_diary_file(date_str)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(diary_data, f, ensure_ascii=False, indent=2)

        return diary_data

    def get_latest_diaries_summary(self, date_str: str = None) -> List[dict]:
        """获取最近一次记录的所有交易员日记（供中枢大脑读取）"""
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")
        data = self.load_diaries(date_str)
        # 优先读取收盘、其次午间、最后早盘
        for s in ["closing", "midday", "morning"]:
            if data["sessions"].get(s):
                return data["sessions"][s]
        return []

if __name__ == "__main__":
    mgr = DiaryManager()
    today = datetime.now().strftime("%Y-%m-%d")
    res = mgr.record_session_diaries("morning", "A股", today)
    print(f"成功保存 {today} 早盘日记：共 {len(res['sessions']['morning'])} 条。")
