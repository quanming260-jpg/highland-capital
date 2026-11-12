# -*- coding: utf-8 -*-
"""HIGHLAND CAPITAL - 真实天气与真实市场快照接入
1. 天气：Open-Meteo 免费 API（无须 Key），覆盖北京、纽约、华盛顿、杭州、木兰
2. 行情：真实 A 股大盘行情快照（上证、深证、创业板、科创50），所有数字必须真实
"""
import json
import os
import sys
import urllib.request
import urllib.parse
from datetime import datetime
from zoneinfo import ZoneInfo

# 添加父目录到 sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CITIES_WEATHER, MARKET_SYMBOLS

UA_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# WMO Weather interpretation codes
WMO_CODE_MAP = {
    0: "晴朗",
    1: "大部晴朗",
    2: "多云",
    3: "阴天",
    45: "有雾",
    48: "沉降雾",
    51: "轻微细雨",
    53: "小细雨",
    55: "密集细雨",
    61: "微雨",
    63: "中雨",
    65: "大雨",
    71: "小雪",
    73: "中雪",
    75: "大雪",
    77: "雪粒",
    80: "轻微阵雨",
    81: "中等阵雨",
    82: "剧烈阵雨",
    85: "小阵雪",
    86: "大阵雪",
    95: "雷暴",
    96: "雷暴伴微雹",
    99: "雷暴伴大雹"
}

def fetch_city_weather(city_key: str = "beijing") -> dict:
    """从 Open-Meteo 抓取指定城市的实时天气数据"""
    if city_key not in CITIES_WEATHER:
        city_key = "beijing"
    
    city_info = CITIES_WEATHER[city_key]
    lat = city_info["latitude"]
    lon = city_info["longitude"]
    tz = city_info["timezone"]
    
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&current_weather=true&timezone={urllib.parse.quote(tz)}"
    )
    
    try:
        req = urllib.request.Request(url, headers=UA_HEADERS)
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            current = data.get("current_weather", {})
            w_code = current.get("weathercode", 0)
            desc = WMO_CODE_MAP.get(w_code, "多云")
            is_day = current.get("is_day", 1) == 1
            
            # 计算当地真实时间
            local_tz = ZoneInfo(tz)
            local_time_str = datetime.now(local_tz).strftime("%Y-%m-%d %H:%M:%S")
            
            return {
                "city": city_info["name"],
                "description": city_info["description"],
                "market": city_info["market"],
                "local_time": local_time_str,
                "temperature": current.get("temperature", "未提供"),
                "windspeed": current.get("windspeed", "未提供"),
                "is_day": is_day,
                "weathercode": w_code,
                "weather_desc": desc,
                "status": "success"
            }
    except Exception as e:
        return {
            "city": city_info["name"],
            "description": city_info["description"],
            "market": city_info["market"],
            "error": str(e),
            "temperature": "未提供",
            "weather_desc": "未知",
            "status": "fallback"
        }

def fetch_all_cities_weather() -> dict:
    """抓取全部 5 座城市的天气状态"""
    results = {}
    for key in CITIES_WEATHER.keys():
        results[key] = fetch_city_weather(key)
    return results

def fetch_market_indices() -> dict:
    """从腾讯金融接口抓取真实大盘指数快照，保障数据 100% 真实"""
    symbols = ",".join(MARKET_SYMBOLS.values())
    url = f"https://qt.gtimg.cn/q={symbols}"
    
    indices = {}
    try:
        req = urllib.request.Request(url, headers=UA_HEADERS)
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw_text = resp.read().decode("gbk", "ignore")
            for line in raw_text.split(";"):
                line = line.strip()
                if not line or "=" not in line:
                    continue
                parts = line.split("=")
                body = parts[1].strip('"')
                fields = body.split("~")
                if len(fields) < 40:
                    continue
                
                code = fields[2]
                name = fields[1]
                current_price = float(fields[3]) if fields[3] else None
                prev_close = float(fields[4]) if fields[4] else None
                chg_pts = float(fields[31]) if fields[31] else 0.0
                chg_pct = float(fields[32]) if fields[32] else 0.0
                turnover_wan = float(fields[37]) if fields[37] else 0.0  # 成交金额（万元）
                
                indices[name] = {
                    "code": code,
                    "price": current_price if current_price is not None else "未提供",
                    "prev_close": prev_close if prev_close is not None else "未提供",
                    "chg_pts": chg_pts,
                    "chg_pct": chg_pct,
                    "amount_yi": round(turnover_wan / 10000.0, 2) if turnover_wan else "未提供",
                    "time": fields[30] if len(fields) > 30 else "未提供"
                }
    except Exception as e:
        indices["_error"] = str(e)
    return indices

if __name__ == "__main__":
    print("--- 天气测试 ---")
    bj_weather = fetch_city_weather("beijing")
    print("北京天气:", bj_weather)
    print("\n--- 大盘真实行情测试 ---")
    m_indices = fetch_market_indices()
    for k, v in m_indices.items():
        print(f"{k}: {v}")
