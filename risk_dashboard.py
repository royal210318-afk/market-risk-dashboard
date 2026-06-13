import streamlit as st
import requests
import pandas as pd
import yfinance as yf
from datetime import datetime

st.set_page_config(
    page_title="市场风险仪表盘",
    page_icon="📈",
    layout="wide"
)

API_KEY = st.secrets["TWELVE_API_KEY"]

st.title("📈 市场风险仪表盘")
st.caption("情绪 · 波动率 · 市场广度 · 信用风险 · 跨资产联动")


@st.cache_data(ttl=1800)
def get_fear_greed():
    try:
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        r = requests.get(url, timeout=20)
        data = r.json()
        return float(data["fear_and_greed"]["score"])
    except:
        return 50.0


@st.cache_data(ttl=1800)
def get_vix():
    try:
        vix = yf.Ticker("^VIX")
        hist = vix.history(period="5d")
        if hist is None or hist.empty:
            return None
        return round(float(hist["Close"].iloc[-1]), 2)
    except:
        return None


@st.cache_data(ttl=1800)
def get_history(symbol):
    url = (
        f"https://api.twelvedata.com/time_series"
        f"?symbol={symbol}"
        f"&interval=1day"
        f"&outputsize=260"
        f"&apikey={API_KEY}"
    )

    try:
        r = requests.get(url, timeout=30)
        data = r.json()

        if data.get("status") != "ok":
            return None

        df = pd.DataFrame(data["values"])
        df["close"] = df["close"].astype(float)
        df["high"] = df["high"].astype(float)

        return df

    except:
        return None


def latest_price(df):
    if df is None or df.empty:
        return None
    return round(float(df.iloc[0]["close"]), 2)


def calc_drawdown(df):
    if df is None or df.empty:
        return None, None

    latest = float(df.iloc[0]["close"])
    high52 = float(df["high"].max())
    drawdown = (latest - high52) / high52 * 100

    return round(latest, 2), round(drawdown, 2)


def calc_change(df, days=60):
    if df is None or df.empty or len(df) < days:
        return None

    latest = float(df.iloc[0]["close"])
    past = float(df.iloc[days - 1]["close"])

    change = (latest - past) / past * 100

    return round(change, 2)


def fear_status(fg):
    if fg < 25:
        return "极度恐惧"
    elif fg < 45:
        return "恐惧"
    elif fg < 75:
        return "中性"
    else:
        return "极度贪婪"


def vix_status(vix):
    if vix is None:
        return "获取失败"
    if vix < 15:
        return "过度乐观"
    elif vix < 20:
        return "低波动"
    elif vix < 30:
        return "风险升温"
    else:
        return "恐慌区"


def drawdown_status(dd):
    if dd is None:
        return "获取失败"
    if dd > -5:
        return "接近高位"
    elif dd > -10:
        return "轻度回调"
    elif dd > -20:
        return "明显回调"
    else:
        return "深度回调"


def relative_status(diff):
    if diff is None:
        return "获取失败"
    if diff < -5:
        return "广度较差"
    elif diff < -2:
        return "广度偏弱"
    else:
        return "广度正常"


def credit_status(change):
    if change is None:
        return "获取失败"
    if change < -5:
        return "信用风险升温"
    elif change < -2:
        return "信用偏弱"
    else:
        return "信用稳定"


# -----------------------
# 获取数据
# -----------------------
fg = get_fear_greed()
vix = get_vix()

spy_df = get_history("SPY")
qqq_df = get_history("QQQ")
rsp_df = get_history("RSP")
iwm_df = get_history("IWM")
hyg_df = get_history("HYG")
jnk_df = get_history("JNK")
tlt_df = get_history("TLT")
gld_df = get_history("GLD")

spy_price, spy_dd = calc_drawdown(spy_df)
qqq_price, qqq_dd = calc_drawdown(qqq_df)

rsp_change = calc_change(rsp_df, 60)
spy_change = calc_change(spy_df, 60)
iwm_change = calc_change(iwm_df, 60)
qqq_change = calc_change(qqq_df, 60)

hyg_change = calc_change(hyg_df, 60)
jnk_change = calc_change(jnk_df, 60)

tlt_change = calc_change(tlt_df, 60)
gld_change = calc_change(gld_df, 60)

rsp_vs_spy = round(rsp_change - spy_change, 2) if rsp_change is not None and spy_change is not None else None
iwm_vs_spy = round(iwm_change - spy_change, 2) if iwm_change is not None and spy_change is not None else None

