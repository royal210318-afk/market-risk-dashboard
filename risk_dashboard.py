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
st.caption("恐惧贪婪指数 · VIX恐慌指数 · 标普500 · 纳斯达克100 · 美债ETF · 黄金ETF")


# -----------------------
# Fear & Greed
# -----------------------
@st.cache_data(ttl=1800)
def get_fear_greed():
    try:
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        r = requests.get(url, timeout=20)
        data = r.json()
        return float(data["fear_and_greed"]["score"])
    except:
        return 50.0


# -----------------------
# VIX：Yahoo Finance
# -----------------------
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


# -----------------------
# Twelve Data：历史数据
# -----------------------
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


# -----------------------
# 计算回调
# -----------------------
def calc_drawdown(df):
    if df is None or df.empty:
        return None, None

    latest = float(df.iloc[0]["close"])
    high52 = float(df["high"].max())

    drawdown = (latest - high52) / high52 * 100

    return round(latest, 2), round(drawdown, 2)


# -----------------------
# 指标状态
# -----------------------
def fear_status(fg):
    if fg < 25:
        return "极度恐惧"
    elif fg < 45:
        return "恐惧"
    elif fg < 75:
        return "中性"
    else:
        return "极度贪婪"


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


def vix_status(vix):
    if vix is None:
        return "获取失败"
    if vix < 18:
        return "低波动"
    elif vix < 25:
        return "正常波动"
    elif vix < 35:
        return "恐慌升温"
    else:
        return "极端恐慌"


# -----------------------
# 获取数据
# -----------------------
fg = get_fear_greed()
vix = get_vix()

spy_df = get_history("SPY")
qqq_df = get_history("QQQ")
tlt_df = get_history("TLT")
gld_df = get_history("GLD")

spy_price, spy_dd = calc_drawdown(spy_df)
qqq_price, qqq_dd = calc_drawdown(qqq_df)

tlt_price = round(float(tlt_df.iloc[0]["close"]), 2) if tlt_df is not None else None
gld_price = round(float(gld_df.iloc[0]["close"]), 2) if gld_df is not None else None


# -----------------------
# 风险评分
# -----------------------
risk = 0
valid_items = 0

# Fear & Greed
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

# VIX
if vix is not None:
    valid_items += 1
    if vix < 18:
        risk += 10
    elif vix < 25:
        risk += 30
    elif vix < 35:
        risk += 60
    else:
        risk += 90

# SPY
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

# QQQ
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

risk_score = round(risk / valid_items) if valid_items > 0 else 0


# -----------------------
# 场景：美股回调加仓策略
# -----------------------
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
# 指标卡片
# -----------------------
c1, c2, c3 = st.columns(3)

c1.metric(
    "恐惧贪婪指数",
    round(fg, 1),
    fear_status(fg)
)

c2.metric(
    "VIX恐慌指数",
    vix if vix is not None else "获取失败",
    vix_status(vix)
)

c3.metric(
    "综合市场风险",
    f"{risk_score}/100"
)

c4, c5, c6 = st.columns(3)

c4.metric(
    "标普500回调",
    f"{spy_dd}%" if spy_dd is not None else "获取失败",
    drawdown_status(spy_dd)
)

c5.metric(
    "纳斯达克100回调",
    f"{qqq_dd}%" if qqq_dd is not None else "获取失败",
    drawdown_status(qqq_dd)
)

c6.metric(
    "美国20年期国债ETF",
    tlt_price if tlt_price is not None else "获取失败"
)

c7, c8, c9 = st.columns(3)

c7.metric(
    "黄金ETF",
    gld_price if gld_price is not None else "获取失败"
)

c8.metric(
    "SPY最新价",
    spy_price if spy_price is not None else "获取失败"
)

c9.metric(
    "QQQ最新价",
    qqq_price if qqq_price is not None else "获取失败"
)

st.markdown("---")


# -----------------------
# 市场状态
# -----------------------
st.subheader("市场状态")

if risk_score < 20:
    st.success(scene)
elif risk_score < 40:
    st.warning(scene)
elif risk_score < 60:
    st.warning(scene)
else:
    st.error(scene)


# -----------------------
# 美股回调加仓计划
# -----------------------
st.subheader("美股回调加仓计划")

st.info(advice)

plan = pd.DataFrame(
    {
        "风险评分区间": [
            "0 - 20",
            "20 - 40",
            "40 - 60",
            "60以上"
        ],
        "市场阶段": [
            "正常市场",
            "第一档回调",
            "第二档回调",
            "极端恐慌"
        ],
        "资金动作": [
            "正常定投",
            "投入预备资金30%",
            "再投入预备资金30%",
            "投入剩余资金40%"
        ],
        "累计投入": [
            "按定投计划",
            "30%",
            "60%",
            "100%"
        ],
        "剩余现金": [
            "回调资金不动用",
            "70%",
            "40%",
            "0%"
        ]
    }
)

st.dataframe(
    plan,
    use_container_width=True,
    hide_index=True
)

st.markdown("---")


# -----------------------
# 当前市场信号
# -----------------------
st.subheader("当前市场信号")

signal_table = pd.DataFrame(
    {
        "指标": [
            "恐惧贪婪指数",
            "VIX恐慌指数",
            "标普500回调",
            "纳斯达克100回调",
            "美国20年期国债ETF",
            "黄金ETF"
        ],
        "数值": [
            round(fg, 1),
            vix if vix is not None else "获取失败",
            f"{spy_dd}%" if spy_dd is not None else "获取失败",
            f"{qqq_dd}%" if qqq_dd is not None else "获取失败",
            tlt_price if tlt_price is not None else "获取失败",
            gld_price if gld_price is not None else "获取失败"
        ],
        "状态": [
            fear_status(fg),
            vix_status(vix),
            drawdown_status(spy_dd),
            drawdown_status(qqq_dd),
            "观察利率预期",
            "观察避险需求"
        ]
    }
)

st.dataframe(
    signal_table,
    use_container_width=True,
    hide_index=True
)

st.markdown("---")

st.caption(
    f"更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)
