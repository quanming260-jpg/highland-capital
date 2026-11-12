# -*- coding: utf-8 -*-
"""HIGHLAND CAPITAL - 两本虚拟股票账户 (Virtual Accounts)
规则要求（按原文规范严格实现）：
1. 两本账：A 股和美股各自一本账，数据结构分开存，页面可切“美股 / A 股 / 合并”，统一折算展示。
2. 每人一个开关：在配置文件中独立启用/停用；同一只票不能两边同时开。
3. 成交窗口：仅在规定窗口（A 股 14:30–15:00，美股 15:30–16:00）收盘集合竞价一笔模拟全成交。
4. 红线：只做模拟记账与持仓诊断，严禁生成实盘订单。
"""
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ACCOUNTS_DIR, TRADERS_CONFIG

# 默认汇率 (USD/CNY)
USD_TO_CNY_RATE = 7.24

def init_default_accounts():
    """初始化两本默认账户数据（如不存在）"""
    ACCOUNTS_DIR.mkdir(parents=True, exist_ok=True)
    
    a_share_file = ACCOUNTS_DIR / "account_a_share.json"
    if not a_share_file.exists():
        default_a = {
            "account_id": "virtual_a_share",
            "market": "A股",
            "currency": "CNY",
            "cash": 350000.0,
            "initial_capital": 1000000.0,
            "holdings": [
                {
                    "symbol": "510880",
                    "name": "红利ETF",
                    "shares": 100000,
                    "cost_price": 3.12,
                    "current_price": 3.18,
                    "owner_trader": "trader_3",
                    "sector": "红利低波"
                },
                {
                    "symbol": "512480",
                    "name": "半导体ETF",
                    "shares": 80000,
                    "cost_price": 1.15,
                    "current_price": 1.28,
                    "owner_trader": "trader_1",
                    "sector": "成长科技"
                },
                {
                    "symbol": "512010",
                    "name": "医药ETF",
                    "shares": 120000,
                    "cost_price": 0.42,
                    "current_price": 0.45,
                    "owner_trader": "trader_4",
                    "sector": "消费医药"
                },
                {
                    "symbol": "512880",
                    "name": "证券ETF",
                    "shares": 100000,
                    "cost_price": 1.05,
                    "current_price": 1.12,
                    "owner_trader": "trader_2",
                    "sector": "大金融均衡"
                }
            ],
            "trade_history": [
                {
                    "timestamp": "2026-11-10 14:55:00",
                    "symbol": "512480",
                    "name": "半导体ETF",
                    "action": "BUY",
                    "shares": 20000,
                    "price": 1.18,
                    "trader": "trader_1",
                    "reason": "突破 20 日均线，成长风格进攻试仓"
                }
            ],
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(a_share_file, "w", encoding="utf-8") as f:
            json.dump(default_a, f, ensure_ascii=False, indent=2)

    us_share_file = ACCOUNTS_DIR / "account_us_share.json"
    if not us_share_file.exists():
        default_us = {
            "account_id": "virtual_us_share",
            "market": "美股",
            "currency": "USD",
            "cash": 45000.0,
            "initial_capital": 100000.0,
            "holdings": [
                {
                    "symbol": "NVDA",
                    "name": "NVIDIA",
                    "shares": 150,
                    "cost_price": 138.0,
                    "current_price": 145.5,
                    "owner_trader": "trader_1",
                    "sector": "AI硬件"
                },
                {
                    "symbol": "AAPL",
                    "name": "Apple",
                    "shares": 120,
                    "cost_price": 220.0,
                    "current_price": 225.0,
                    "owner_trader": "trader_2",
                    "sector": "消费电子"
                }
            ],
            "trade_history": [],
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(us_share_file, "w", encoding="utf-8") as f:
            json.dump(default_us, f, ensure_ascii=False, indent=2)

class VirtualAccountManager:
    """虚拟账户管理器：负责两本账的读取、诊断与估值统计"""
    def __init__(self):
        init_default_accounts()
        self.a_file = ACCOUNTS_DIR / "account_a_share.json"
        self.us_file = ACCOUNTS_DIR / "account_us_share.json"

    def load_account(self, market: str = "A股") -> dict:
        """读取指定市场的账户"""
        target_file = self.a_file if market == "A股" else self.us_file
        if not target_file.exists():
            init_default_accounts()
        with open(target_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def compute_portfolio_metrics(self, account: dict) -> dict:
        """计算账户的持仓市值、总资产、现金比例、集中度及个股权重分布"""
        cash = float(account.get("cash", 0.0))
        currency = account.get("currency", "CNY")
        holdings = account.get("holdings", [])
        
        total_market_value = 0.0
        enriched_holdings = []
        for h in holdings:
            shares = float(h.get("shares", 0))
            price = float(h.get("current_price", 0.0))
            cost = float(h.get("cost_price", price))
            mv = shares * price
            pnl = (price - cost) * shares
            pnl_pct = ((price - cost) / cost * 100.0) if cost > 0 else 0.0
            
            total_market_value += mv
            enriched_holdings.append({
                **h,
                "market_value": round(mv, 2),
                "unrealized_pnl": round(pnl, 2),
                "pnl_pct": round(pnl_pct, 2)
            })
            
        total_assets = cash + total_market_value
        cash_ratio = (cash / total_assets) if total_assets > 0 else 1.0
        
        # 计算持仓集中度 (Top 1 和 Top 3 权重)
        sorted_by_mv = sorted(enriched_holdings, key=lambda x: x["market_value"], reverse=True)
        top1_weight = (sorted_by_mv[0]["market_value"] / total_assets) if sorted_by_mv and total_assets > 0 else 0.0
        top3_weight = (sum(x["market_value"] for x in sorted_by_mv[:3]) / total_assets) if total_assets > 0 else 0.0
        
        # 为每只股票补充权重占比
        for h in enriched_holdings:
            h["weight_pct"] = round((h["market_value"] / total_assets * 100.0) if total_assets > 0 else 0.0, 2)
            
        return {
            "account_id": account.get("account_id"),
            "market": account.get("market"),
            "currency": currency,
            "cash": round(cash, 2),
            "total_market_value": round(total_market_value, 2),
            "total_assets": round(total_assets, 2),
            "cash_ratio_pct": round(cash_ratio * 100.0, 2),
            "holdings_count": len(enriched_holdings),
            "top1_concentration_pct": round(top1_weight * 100.0, 2),
            "top3_concentration_pct": round(top3_weight * 100.0, 2),
            "holdings": enriched_holdings,
            "trade_history": account.get("trade_history", [])
        }

    def get_combined_overview(self) -> dict:
        """获取 A 股与美股两本账的合并折算概览 (统一折算为 CNY)"""
        a_metrics = self.compute_portfolio_metrics(self.load_account("A股"))
        us_metrics = self.compute_portfolio_metrics(self.load_account("美股"))
        
        total_assets_cny = a_metrics["total_assets"] + (us_metrics["total_assets"] * USD_TO_CNY_RATE)
        total_cash_cny = a_metrics["cash"] + (us_metrics["cash"] * USD_TO_CNY_RATE)
        
        return {
            "a_share": a_metrics,
            "us_share": us_metrics,
            "combined": {
                "total_assets_cny": round(total_assets_cny, 2),
                "total_cash_cny": round(total_cash_cny, 2),
                "overall_cash_ratio_pct": round(total_cash_cny / total_assets_cny * 100.0, 2) if total_assets_cny > 0 else 0.0,
                "usd_to_cny_rate": USD_TO_CNY_RATE
            }
        }

if __name__ == "__main__":
    mgr = VirtualAccountManager()
    overview = mgr.get_combined_overview()
    print("=== A 股账户诊断 ===")
    print(f"总资产: {overview['a_share']['total_assets']} CNY | 现金比例: {overview['a_share']['cash_ratio_pct']}% | Top1集中度: {overview['a_share']['top1_concentration_pct']}%")
    print("=== 美股账户诊断 ===")
    print(f"总资产: {overview['us_share']['total_assets']} USD | 现金比例: {overview['us_share']['cash_ratio_pct']}%")
    print(f"=== 两账合并总折算: {overview['combined']['total_assets_cny']} CNY ===")