hyg_price = latest_price(hyg_df)
jnk_price = latest_price(jnk_df)
tlt_price = latest_price(tlt_df)
gld_price = latest_price(gld_df)


# -----------------------
# 风险评分
# -----------------------
risk = 0
valid_items = 0

if fg is not None:
    valid_items += 1
    if fg < 25:
        risk += 80
    elif fg < 45:
        risk += 50
    elif fg < 75:
        risk += 20
    else:
        risk += 70

if vix is not None:
    valid_items += 1
    if vix < 15:
        risk += 15
    elif vix < 20:
        risk += 20
    elif vix < 30:
        risk += 50
    else:
        risk += 85

if spy_dd is not None:
    valid_items += 1
    if spy_dd > -5:
        risk += 10
    elif spy_dd > -10:
        risk += 40
    elif spy_dd > -20:
        risk += 70
    else:
        risk += 90

if qqq_dd is not None:
    valid_items += 1
    if qqq_dd > -5:
        risk += 10
    elif qqq_dd > -10:
        risk += 40
    elif qqq_dd > -20:
        risk += 70
    else:
        risk += 90

if rsp_vs_spy is not None:
    valid_items += 1
    if rsp_vs_spy < -5:
        risk += 70
    elif rsp_vs_spy < -2:
        risk += 45
    else:
        risk += 20

if iwm_vs_spy is not None:
    valid_items += 1
    if iwm_vs_spy < -5:
        risk += 70
    elif iwm_vs_spy < -2:
        risk += 45
    else:
        risk += 20

if hyg_change is not None:
    valid_items += 1
    if hyg_change < -5:
        risk += 85
    elif hyg_change < -2:
        risk += 55
    else:
        risk += 15

if jnk_change is not None:
    valid_items += 1
    if jnk_change < -5:
        risk += 85
    elif jnk_change < -2:
        risk += 55
    else:
        risk += 15

risk_score = round(risk / valid_items) if valid_items > 0 else 0


# -----------------------
# 核心判断
# -----------------------
credit_warning = (
    (hyg_change is not None and hyg_change < -5)
    or (jnk_change is not None and jnk_change < -5)
)

good_buy_window = (
    vix is not None
    and fg is not None
    and vix > 30
    and fg < 25
    and not credit_warning
)

fomo_warning = (
    vix is not None
    and fg is not None
    and vix <= 15
    and fg > 75
)

breadth_warning = (
    (rsp_vs_spy is not None and rsp_vs_spy < -5)
    or (iwm_vs_spy is not None and iwm_vs_spy < -5)
)


# -----------------------
# 场景：美股回调加仓策略
# -----------------------
if credit_warning:
    scene = "🔴 信用风险升温"
    advice = """
当前策略：暂停抄底，优先观察信用市场

股市下跌如果伴随高收益债同步下跌，
说明市场担心企业违约和融资压力。

这种下跌不是普通估值调整，
不要急着打出加仓子弹。
"""

elif good_buy_window:
    scene = "🟠 优质加仓窗口"
    advice = """
当前策略：重点关注加仓机会

VIX超过30，
恐惧贪婪指数低于25，
说明市场已经出现明显恐慌。

如果信用市场没有失控，
这是较好的分批加仓窗口。
"""

elif fomo_warning:
    scene = "🟣 市场过热"
    advice = """
当前策略：谨慎追高

Fear & Greed长期高于75，
同时VIX处于15以下，
说明市场不愿意给风险定价。

这类环境容易出现FOMO，
不适合大幅加仓。
"""

elif breadth_warning:
    scene = "🟡 上涨广度偏弱"
    advice = """
当前策略：谨慎观察

指数上涨可能主要由少数权重股推动，
RSP或IWM跑输SPY，
说明资金没有充分扩散。

这种上涨不够健康，
不宜盲目追高。
"""

else:
    if risk_score < 20:
        scene = "🟢 正常市场"
        advice = """
当前策略：正常定投

市场风险较低，按原计划持续定投即可。

回调加仓资金暂不动用。
"""

    elif risk_score < 40:
        scene = "🟡 第一档回调"
        advice = """
当前策略：执行第一档加仓

建议投入预备资金：30%

累计投入：30%
剩余现金：70%
"""

    elif risk_score < 60:
        scene = "🟠 第二档回调"
        advice = """
当前策略：执行第二档加仓

建议再投入预备资金：30%

累计投入：60%
剩余现金：40%
"""

    else:
        scene = "🔴 极端恐慌"
        advice = """
当前策略：执行第三档加仓

建议投入剩余资金：40%

累计投入：100%
剩余现金：0%
"""


