import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="市场风险仪表盘",
    page_icon="📈",
    layout="wide"
)

PASSWORD = "123456"

ALPHA_KEYS = st.secrets.get("ALPHA_KEYS", [
    "I8KWVE0BZQHLGAWJ",
    "BO4ESK7CZQ5ENDZ2",
    "PYZP0ZMKFOYVY3D4"
])

pwd = st.sidebar.text_input("请输入密码", type="password")

if pwd != PASSWORD:
    st.warning("请输入正确密码")
    st.stop()

st.title("📈 市场风险仪表盘")
st.caption("VIXY / 恐惧贪婪指数 / SPY距离52周高点 / QQQ距离52周高点 / UUP / HYG / 场景判断")


@st.cache_data(ttl=14400)
def alpha_daily(symbol, outputsize="compact"):
    url = "https://www.alphavantage.co/query"

    for key in ALPHA_KEYS:
        try:
            r = requests.get(
                url,
                params={
                    "function": "TIME_SERIES_DAILY",
                    "symbol": symbol,
                    "apikey": key,
                    "outputsize": outputsize
                },
                timeout=20
            )
            data = r.json()

            if "Time Series (Daily)" in data:
                df = pd.DataFrame(data["Time Series (Daily)"]).T
                df.index = pd.to_datetime(df.index)
                df = df.sort_index()
                df["close"] = df["4. close"].astype(float)
                return df
        except:
            continue

    return None


@st.cache_data(ttl=14400)
def alpha_latest(symbol):
    df = alpha_daily(symbol, "compact")
    if df is None or df.empty:
        return None
    return round(float(df["close"].iloc[-1]), 2)


@st.cache_data(ttl=14400)
def alpha_distance_from_52week_high(symbol):
    df = alpha_daily(symbol, "full")
    if df is None or df.empty:
        return None

    close = df["close"]
    if len(close) < 252:
        return None

    current = float(close.iloc[-1])
    high_52week = float(close.tail(252).max())

    return round((current - high_52week) / high_52week * 100, 2)


