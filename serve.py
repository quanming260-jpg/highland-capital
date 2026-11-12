#!/usr/bin/env bash
# -*- coding: utf-8 -*-
"""HIGHLAND CAPITAL - 全功能 Web 服务与 API 后端 (Web & API Server)
集成：
1. 静态文件托管（3D Loft、JSON 账本、多媒体）
2. 七人群聊 API (/api/group_chat)
3. 多模态走势图/截图识别 API (图片 Base64 + 分析)
4. 交易员长期记忆管理 API (/api/memory)
5. 偷看模式自主交锋 API (/api/peek)
"""
import sys
import os
import json
import http.server
import socketserver
from urllib.parse import urlparse

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIR)

from src.chat_room import SevenPersonChatRoom
from config import TRADERS_CONFIG

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8500
CHAT_ENGINE = SevenPersonChatRoom()

class HighlandApiHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def _send_json_response(self, data, status_code=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/history":
            history = CHAT_ENGINE.load_chat_history()
            self._send_json_response({"status": "success", "history": history[-30:]})
            return
        elif path == "/api/memory":
            mem = CHAT_ENGINE.load_memory()
            enriched = {}
            for t_id, data in mem.items():
                cfg = TRADERS_CONFIG.get(t_id, {})
                enriched[t_id] = {
                    "name": cfg.get("name", t_id),
                    "style": cfg.get("style", ""),
                    "self_note": data.get("self_note", ""),
                    "commitment": data.get("commitment", ""),
                    "recent_topics": data.get("recent_topics", [])
                }
            self._send_json_response({"status": "success", "traders_memory": enriched})
            return

        # 默认静态文件处理
        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        try:
            req_json = json.loads(post_data.decode("utf-8")) if post_data else {}
        except Exception:
            req_json = {}

        if path == "/api/group_chat":
            text = req_json.get("text", "").strip()
            image_b64 = req_json.get("image_base64", None)
            if not text and not image_b64:
                self._send_json_response({"status": "error", "message": "消息或图片不能为空"}, 400)
                return

            replies = CHAT_ENGINE.send_group_message(text or "请各位交易员帮我分析这张走势截图", image_base64=image_b64)
            self._send_json_response({"status": "success", "replies": replies})
            return

        elif path == "/api/peek":
            peek_msgs = CHAT_ENGINE.run_peek_mode()
            self._send_json_response({"status": "success", "replies": peek_msgs})
            return

        elif path == "/api/private_chat":
            trader_id = req_json.get("trader_id", "trader_1")
            text = req_json.get("text", "").strip()
            if not text:
                self._send_json_response({"status": "error", "message": "提问内容不能为空"}, 400)
                return
            reply = CHAT_ENGINE.ask_trader_private(trader_id, text)
            self._send_json_response({"status": "success", "result": reply})
            return

        self._send_json_response({"status": "error", "message": "接口不存在"}, 404)

    def log_message(self, format, *args):
        # 仅在非 200 或异常时打印日志，避免刷屏
        if " 200 " not in format % args:
            super().log_message(format, *args)

def main():
    os.chdir(DIR)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), HighlandApiHandler) as httpd:
        url = f"http://localhost:{PORT}"
        print("=" * 60)
        print(f" 🚀 HIGHLAND CAPITAL 全功能 Web & API 服务已就绪！")
        print(f" 🖥️  电脑访问: {url}")
        print(f" 💬 接口支持: 群聊 / 多模态图表识别 / 记忆库 / 偷看模式")
        print("=" * 60)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n服务已关闭。")

if __name__ == "__main__":
    main()