# -----------------------
# 第一屏：核心指标
# -----------------------
c1, c2, c3 = st.columns(3)

c1.metric("恐惧贪婪指数", round(fg, 1), fear_status(fg))
c2.metric("VIX恐慌指数", vix if vix is not None else "获取失败", vix_status(vix))
c3.metric("综合市场风险", f"{risk_score}/100")

c4, c5, c6 = st.columns(3)

c4.metric("标普500回调", f"{spy_dd}%" if spy_dd is not None else "获取失败", drawdown_status(spy_dd))
c5.metric("纳斯达克100回调", f"{qqq_dd}%" if qqq_dd is not None else "获取失败", drawdown_status(qqq_dd))
c6.metric("RSP相对SPY", f"{rsp_vs_spy}%" if rsp_vs_spy is not None else "获取失败", relative_status(rsp_vs_spy))

c7, c8, c9 = st.columns(3)

c7.metric("IWM相对SPY", f"{iwm_vs_spy}%" if iwm_vs_spy is not None else "获取失败", relative_status(iwm_vs_spy))
c8.metric("HYG近60日", f"{hyg_change}%" if hyg_change is not None else "获取失败", credit_status(hyg_change))
c9.metric("JNK近60日", f"{jnk_change}%" if jnk_change is not None else "获取失败", credit_status(jnk_change))

st.markdown("---")


# -----------------------
# 市场状态
# -----------------------
st.subheader("市场状态")

if "🔴" in scene:
    st.error(scene)
elif "🟠" in scene:
    st.warning(scene)
elif "🟡" in scene:
    st.warning(scene)
elif "🟣" in scene:
    st.warning(scene)
else:
    st.success(scene)

st.subheader("美股回调加仓计划")
st.info(advice)

plan = pd.DataFrame(
    {
        "风险评分区间": ["0 - 20", "20 - 40", "40 - 60", "60以上"],
        "市场阶段": ["正常市场", "第一档回调", "第二档回调", "极端恐慌"],
        "资金动作": ["正常定投", "投入预备资金30%", "再投入预备资金30%", "投入剩余资金40%"],
        "累计投入": ["按定投计划", "30%", "60%", "100%"],
        "剩余现金": ["回调资金不动用", "70%", "40%", "0%"]
    }
)

st.dataframe(plan, use_container_width=True, hide_index=True)

st.markdown("---")


# -----------------------
# 详细信号
# -----------------------
st.subheader("详细市场信号")

signal_table = pd.DataFrame(
    {
        "层级": [
            "情绪层",
            "情绪层",
            "趋势层",
            "趋势层",
            "市场广度",
            "市场广度",
            "信用层",
            "信用层",
            "跨资产",
            "跨资产"
        ],
        "指标": [
            "Fear & Greed",
            "VIX",
            "SPY回调",
            "QQQ回调",
            "RSP相对SPY",
            "IWM相对SPY",
            "HYG近60日",
            "JNK近60日",
            "TLT近60日",
            "GLD近60日"
        ],
        "数值": [
            round(fg, 1),
            vix if vix is not None else "获取失败",
            f"{spy_dd}%" if spy_dd is not None else "获取失败",
            f"{qqq_dd}%" if qqq_dd is not None else "获取失败",
            f"{rsp_vs_spy}%" if rsp_vs_spy is not None else "获取失败",
            f"{iwm_vs_spy}%" if iwm_vs_spy is not None else "获取失败",
            f"{hyg_change}%" if hyg_change is not None else "获取失败",
            f"{jnk_change}%" if jnk_change is not None else "获取失败",
            f"{tlt_change}%" if tlt_change is not None else "获取失败",
            f"{gld_change}%" if gld_change is not None else "获取失败"
        ],
        "解释": [
            fear_status(fg),
            vix_status(vix),
            drawdown_status(spy_dd),
            drawdown_status(qqq_dd),
            relative_status(rsp_vs_spy),
            relative_status(iwm_vs_spy),
            credit_status(hyg_change),
            credit_status(jnk_change),
            "观察利率压力",
            "观察避险需求"
        ]
    }
)

st.dataframe(signal_table, use_container_width=True, hide_index=True)

st.markdown("---")

st.caption(
    f"更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)
