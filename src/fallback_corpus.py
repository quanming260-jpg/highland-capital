# -*- coding: utf-8 -*-
"""HIGHLAND CAPITAL - 本地高拟真交易语料库与知识引擎 (Fallback Corpus Engine)
当未配置 API Key 或网络/模型请求超时异常时，自动退回本地语料库。
保障系统“群聊不会突然死掉”，六位交易员严格按各自投资风格与期限拟真发声。
"""
import random
from typing import Dict, List

# 六位交易员的开盘前/盘中/盘后拟真模板库
TRADER_VOICES = {
    "trader_1": {
        "name": "千里马",
        "style": "短线·成长进攻",
        "tone": "敏锐果决、紧盯放量与动量、雷厉风行",
        "morning_templates": [
            "隔夜催化我筛过了，重点看科技和算力成长板块的分时量能。情绪分在 {sentiment_score}，只要开盘半小时成交额跟上，我随时准备抓进攻突破机会！",
            "短线吃的是速度与盈亏比。今天核心观察科技龙头能不能领涨破位。只要盘面有放量合力，成长进攻位绝不手软；量能不及预期就继续盯盘！"
        ],
        "midday_templates": [
            "上午盘面扫了一遍，高位有分歧但承接力度尚可。下午重点盯 14:30 窗口，若没有增量资金强攻，短线绝不追高，保持机动！",
            "午前成长方向脉冲了一波，短线仓位继续以日内均线为风控防线。下午先看震荡洗盘后的二阶方向。"
        ],
        "closing_templates": [
            "今天短线仓位只做试探观察，符合纪律不盲目追单。收盘集合竞价维持防守，明天开盘再战。",
            "收盘盘点：短线博弈靠的是严格止损与弹性。今天无新增突破信号，空仓部分现金继续握在手里等下一次放量！"
        ],
        "chat_replies": [
            "短线别被小打小闹的杂音带偏了节奏！盯紧分时成交量和龙头换手，没有量就是假突破！",
            "我赞同顺势而为，但如果成长赛道没出现合力共振，我宁可空仓等机会，也不想在横盘里磨损本金！",
            "只要盈亏比合适，我愿意在右侧放量时拿底仓冲锋！"
        ]
    },
    "trader_2": {
        "name": "天平",
        "style": "中短线·均衡",
        "tone": "理性客观、兼顾防守与进攻、强调平衡",
        "morning_templates": [
            "从全市场全局看，今日多空权重比在 {pos_ratio}%:{neg_ratio}%。宏观环境整体平稳，建议组合保持中短线均衡配置，不要单边押注极端方向。",
            "今日早盘宏观与微观资讯相互对冲，情绪账本维持在 {sentiment_lean} 状态。均衡底仓不动，观察盘面结构轮动。"
        ],
        "midday_templates": [
            "午间观察各板块涨跌中位数，分化依旧明显。核心宽基 ETF 波动在合理区间，我们账户的现金比例与持仓结构健康，无需恐慌。",
            "上午行情多空拉锯，符合均衡市特征。午后继续维持防守与进攻 5:5 动态平衡。"
        ],
        "closing_templates": [
            "全天收盘平稳。账户集中度在可控范围之内，今天没有偏离既定策略，继续保持组合韧性。",
            "收盘评估：市场多空拉锯没有明显失衡。今日未触发调仓阈值，中短线持仓按原计划推移。"
        ],
        "chat_replies": [
            "大家先别急着下定论。一边是成长方向在放量，另一边红利与消费也在支撑底盘，走极端反而容易两头挨打。",
            "我赞同千里马的敏锐，但也提醒大家盯紧整体组合的最大回撤。均衡配置是穿越周期的压舱石。",
            "从数据上看，目前的风险收益比还在可承受区间，保持定力最重要。"
        ]
    },
    "trader_3": {
        "name": "磐石",
        "style": "中长线·红利防御",
        "tone": "稳健审慎、重视现金流、视回撤为首敌",
        "morning_templates": [
            "不管隔夜快讯怎么喧嚣，我第一件事只看沪深300在MA200下方还是上方。高股息红利资产的股息率与现金流才是真正的护城河，防御底仓坚决不动！",
            "红利防御看的是长周期的确定性。今天情绪虽然有催化，但估值与安全边际还没到激进时刻，继续严守防守纪律。"
        ],
        "midday_templates": [
            "上午盘面虽然热闹，但进攻方向多伴随高波动。红利低波类标的依然稳如磐石，回撤控制良好，无需做任何无效交易动作。",
            "午盘复核：高股息品种股息收益率稳定，防守闸门保持常态锁定。宁可少赚，绝不承担无谓回撤。"
        ],
        "closing_templates": [
            "收盘盘点，防御底仓收益稳健，完全符合中长线预期。不追涨、不杀跌，耐心等待分红复利沉淀。",
            "今日收盘，防守体系经受住了分化考验。安全边际大于一切，今天不开新仓就是最好的仓位管理。"
        ],
        "chat_replies": [
            "短期冲高回落见得太多了。只要没有持续的现金流和分红支撑，纯情绪估值泡沫终究要挤压。",
            "本金安全永远排第一位！千里马你想冲可以，但防守底仓绝对不能被你拿去当炮灰。",
            "市场越是躁动，越要耐得住寂寞。稳住基本盘，时间是我们的朋友。"
        ]
    },
    "trader_4": {
        "name": "远见",
        "style": "长线·消费医药",
        "tone": "耐心执着、立足基本面与人口老龄化商业壁垒",
        "morning_templates": [
            "长线关注消费医药的深层逻辑：人口结构老龄化与刚性健康需求是确定的大趋势。短期一两天的消息面波动不改中长线内在价值，保持从容跟踪。",
            "今天消费与创新药板块估值仍处于历史合理分位数区间。长线投资者赚的是企业成长的钱，开盘前保持静心观察。"
        ],
        "midday_templates": [
            "中午看了眼几家核心医药公司的财报预告，管线进展与研发投入稳步推进。盘面脉冲不用过虑，长线定投节奏不变。",
            "午间复盘：刚需赛道具备抗周期韧性，短期情绪波动反而是审视企业护城河的好时机。"
        ],
        "closing_templates": [
            "收盘心如止水。消费医药的复利需要时间发酵，今天持仓表现温和，长线策略稳步推进。",
            "全天走势平稳，优质资产的价值只会在长跑中显现。今天无需任何调仓，静待花开。"
        ],
        "chat_replies": [
            "千里马太看重分钟级分时了，短期的波动三年后再看不过是一朵微小的浪花。",
            "我和磐石的看法有一半相通：确定性最重要。医药创新和刚需消费是长坡厚雪的典型代表。",
            "别被眼前的分歧吓倒，真正的好生意只要估值不离谱，拿着睡得着觉才是硬道理。"
        ]
    },
    "trader_5": {
        "name": "逆风",
        "style": "中短线·逆向事件",
        "tone": "反直觉、善于在悲观中抓错杀、警惕狂热",
        "morning_templates": [
            "情绪账本显示多空分歧度={divergence}。大家都在一致预期的时候往往最危险，我反而盯紧那些被利空错杀、砸出黄金坑的逆向机会！",
            "开盘前重点梳理隔夜哪些标的被非理性恐慌抛售。别人贪婪我退后半步，别人恐慌我准备端好放大镜挑金子！"
        ],
        "midday_templates": [
            "上午果然有人在冲高时盲目追入被套。逆向博弈的关键是等市场情绪宣泄完毕，下午关注 14:30 集合竞价前是否有错杀品种均值回归。",
            "午盘快讯显示局部有黑天鹅传闻，但从事实核查来看被过度放大了。等恐慌盘再砸一把，那就是绝佳的逆向观察点。"
        ],
        "closing_templates": [
            "收盘复盘：逆向事件策略就是与大众情绪保持距离。今天未见极端错杀信号，继续保持潜伏状态。",
            "今天那些被狂热追捧的方向尾盘均有承压，逆向思维再次验证。不盲动，静待真正冰点降临。"
        ],
        "chat_replies": [
            "大众都在欢呼的时候，正是风险悄然聚集的时刻；等哪天大家都骂盘绝望了，叫我一声，我来抄底！",
            "别迷信一致预期！每次市场觉得‘这次不一样’的时候，最后都一模一样。",
            "逆向不是蛮干，是要在利空充分消化、抛压枯竭后才出手。"
        ]
    },
    "trader_6": {
        "name": "乘风",
        "style": "中长线·周期弹性",
        "tone": "宏观视野、关注大宗商品、工业开工与信贷脉冲",
        "morning_templates": [
            "看盘先看大势：全球宏观流动性与工业大宗商品价格走势是周期的晴雨表。当前信贷脉冲与开工数据温和，周期弹性板块保持右侧观察。",
            "周期有它自身的客观规律，春种秋收急不得。隔夜外围大宗商品波动有限，今天中长线周期持仓维持基准跟踪。"
        ],
        "midday_templates": [
            "午间查看上游原材料与航运高频数据，库存消化节奏平稳。周期类品种没有出现暴起暴落，继续耐心跟踪宏观拐点信号。",
            "中午复盘：宏观信贷与基建发力节奏在下半月是观察重点，目前未到周期爆发极值点，按兵不动。"
        ],
        "closing_templates": [
            "收盘总结：大宗与周期板块温和震荡，周期策略重在大趋势，不为一两天的窄幅震荡所动。",
            "今天全天周期品运行平稳，宏观向上弹性仍需更明确的数据共振。今日无调仓计划，继续守株待兔。"
        ],
        "chat_replies": [
            "微观上怎么折腾，都逃不出宏观周期的引力。看清楚大宗原材料和利率周期，心里的底气就不一样。",
            "我同意远见的定力，周期和价值本质上都是对客观规律的敬畏。",
            "等库存周期真正完成去库转补库，那时候的爆发力不是几只题材小票能比的。"
        ]
    }
}

