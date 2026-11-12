# -*- coding: utf-8 -*-
"""HIGHLAND CAPITAL - 统一 LLM 调用网关 (LLM Gateway)
特性：
1. 优先检测 DEEPSEEK_API_KEY 与 GEMINI_API_KEY
2. 支持切换 DeepSeek / Gemini 3.8 Flash
3. 严格兜底：若无密钥或请求超时失败，自动平滑退回本地语料与规则引擎
4. 保障服务 7x24 小时不掉线
"""
import json
import os
import sys
import requests
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import BASE_DIR, DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, GEMINI_API_KEY
from src.fallback_corpus import TRADER_VOICES, generate_fallback_chat_reply, generate_fallback_diary

def _load_env_keys():
    """尝试从 .env 文件自动载入环境变量"""
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'").strip('"')
                    if k and v and k not in os.environ:
                        os.environ[k] = v

_load_env_keys()

class LLMGateway:
    """LLM 综合网关"""
    def __init__(self):
        self.deepseek_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        self.gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.timeout = 15

    def is_live_api_ready(self) -> bool:
        """检查是否有真实外部 LLM Key 可用"""
        return bool(self.deepseek_key or self.gemini_key)

    def call_deepseek(self, messages: List[Dict], temperature: float = 0.5) -> Optional[str]:
        """通过 DeepSeek API 进行推理"""
        if not self.deepseek_key:
            return None
        url = f"{DEEPSEEK_BASE_URL}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.deepseek_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": messages,
            "temperature": temperature,
            "stream": False
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            else:
                print(f"[Warn] DeepSeek API 响应状态异常: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"[Warn] DeepSeek API 调用失败: {e}")
        return None

    def call_gemini(self, prompt: str, system_instruction: str = "") -> Optional[str]:
        """通过 Gemini API (3.8 Flash) 进行推理"""
        if not self.gemini_key:
            return None
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
        payload = {
            "contents": [{"parts": [{"text": f"{system_instruction}\n\n{prompt}".strip()}]}]
        }
        try:
            resp = requests.post(url, json=payload, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            print(f"[Warn] Gemini API 调用失败: {e}")
        return None

    def query(self, messages: List[Dict], fallback_fn=None, **fallback_kwargs) -> str:
        """通用查询：先尝试真实 API，失败时无缝切换兜底"""
        if self.deepseek_key:
            ans = self.call_deepseek(messages)
            if ans:
                return ans
        elif self.gemini_key:
            prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
            ans = self.call_gemini(prompt)
            if ans:
                return ans

        # 触发本地高质量语料兜底
        if fallback_fn:
            return fallback_fn(**fallback_kwargs)
        return "当前模型正在本地离线调度中，已保持基准状态。"

GLOBAL_LLM = LLMGateway()

if __name__ == "__main__":
    gw = LLMGateway()
    print("LLM Gateway 状态: 实时 API 就绪 =", gw.is_live_api_ready())
    reply = generate_fallback_chat_reply("trader_1", "今天半导体怎么看？", {"weather_desc": "晴朗", "temp": 11})
    print("本地兜底测试 (千里马):", reply)