@st.cache_data(ttl=14400)
def get_fear_greed():
    urls = [
        "https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
        "https://production.dataviz.cnn.io/index/fearandgreed/graphdata/2025-01-01"
    ]

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json,text/plain,*/*",
        "Referer": "https://www.cnn.com/markets/fear-and-greed"
    }

    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=20)
            data = r.json()
            score = data["fear_and_greed"].get("score")
            if score is not None:
                return round(float(score), 1)
        except:
            continue

    return 60.0


def vix_status(x):
    if x is None:
        return "获取失败", 0
    if x < 18:
        return "低波动", 10
    elif x < 25:
        return "正常波动", 25
    elif x < 35:
        return "恐慌升温", 55
    else:
        return "极端恐慌", 85


def fear_status(x):
    if x is None:
        return "获取失败", 0
    if x < 25:
        return "极度恐惧", 80
    elif x < 45:
        return "恐惧", 55
    elif x < 75:
        return "中性", 25
    else:
        return "极度贪婪", 75


def high_distance_status(x):
    if x is None:
        return "获取失败", 0
    if x > -5:
        return "接近52周新高", 10
    elif x > -10:
        return "正常回调", 40
    elif x > -20:
        return "深度回调", 70
    else:
        return "熊市区域", 90


def credit_status(x):
    if x is None:
        return "获取失败", 0
    if x >= 78:
        return "信用市场稳定", 10
    elif x >= 74:
        return "信用市场转弱", 45
    else:
        return "信用风险上升", 80


def dollar_status(x):
    if x is None:
        return "获取失败", 0
    if x < 28:
        return "美元正常", 15
    elif x < 30:
        return "美元偏强", 40
    else:
        return "美元过强", 70


with st.spinner("正在获取市场数据..."):
    vixy = alpha_latest("VIXY")
    uup = alpha_latest("UUP")
    hyg = alpha_latest("HYG")

    spy_price = alpha_latest("SPY")
    qqq_price = alpha_latest("QQQ")

    spy_dist = alpha_distance_from_52week_high("SPY")
    qqq_dist = alpha_distance_from_52week_high("QQQ")

    fg = get_fear_greed()


vix_text, vix_score = vix_status(vixy)
fg_text, fg_score = fear_status(fg)
spy_text, spy_score = high_distance_status(spy_dist)
qqq_text, qqq_score = high_distance_status(qqq_dist)
credit_text, credit_score = credit_status(hyg)
dollar_text, dollar_score = dollar_status(uup)

valid_scores = [
    score
    for value, score in [
        (vixy, vix_score),
        (fg, fg_score),
        (spy_dist, spy_score),
        (qqq_dist, qqq_score),
        (hyg, credit_score),
        (uup, dollar_score)
    ]
    if value is not None
]

risk_score = round(sum(valid_scores) / len(valid_scores)) if valid_scores else 0

scene = "🟢 场景一：市场正常，可以正常定投"
advice = "市场整体尚可，按计划执行，避免情绪化交易。"
market_signal = "🟢 市场正常"

if fg is not None and fg > 75:
    scene = "🟣 场景五：过度贪婪，考虑减仓"
    advice = "市场情绪偏热，避免追高。可以降低进攻性仓位，保留现金。"
    market_signal = "🟣 市场偏热"

if spy_dist is not None and -10 <= spy_dist <= -5:
    scene = "🟡 场景二：正常回调，可以分批加仓"
    advice = "指数进入回调区间，可以小仓位分批布局，但不要一次性满仓。"
    market_signal = "🟡 市场回调"

if fg is not None and fg < 25 and spy_dist is not None and spy_dist <= -7:
    scene = "🟠 场景三：极端恐慌，关注抄底机会"
    advice = "恐慌较强，但如果信用市场没有崩，可以关注核心资产，分批买入。"
    market_signal = "🟠 极端恐慌"

if risk_score >= 70 or (hyg is not None and hyg < 74):
    scene = "🔴 场景四：系统性风险，先防守"
    advice = "优先控制仓位，不要急着抄底。降低杠杆和高Beta资产，等待信用市场稳定。"
    market_signal = "🔴 系统风险"


st.subheader("当前市场信号")
st.success(market_signal)

st.write(
    f"VIXY：{vixy}（{vix_text}）｜"
    f"恐惧贪婪：{fg}（{fg_text}）｜"
    f"HYG：{hyg}（{credit_text}）｜"
    f"UUP：{uup}（{dollar_text}）"
)

st.markdown("---")

c1, c2, c3 = st.columns(3)

c1.metric("VIX替代指标 VIXY", vixy if vixy is not None else "失败", vix_text)
c2.metric("恐惧贪婪指数", fg if fg is not None else "失败", fg_text)
c3.metric("标普500 距离52周高点", f"{spy_dist}%" if spy_dist is not None else "失败", spy_text)

c4, c5, c6 = st.columns(3)

c4.metric("纳斯达克 距离52周高点", f"{qqq_dist}%" if qqq_dist is not None else "失败", qqq_text)
c5.metric("美元指数替代 UUP", uup if uup is not None else "失败", dollar_text)
c6.metric("信用债 HYG", hyg if hyg is not None else "失败", credit_text)

st.markdown("---")

st.subheader("当前市场场景")
st.success(scene)

st.metric("综合风险评分", f"{risk_score}/100")

st.subheader("操作参考")
st.info(advice)

st.markdown("---")

st.subheader("详细指标")

table = pd.DataFrame(
    [
        ["VIXY", vixy, vix_text],
        ["恐惧贪婪指数", fg, fg_text],
        ["SPY价格", spy_price, "标普500ETF"],
        ["SPY距离52周高点", f"{spy_dist}%" if spy_dist is not None else None, spy_text],
        ["QQQ价格", qqq_price, "纳斯达克ETF"],
        ["QQQ距离52周高点", f"{qqq_dist}%" if qqq_dist is not None else None, qqq_text],
        ["UUP", uup, dollar_text],
        ["HYG", hyg, credit_text],
    ],
    columns=["指标", "数值", "状态"]
)

st.dataframe(table, use_container_width=True)

st.markdown("---")

st.caption(
    f"更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ｜ "
    "数据源：Alpha Vantage + CNN Fear & Greed。仅供辅助判断，不构成投资建议。"
)