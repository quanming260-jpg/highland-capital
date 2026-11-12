# -*- coding: utf-8 -*-
"""HIGHLAND CAPITAL - 全局配置文件
遵循抖音 CLOVIS《凌晨 5 点前收盘》原文规范设计
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
REPORTS_DIR = BASE_DIR / "reports"
LOGS_DIR = BASE_DIR / "logs"

# 资讯契约版本
SCHEMA_VERSION = "v1"

# 虚拟账户与日记目录
ACCOUNTS_DIR = DATA_DIR / "accounts"
DIARIES_DIR = DATA_DIR / "diaries"
MEMORY_DIR = DATA_DIR / "memory"

# LLM 配置
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "fallback")  # deepseek | gemini | fallback
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# 六位交易员核心配置（严格按原文 6 种期限与风格设定）
TRADERS_CONFIG = {
    "trader_1": {
        "id": "trader_1",
        "name": "千里马",
        "alias": "交易员 1（短线·成长进攻）",
        "horizon": "短线",
        "style": "成长进攻",
        "primary_source": "财联社电报 (cls.cn)",
        "backup_source": "东财全球资讯 7×24",
        "focus": "分时动量、放量突破、AI算力与硬科技成长题材，强调胜率与敏锐度",
        "enabled": True
    },
    "trader_2": {
        "id": "trader_2",
        "name": "天平",
        "alias": "交易员 2（中短线·均衡）",
        "horizon": "中短线",
        "style": "均衡配置",
        "primary_source": "东财全球资讯 7×24",
        "backup_source": "华尔街见闻",
        "focus": "多空权重平衡、宏观环境与行业均衡、核心宽基ETF，强调攻守兼备",
        "enabled": True
    },
    "trader_3": {
        "id": "trader_3",
        "name": "磐石",
        "alias": "交易员 3（中长线·红利防御）",
        "horizon": "中长线",
        "style": "红利防御",
        "primary_source": "Baostock (分红与除权日线)",
        "backup_source": "Tushare Pro",
        "focus": "股息率、稳定现金流、防守底仓、沪深300 MA200防守线，强调本金安全",
        "enabled": True
    },
    "trader_4": {
        "id": "trader_4",
        "name": "远见",
        "alias": "交易员 4（长线·消费医药）",
        "horizon": "长线",
        "style": "消费医药长线",
        "primary_source": "Tushare / 基本面财务三表",
        "backup_source": "AkShare 行业专题",
        "focus": "赛道商业壁垒、人口老龄化与刚需消费、长线内在价值、定投复利",
        "enabled": True
    },
    "trader_5": {
        "id": "trader_5",
        "name": "逆风",
        "alias": "交易员 5（中短线·逆向事件）",
        "horizon": "中短线",
        "style": "逆向事件",
        "primary_source": "Finnhub 全球快讯与情绪突发",
        "backup_source": "Twelve Data",
        "focus": "极端恐慌错杀、重大利空充分消化后的均值回归、多空剧烈分歧点",
        "enabled": True
    },
    "trader_6": {
        "id": "trader_6",
        "name": "乘风",
        "alias": "交易员 6（中长线·周期弹性）",
        "horizon": "中长线",
        "style": "周期弹性",
        "primary_source": "AkShare 宏观/大宗与行业资金面",
        "backup_source": "东财个股研报流",
        "focus": "宏观信用扩张、大宗工业原料价格拐点、周期开工与库存脉冲",
        "enabled": True
    }
}

# 去重配置：24小时内 2-gram Dice 相似度阈值
DICE_SIMILARITY_THRESHOLD = 0.8
DEDUP_WINDOW_HOURS = 24.0

# 情绪评分模型配置（原文公式参数）
# S = Σ(s * L * c * d) / Σ(L * c * d)
LEVEL_WEIGHTS = {
    "S": 5.0,  # 顶级宏观/地缘/黑天鹅
    "A": 4.0,  # 重点政策/重磅财报/CPI/降准降息
    "B": 3.0,  # 行业动态/中报预告/资金流向
    "C": 2.0,  # 普通公告/日常评级
    "D": 1.0   # 杂讯/弱相关
}

# 时间半衰期（小时）
SENTIMENT_HALF_LIFE_HOURS = 12.0
# 最小有效样本量
MIN_EFFECTIVE_SAMPLES = 5
# 方向阈值 (+/- 0.10)
SENTIMENT_DIRECTION_THRESHOLD = 0.10
# 多空分歧判断阈值（多方与空方权重各自占比超过总权重该比例）
DIVERGENCE_RATIO_THRESHOLD = 0.28

# 真实天气：Open-Meteo 城市坐标与时区配置（原文提到的五座城市）
CITIES_WEATHER = {
    "beijing": {
        "name": "北京",
        "description": "北京国贸",
        "latitude": 39.9042,
        "longitude": 116.4074,
        "timezone": "Asia/Shanghai",
        "market": "A股"
    },
    "new_york": {
        "name": "纽约",
        "description": "纽约 50F",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "timezone": "America/New_York",
        "market": "美股"
    },
    "washington": {
        "name": "华盛顿",
        "description": "华盛顿白宫",
        "latitude": 38.9072,
        "longitude": -77.0369,
        "timezone": "America/New_York",
        "market": "政策中心"
    },
    "hangzhou": {
        "name": "杭州",
        "description": "杭州西湖",
        "latitude": 30.2741,
        "longitude": 120.1551,
        "timezone": "Asia/Shanghai",
        "market": "科技/数字经济"
    },
    "mulan": {
        "name": "木兰",
        "description": "木兰江畔",
        "latitude": 45.9427,
        "longitude": 128.0448,
        "timezone": "Asia/Shanghai",
        "market": "北方自然"
    }
}

# 真实大盘与指标配置（真实数据源接入）
MARKET_SYMBOLS = {
    "sh": "sh000001",   # 上证指数
    "sz": "sz399001",   # 深证成指
    "cyb": "sz399006",  # 创业板指
    "kc50": "sh000688"  # 科创50
}
