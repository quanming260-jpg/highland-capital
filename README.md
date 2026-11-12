# HIGHLAND CAPITAL · 3D 等距交易工作室

> 复刻抖音 CLOVIS《凌晨 5 点前收盘》里的 HIGHLAND CAPITAL 工作室。  
> 目标：开盘前六位 AI 交易员筛选全市场资讯并给出研判；交易台中枢大脑固定三轮推理；全流程 3D 等距交易 Loft 空间可视化。  
> **红线纪律**：只给量化参考研判，绝不下单、不生成交易指令；所有价格涨跌数字严格来自真实数据源。

---

## 一、系统整体架构

```text
highland_capital/
├── index.html                     # [Phase 3] Three.js 3D 等距交易 Loft 虚拟办公室
├── serve.py                       # 本地轻量 Web 服务器（支持手机局域网与电脑访问）
├── chat.py                        # [Phase 2] 七人群聊与 1v1 私聊交互终端
├── record_diary.py                # [Phase 2] 交易日记定时触发脚本 (09:00 / 12:00 / 14:00)
├── run_morning.sh                 # [Phase 1] 每日盘前管线一键触发脚本 (Mac launchd 05:00/07:00 调度)
├── com.highland.capital.morning.plist # launchd 定时配置文件
├── config.py                      # 全局常量、契约版本、城市与交易员风格配置
├── src/
│   ├── ingest.py                  # [管线 1/5] 接入：财联社电报 + 东财 7x24，批次归档
│   ├── dedup.py                   # [管线 2/5] 去重：ID 幂等 + 24小时 2-gram Dice 相似度 > 0.8
│   ├── classify.py                # [管线 3/5] 定级：S/A/B/C/D 五级金字塔制度，S/A 优先推入上下文
│   ├── sentiment.py               # [管线 4/5] 情绪：按原文公式加权与 12 小时半衰期计算
│   ├── market_weather.py          # 真实环境：Open-Meteo 真实天气 + 真实大盘行情
│   ├── publisher.py               # [管线 5/5] 成稿：生成标准 brief JSON 与 Markdown 晨报
│   ├── virtual_accounts.py        # 虚拟账户：A 股与美股两本账、现金比例、持仓集中度监控
│   ├── traders.py                 # 六位独立风格交易员（期限+风格设定，非职能分工）
│   ├── central_brain.py           # 中枢大脑：固定三轮推理 (R1地图 -> R2诊断 -> R3深推)
│   ├── diaries.py                 # 交易日记引擎：自动写入 data/diaries/，只读存储
│   ├── chat_room.py               # 七人群聊总引擎（时间场景/天气感知、长期记忆、观点交锋）
│   ├── llm_client.py              # LLM 网关（DeepSeek / Gemini 3.8 Flash / 本地高质量语料平滑兜底）
│   └── fallback_corpus.py         # 本地高拟真角色语料库与知识引擎
├── data/
│   ├── raw/                       # 原始抓取批次归档
│   ├── accounts/                  # A 股 (account_a_share.json) 与美股 (account_us_share.json) 两本账
│   ├── diaries/                   # 每日三次交易日记留痕 (diaries_YYYY-MM-DD.json)
│   ├── memory/                    # 交易员长期记忆库 (self_note, commitment)
│   ├── brief_YYYY-MM-DD.json      # 每日标准结构化账本
│   └── brief_latest.json          # 最新一份账本（供 3D Loft 读取）
├── reports/
│   └── brief_YYYY-MM-DD.md        # 每日开盘前晨会简报
└── logs/
    └── morning_pipeline.log       # 调度日志
```

---

## 二、六位交易员设定（严格按原文修正）

六人**不是职能分工（无基本面/技术面分析师）**，而是六位有作息的 AI 交易员，共用同一套工作方式，区别在**策略期限**与**投资风格**：

| 交易员 | 策略期限 | 投资风格 | 主数据源（免费） | 风格口吻与观察重心 |
|---|---|---|---|---|
| **1 号 千里马** | 短线 | 成长进攻 | 财联社电报 (cls.cn) | 敏锐果决，盯紧分时动量、放量突破与硬科技算力成长 |
| **2 号 天平** | 中短线 | 均衡配置 | 东财全球资讯 7×24 | 理性客观，兼顾宏观与微观，追求多空权重平衡与资产配置 |
| **3 号 磐石** | 中长线 | 红利防御 | Baostock (分红与除权) | 稳健审慎，看重高股息、稳定现金流与 MA200 防守线，视回撤为首敌 |
| **4 号 远见** | 长线 | 消费医药 | Tushare / 财务三表 | 耐心执着，立足人口老龄化与刚需护城河，赚企业复利，看淡短期波动 |
| **5 号 逆风** | 中短线 | 逆向事件 | Finnhub 突发与情绪 | 独立反直觉，善于在极端悲观中发掘被利空错杀的黄金坑，警惕狂热 |
| **6 号 乘风** | 中长线 | 周期弹性 | AkShare 宏观/大宗商品 | 宏观视野，从全球流动性与工业开工库存推导周期拐点与右侧信号 |

---

## 三、快速启动与操作指南

### 1. 启动 3D 等距虚拟办公室 (Phase 3)
```bash
# 启动本地服务
/Users/qiaoquanming/Downloads/03_投资/etf_quant/.venv/bin/python serve.py
```
- **电脑浏览器访问**：`http://localhost:8500`
- **手机访问**：在同一 WiFi 下访问 `http://<你的Mac局域网IP>:8500`
- **功能体验**：
  - 拖拽旋转 / 滚轮缩放，支持 📐 开放 Loft、🛰️ 雷达俯视、🔍 紧凑工位、🔄 自动巡航；
  - 点击任一交易员小人或工位，右侧弹出该交易员卡片（含最新交易日记），并可直接 1v1 发起提问；
  - 顶部五座城市无缝切换（纽约 50F、北京国贸、华盛顿白宫、杭州西湖、木兰江畔），窗外楼群、天空光照与真实天气随之变换；
  - 底部可自由切换“🏠 掀开屋顶”与“🌙 看盘模式 (关灯)”。

### 2. 进入七人群聊与私聊 (Phase 2)
```bash
/Users/qiaoquanming/Downloads/03_投资/etf_quant/.venv/bin/python chat.py
```
- 直接输入文字在七人群中发言；
- 输入 `@千里马 算力还能追吗？` 触发 1v1 私聊；
- 输入 `peek` 查看交易员们自主发起的多空观点交锋。

### 3. 一键运行每日盘前晨报管线 (Phase 1)
```bash
./run_morning.sh
```
或直接运行 Python 调度：
```bash
/Users/qiaoquanming/Downloads/03_投资/etf_quant/.venv/bin/python src/pipeline.py
```
- 自动抓取 200+ 条隔夜资讯并执行 2-gram Dice 语义去重；
- 依据金字塔定级与半衰期公式计算情绪分；
- 触发六人日记与中枢大脑 R1/R2/R3 三轮推理；
- 输出并覆盖最新的 `data/brief_latest.json` 与 `reports/brief_YYYY-MM-DD.md`。

---

## 四、纪律红线与设计原则

1. **红线声明**：系统所有模块输出均为参考研判，AI 绝不创建实盘订单，不生成交易指令；
2. **数据真实**：所有行情、大盘、气象指标 100% 接入真实接口（AkShare、Tencent、Open-Meteo），无数据明确标注“未提供”，杜绝幻觉捏造；
3. **情绪账本原样入词**：情绪分与结论是自然语言文本事实，交由交易员与中枢大脑在上下文中权衡，不以代码规则僵硬写死买卖。
