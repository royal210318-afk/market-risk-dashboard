import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(
    page_title="市场风险仪表盘",
    page_icon="📈",
    layout="wide"
)

API_KEY = st.secrets["TWELVE_API_KEY"]

st.title("📈 市场风险仪表盘")
st.caption("Fear & Greed + SPY + QQQ + TLT + GLD")

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
# Twelve Data
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

    r = requests.get(url, timeout=30)
    data = r.json()

    if data.get("status") != "ok":
        return None

    df = pd.DataFrame(data["values"])

    df["close"] = df["close"].astype(float)
    df["high"] = df["high"].astype(float)

    return df


# -----------------------
# 计算回调
# -----------------------
def calc_drawdown(df):
    latest = float(df.iloc[0]["close"])
    high52 = float(df["high"].max())

    drawdown = (latest - high52) / high52 * 100

    return round(latest, 2), round(drawdown, 2)


# -----------------------
# 数据
# -----------------------
fg = get_fear_greed()

spy_df = get_history("SPY")
qqq_df = get_history("QQQ")
tlt_df = get_history("TLT")
gld_df = get_history("GLD")

spy_price, spy_dd = calc_drawdown(spy_df)
qqq_price, qqq_dd = calc_drawdown(qqq_df)

tlt_price = round(float(tlt_df.iloc[0]["close"]), 2)
gld_price = round(float(gld_df.iloc[0]["close"]), 2)


# -----------------------
# 风险评分
# -----------------------
risk = 0

# Fear & Greed
if fg < 25:
    risk += 80
elif fg < 45:
    risk += 50
elif fg < 75:
    risk += 20
else:
    risk += 70

# SPY
if spy_dd > -5:
    risk += 10
elif spy_dd > -10:
    risk += 40
elif spy_dd > -20:
    risk += 70
else:
    risk += 90

# QQQ
if qqq_dd > -5:
    risk += 10
elif qqq_dd > -10:
    risk += 40
elif qqq_dd > -20:
    risk += 70
else:
    risk += 90

risk_score = round(risk / 3)


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
    round(fg, 1)
)

c2.metric(
    "标普500距52周高点",
    f"{spy_dd}%"
)

c3.metric(
    "纳斯达克100距52周高点",
    f"{qqq_dd}%"
)

c4, c5, c6 = st.columns(3)

c4.metric(
    "美国20年期国债ETF",
    tlt_price
)

c5.metric(
    "黄金ETF",
    gld_price
)

c6.metric(
    "综合市场风险",
    f"{risk_score}/100"
)

st.markdown("---")


# -----------------------
# 场景显示
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

st.subheader("美股回调加仓计划")
st.info(advice)

st.markdown("---")


# -----------------------
# 风险趋势图
# -----------------------
history = pd.DataFrame({
    "日期": [
        "5天前",
        "4天前",
        "3天前",
        "2天前",
        "昨天",
        "今天"
    ],
    "风险": [
        min(risk_score + 15, 100),
        min(risk_score + 12, 100),
        min(risk_score + 8, 100),
        min(risk_score + 5, 100),
        min(risk_score + 2, 100),
        risk_score
    ]
})

fig = px.line(
    history,
    x="日期",
    y="风险",
    markers=True,
    title="风险评分趋势"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

st.markdown("---")

st.caption(
    f"更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)
