#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HIGHLAND CAPITAL - 七人群聊交互终端 (Interactive Chat CLI)
用法：
  python chat.py              # 进入交互群聊模式
  python chat.py --peek       # 触发一次交易员自主交锋（偷看模式）
  python chat.py --private 1  # 针对 1 号交易员（千里马）单独私聊
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.chat_room import SevenPersonChatRoom
from config import TRADERS_CONFIG

def main():
    chat = SevenPersonChatRoom()
    env = chat.get_time_and_environment_context()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--peek":
        print("=== HIGHLAND CAPITAL 偷看模式（交易员内部对话）===")
        msgs = chat.run_peek_mode()
        for m in msgs:
            print(f"[{m['trader_name']} | {m['style']}]: {m['reply']}")
        return

    print("=" * 60)
    print(" 🏛️  HIGHLAND CAPITAL 七人群聊工作室")
    print(f" 当前时段：{env['scene_desc']}")
    print(f" 北京天气：{env['weather_desc']} {env['temp']}°C")
    print(" 成员：千里马(短线)、天平(均衡)、磐石(红利)、远见(消费医药)、逆风(逆向)、乘风(周期) + 您")
    print(" 提示：输入消息直接在群里发言；输入 '@名字 消息' 可点名私聊；输入 'peek' 偷看内部交流；输入 'quit' 退出。")
    print("=" * 60)

    while True:
        try:
            user_input = input("\n[您] > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["quit", "exit", "q"]:
                print("退出群聊。")
                break
            if user_input.lower() == "peek":
                print("\n--- 交易员内部交锋中 ---")
                peeks = chat.run_peek_mode()
                for p in peeks:
                    print(f"[{p['trader_name']} | {p['style']}]: {p['reply']}")
                continue

            # 检查是否为私聊格式: @千里马 或 @trader_1
            target_trader = None
            for t_id, cfg in TRADERS_CONFIG.items():
                if f"@{cfg['name']}" in user_input or f"@{t_id}" in user_input:
                    target_trader = t_id
                    user_input = user_input.replace(f"@{cfg['name']}", "").replace(f"@{t_id}", "").strip()
                    break

            if target_trader:
                cfg = TRADERS_CONFIG[target_trader]
                print(f"\n--- 私聊中: 与 {cfg['name']} ({cfg['style']}) 1v1 对话 ---")
                res = chat.ask_trader_private(target_trader, user_input)
                print(f"[{res['trader_name']}]: {res['reply']}")
            else:
                print("\n--- 群聊广播中 ---")
                replies = chat.send_group_message(user_input)
                for r in replies:
                    print(f"[{r['trader_name']} | {r['style']}]: {r['reply']}")

        except (KeyboardInterrupt, EOFError):
            print("\n已退出群聊。")
            break

if __name__ == "__main__":
    main()