def generate_fallback_diary(trader_id: str, session: str, context: dict) -> dict:
    """根据交易员风格与当前环境生成拟真交易日记"""
    voice = TRADER_VOICES.get(trader_id, TRADER_VOICES["trader_2"])
    sentiment_score = context.get("sentiment_score", 0.0)
    sentiment_lean = context.get("sentiment_lean", "中性")
    pos_ratio = int(context.get("pos_ratio", 0.18) * 100)
    neg_ratio = int(context.get("neg_ratio", 0.03) * 100)
    divergence = "有分歧" if context.get("divergence") else "平稳"
    
    if session == "morning":
        tpls = voice["morning_templates"]
        session_title = "开盘前：今天看什么"
    elif session == "midday":
        tpls = voice["midday_templates"]
        session_title = "午间：上午发生了什么、要不要改"
    else:
        tpls = voice["closing_templates"]
        session_title = "收盘前：今天做没做、为什么"
        
    template = random.choice(tpls)
    content = template.format(
        sentiment_score=f"{sentiment_score:+.2f}",
        sentiment_lean=sentiment_lean,
        pos_ratio=pos_ratio,
        neg_ratio=neg_ratio,
        divergence=divergence
    )
    
    # 结合风格的行动决策
    action = "维持观望跟踪"
    if trader_id == "trader_1" and sentiment_score > 0.20:
        action = "关注放量突破机会"
    elif trader_id == "trader_3":
        action = "防御底仓锁仓不动"
    elif trader_id == "trader_5" and context.get("divergence"):
        action = "搜寻恐慌错杀标的"
        
    return {
        "trader_id": trader_id,
        "trader_name": voice["name"],
        "style": voice["style"],
        "session": session,
        "session_title": session_title,
        "lean": sentiment_lean,
        "action": action,
        "content": content
    }

def generate_fallback_chat_reply(trader_id: str, user_input: str, chat_context: dict) -> str:
    """为指定交易员生成拟真聊天回复"""
    voice = TRADER_VOICES.get(trader_id, TRADER_VOICES["trader_1"])
    replies = voice["chat_replies"]
    base_reply = random.choice(replies)
    
    # 融入天气或时间感知
    weather_desc = chat_context.get("weather_desc", "")
    temp = chat_context.get("temp", "")
    weather_comment = ""
    if weather_desc and random.random() < 0.3:
        weather_comment = f"（顺便看了一眼窗外，今天北京{weather_desc}，气温才 {temp}°C，盘面倒比天气还躁动一些。）"
        
    return f"{base_reply} {weather_comment}".strip()
