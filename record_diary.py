#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HIGHLAND CAPITAL - 交易日记定时录入脚本 (Diary Scheduler Trigger)
用法：
  python record_diary.py                 # 根据当前时间自动判断时段
  python record_diary.py --session morning   # 09:00 录入“今天看什么”
  python record_diary.py --session midday    # 12:00 录入“上午发生了什么、要不要改”
  python record_diary.py --session closing   # 14:00 录入“今天做没做、为什么”
"""
import sys
import os
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.diaries import DiaryManager

def get_session_by_time() -> str:
    now = datetime.now()
    hour = now.hour
    if hour < 11:
        return "morning"
    elif hour < 13:
        return "midday"
    else:
        return "closing"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", choices=["morning", "midday", "closing"], help="日记时段")
    parser.add_argument("--market", default="A股", help="市场: A股 / 美股")
    args = parser.parse_args()

    session = args.session or get_session_by_time()
    market = args.market

    mgr = DiaryManager()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 正在触发六位交易员记录【{market} {session}】交易日记...")
    res = mgr.record_session_diaries(session=session, market=market)
    entries = res["sessions"].get(session, [])
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 录入完成，共记录 {len(entries)} 条日记留痕。")
    for d in entries:
        print(f"  - [{d['trader_name']} | {d['style']}]: {d['content'][:45]}...")

if __name__ == "__main__":
    main()
