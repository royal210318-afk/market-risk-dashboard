```python
import streamlit as st
import requests
import pandas as pd
import yfinance as yf
import plotly.express as px
from datetime import datetime

st.set_page_config(
    page_title="市场风险仪表盘",
    page_icon="📈",
    layout="wide"
)

# -----------------------
# 密钥
# -----------------------
try:
    API_KEY = st.secrets["TWELVE_API_KEY"]
except Exception:
    API_KEY = ""


# -----------------------
# 页面标题
# -----------------------
st.title("📈 市场风险仪表盘 V7")
st.caption("美股回调加仓版 · 情绪 · 波动率 · 市场广度 · 信用风险 · 跨资产联动")


# -----------------------
# Fear & Greed 当前值 + 历史图表
# -----------------------
@st.cache_data(ttl=1800)
def get_fear_greed_data():
    try:
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        r = requests.get(url, timeout=20)
        data = r.json()

        score = float(data["fear_and_greed"]["score"])

        rows = []

        historical = data.get("fear_and_greed_historical", {})

        if isinstance(historical, dict):
            hist_data = historical.get("data", [])
        elif isinstance(historical, list):
            hist_data = historical
        else:
            hist_data = []

        for item in hist_data:
            x = item.get("x") or item.get("timestamp") or item.get("date")
            y = item.get("y") or item.get("score") or item.get("value")

            if x is None or y is None:
                continue

            try:
                if isinstance(x, (int, float)):
                    if x > 10000000000:
                        dt = pd.to_datetime(x, unit="ms")
                    else:
                        dt = pd.to_datetime(x, unit="s")
                else:
                    dt = pd.to_datetime(x)

                rows.append(
                    {
                        "date": dt,
                        "value": float(y)
                    }
                )
            except Exception:
                continue

        hist_df = pd.DataFrame(rows)

        if not hist_df.empty:
            hist_df = hist_df.dropna()
            hist_df = hist_df.sort_values("date")
            hist_df = hist_df.tail(90)

        return score, hist_df

    except Exception:
        return 50.0, pd.DataFrame(columns=["date", "value"])


# -----------------------
# VIX 当前值 + 历史图表
# -----------------------
@st.cache_data(ttl=1800)
def get_vix_data():
    try:
        vix = yf.Ticker("^VIX")
        hist = vix.history(period="6mo")

        if hist is None or hist.empty:
            return None, pd.DataFrame(columns=["date", "value"])

        hist = hist.reset_index()
        hist["date"] = pd.to_datetime(hist["Date"]).dt.tz_localize(None)
        hist["value"] = hist["Close"].astype(float)

        latest = round(float(hist["value"].iloc[-1]), 2)

        return latest, hist[["date", "value"]].tail(120)

    except Exception:
        return None, pd.DataFrame(columns=["date", "value"])


# -----------------------
# Twelve Data 历史数据
# -----------------------
@st.cache_data(ttl=1800)
def get_history(symbol):
    if not API_KEY:
        return None

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
        df["date"] = pd.to_datetime(df["datetime"])
        df["close"] = df["close"].astype(float)
        df["high"] = df["high"].astype(float)

        df = df.sort_values("date")

        return df[["date", "close", "high"]]

    except Exception:
        return None


# -----------------------
# 基础计算
# -----------------------
def latest_price(df):
    if df is None or df.empty:
        return None

    return round(float(df.iloc[-1]["close"]), 2)


def calc_drawdown(df):
    if df is None or df.empty:
        return None, None

    latest = float(df.iloc[-1]["close"])
    high52 = float(df["high"].max())
    drawdown = (latest - high52) / high52 * 100

    return round(latest, 2), round(drawdown, 2)


def calc_change(df, days=60):
    if df is None or df.empty or len(df) < days:
        return None

    latest = float(df.iloc[-1]["close"])
    past = float(df.iloc[-days]["close"])

    change = (latest - past) / past * 100

    return round(change, 2)


def make_return_series(df, days=60):
    if df is None or df.empty or len(df) < days:
        return pd.DataFrame(columns=["date", "value"])

    temp = df.tail(days).copy()

    start_price = float(temp.iloc[0]["close"])

    if start_price == 0:
        return pd.DataFrame(columns=["date", "value"])

    temp["value"] = (temp["close"] / start_price - 1) * 100
    temp["value"] = temp["value"].round(2)

    return temp[["date", "value"]]


def make_relative_series(df_a, df_b, days=60):
    if df_a is None or df_b is None or df_a.empty or df_b.empty:
        return pd.DataFrame(columns=["date", "value"])

    a = df_a[["date", "close"]].copy()
    b = df_b[["date", "close"]].copy()

    a = a.rename(columns={"close": "a_close"})
    b = b.rename(columns={"close": "b_close"})

    merged = pd.merge(a, b, on="date", how="inner")
    merged = merged.sort_values("date")

    if len(merged) < days:
        return pd.DataFrame(columns=["date", "value"])

    merged = merged.tail(days)

    a_start = float(merged.iloc[0]["a_close"])
    b_start = float(merged.iloc[0]["b_close"])

    if a_start == 0 or b_start == 0:
        return pd.DataFrame(columns=["date", "value"])

    merged["a_return"] = (merged["a_close"] / a_start - 1) * 100
    merged["b_return"] = (merged["b_close"] / b_start - 1) * 100
    merged["value"] = merged["a_return"] - merged["b_return"]
    merged["value"] = merged["value"].round(2)

    return merged[["date", "value"]]


# -----------------------
# 状态解释
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


def vix_status(vix):
    if vix is None:
        return "获取失败"
    if vix <= 15:
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
    elif diff > 2:
        return "广度较好"
    else:
        return "广度正常"


def credit_status(change):
    if change is None:
        return "获取失败"
    if change < -5:
        return "信用风险升温"
    elif change < -2:
        return "信用偏弱"
    elif change > 2:
        return "信用稳定偏强"
    else:
        return "信用稳定"


def cross_asset_status(tlt_change, gld_change):
    if tlt_change is None or gld_change is None:
        return "获取失败"

    if gld_change > 5 and tlt_change < -3:
        return "通胀或货币信用压力"
    elif gld_change > 5 and tlt_change > 3:
        return "避险或衰退担忧"
    elif tlt_change < -5:
        return "利率压力偏大"
    elif tlt_change > 5:
        return "利率压力缓和"
    else:
        return "跨资产中性"


# -----------------------
# 单项评分
# -----------------------
def score_fear(fg):
    if fg is None:
        return None
    if fg < 25:
        return 80
    elif fg < 45:
        return 50
    elif fg < 75:
        return 20
    else:
        return 70


def score_vix(vix):
    if vix is None:
        return None
    if vix <= 15:
        return 25
    elif vix < 20:
        return 20
    elif vix < 30:
        return 50
    else:
        return 85


def score_drawdown(dd):
    if dd is None:
        return None
    if dd > -5:
        return 10
    elif dd > -10:
        return 40
    elif dd > -20:
        return 70
    else:
        return 90


def score_relative(diff):
    if diff is None:
        return None
    if diff < -5:
        return 70
    elif diff < -2:
        return 45
    else:
        return 20


def score_credit(change):
    if change is None:
        return None
    if change < -5:
        return 85
    elif change < -2:
        return 55
    else:
        return 15


def score_cross_asset(tlt_change, gld_change):
    if tlt_change is None or gld_change is None:
        return None

    if gld_change > 5 and tlt_change < -3:
        return 75
    elif gld_change > 5 and tlt_change > 3:
        return 55
    elif tlt_change < -5:
        return 55
    elif tlt_change > 5:
        return 25
    else:
        return 20


def average_score(values):
    valid = [v for v in values if v is not None]
    if not valid:
        return 0
    return round(sum(valid) / len(valid))


def risk_level(score):
    if score < 20:
        return "低风险"
    elif score < 40:
        return "轻度回调"
    elif score < 60:
        return "中等风险"
    else:
        return "高风险"


# -----------------------
# 图表函数
# -----------------------
def show_line_chart(df, title, y_title, threshold_lines=None):
    if df is None or df.empty:
        st.warning("暂无足够数据生成图表")
        return

    fig = px.line(
        df,
        x="date",
        y="value",
        labels={
            "date": "日期",
            "value": y_title
        },
        title=title
    )

    fig.update_layout(
        height=340,
        margin=dict(l=20, r=20, t=60, b=20),
        hovermode="x unified"
    )

    if threshold_lines:
        for line in threshold_lines:
            fig.add_hline(
                y=line["y"],
                line_dash="dash",
                annotation_text=line["text"],
                annotation_position="top left"
            )

    st.plotly_chart(fig, use_container_width=True)


# -----------------------
# 获取数据
# -----------------------
fg, fg_hist_df = get_fear_greed_data()
vix, vix_hist_df = get_vix_data()

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

spy_change = calc_change(spy_df, 60)
rsp_change = calc_change(rsp_df, 60)
iwm_change = calc_change(iwm_df, 60)
hyg_change = calc_change(hyg_df, 60)
jnk_change = calc_change(jnk_df, 60)
tlt_change = calc_change(tlt_df, 60)
gld_change = calc_change(gld_df, 60)

rsp_vs_spy = round(rsp_change - spy_change, 2) if rsp_change is not None and spy_change is not None else None
iwm_vs_spy = round(iwm_change - spy_change, 2) if iwm_change is not None and spy_change is not None else None

rsp_vs_spy_series = make_relative_series(rsp_df, spy_df, 60)
iwm_vs_spy_series = make_relative_series(iwm_df, spy_df, 60)
hyg_series = make_return_series(hyg_df, 60)
jnk_series = make_return_series(jnk_df, 60)

hyg_price = latest_price(hyg_df)
jnk_price = latest_price(jnk_df)
tlt_price = latest_price(tlt_df)
gld_price = latest_price(gld_df)


# -----------------------
# 四大子评分
# -----------------------
emotion_score = average_score(
    [
        score_fear(fg),
        score_vix(vix)
    ]
)

breadth_score = average_score(
    [
        score_relative(rsp_vs_spy),
        score_relative(iwm_vs_spy)
    ]
)

credit_score = average_score(
    [
        score_credit(hyg_change),
        score_credit(jnk_change)
    ]
)

cross_asset_score = average_score(
    [
        score_cross_asset(tlt_change, gld_change)
    ]
)

trend_score = average_score(
    [
        score_drawdown(spy_dd),
        score_drawdown(qqq_dd)
    ]
)

risk_score = average_score(
    [
        emotion_score,
        trend_score,
        breadth_score,
        credit_score,
        cross_asset_score
    ]
)


# -----------------------
# 关键风险判断
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

normal_pullback = (
    risk_score >= 20
    and risk_score < 60
    and not credit_warning
)


# -----------------------
# 当前买入等级
# -----------------------
if credit_warning:
    buy_grade = "D级风险"
    buy_action = "信用市场恶化，暂停抄底，优先保留现金。"
    scene = "🔴 信用风险升温"
    advice = """
当前策略：暂停抄底，优先观察信用市场。

如果股市下跌，同时 HYG/JNK 也明显下跌，
说明市场不只是估值调整，而是在担心企业违约和融资压力。

这种时候不要急着加仓，先等信用市场稳定。
"""

elif good_buy_window:
    buy_grade = "A级机会"
    buy_action = "恐慌充分但信用未失控，可以重点分批加仓。"
    scene = "🟠 优质加仓窗口"
    advice = """
当前策略：重点关注加仓机会。

VIX超过30，Fear & Greed低于25，
说明市场已经出现明显恐慌。

如果 HYG/JNK 没有同步崩盘，
这通常是比较好的分批加仓窗口。
"""

elif fomo_warning:
    buy_grade = "E级过热"
    buy_action = "市场过度乐观，不适合追高。"
    scene = "🟣 市场过热"
    advice = """
当前策略：谨慎追高。

Fear & Greed 高于75，同时 VIX 低于或接近15，
说明市场不愿意给风险定价，FOMO情绪较强。

这种环境不适合大幅加仓。
"""

elif normal_pullback:
    buy_grade = "B级机会"
    buy_action = "市场出现回调但信用未失控，可以按计划分批加仓。"

    if risk_score < 40:
        scene = "🟡 第一档回调"
        advice = """
当前策略：执行第一档加仓。

建议投入预备资金：30%。

累计投入：30%
剩余现金：70%
"""
    else:
        scene = "🟠 第二档回调"
        advice = """
当前策略：执行第二档加仓。

建议再投入预备资金：30%。

累计投入：60%
剩余现金：40%
"""

elif breadth_warning:
    buy_grade = "C级观察"
    buy_action = "上涨广度偏弱，谨慎观察，不盲目追高。"
    scene = "🟡 上涨广度偏弱"
    advice = """
当前策略：谨慎观察。

RSP相对SPY或IWM相对SPY明显走弱，
说明指数上涨可能主要由少数权重股推动。

这种上涨不够健康，不适合盲目追高。
"""

elif risk_score >= 60:
    buy_grade = "B级机会"
    buy_action = "恐慌较高，但仍需确认信用市场是否稳定。"
    scene = "🔴 极端恐慌"
    advice = """
当前策略：执行第三档加仓。

建议投入剩余资金：40%。

累计投入：100%
剩余现金：0%

但前提是：HYG/JNK 没有明显崩盘。
"""

else:
    buy_grade = "C级观察"
    buy_action = "市场风险较低，继续正常定投，回调资金暂不动用。"
    scene = "🟢 正常市场"
    advice = """
当前策略：正常定投。

市场风险较低，按原计划持续定投即可。

回调加仓资金暂不动用。
"""


# -----------------------
# 第一部分：第一屏结论
# -----------------------
st.subheader("一、当前结论")

col_a, col_b, col_c = st.columns(3)

col_a.metric(
    "当前市场状态",
    scene
)

col_b.metric(
    "当前买入等级",
    buy_grade
)

col_c.metric(
    "综合风险评分",
    f"{risk_score}/100",
    risk_level(risk_score)
)

st.info(buy_action)

st.markdown("---")


# -----------------------
# 第二部分：核心指标卡片
# -----------------------
st.subheader("二、核心指标")

c1, c2, c3 = st.columns(3)

c1.metric(
    "恐惧贪婪指数 Fear & Greed",
    round(fg, 1),
    fear_status(fg)
)

c2.metric(
    "VIX恐慌指数 VIX",
    vix if vix is not None else "获取失败",
    vix_status(vix)
)

c3.metric(
    "SPY标普500回调",
    f"{spy_dd}%" if spy_dd is not None else "获取失败",
    drawdown_status(spy_dd)
)

c4, c5, c6 = st.columns(3)

c4.metric(
    "QQQ纳斯达克100回调",
    f"{qqq_dd}%" if qqq_dd is not None else "获取失败",
    drawdown_status(qqq_dd)
)

c5.metric(
    "RSP相对SPY",
    f"{rsp_vs_spy}%" if rsp_vs_spy is not None else "获取失败",
    relative_status(rsp_vs_spy)
)

c6.metric(
    "IWM相对SPY",
    f"{iwm_vs_spy}%" if iwm_vs_spy is not None else "获取失败",
    relative_status(iwm_vs_spy)
)

c7, c8, c9 = st.columns(3)

c7.metric(
    "HYG近60日",
    f"{hyg_change}%" if hyg_change is not None else "获取失败",
    credit_status(hyg_change)
)

c8.metric(
    "JNK近60日",
    f"{jnk_change}%" if jnk_change is not None else "获取失败",
    credit_status(jnk_change)
)

c9.metric(
    "跨资产状态",
    cross_asset_status(tlt_change, gld_change)
)

st.markdown("---")


# -----------------------
# 第三部分：四大风险来源
# -----------------------
st.subheader("三、风险来源拆解")

s1, s2, s3, s4, s5 = st.columns(5)

s1.metric("情绪风险", f"{emotion_score}/100", risk_level(emotion_score))
s2.metric("趋势风险", f"{trend_score}/100", risk_level(trend_score))
s3.metric("广度风险", f"{breadth_score}/100", risk_level(breadth_score))
s4.metric("信用风险", f"{credit_score}/100", risk_level(credit_score))
s5.metric("跨资产风险", f"{cross_asset_score}/100", risk_level(cross_asset_score))

risk_source_table = pd.DataFrame(
    {
        "模块": [
            "情绪层",
            "趋势层",
            "市场广度",
            "信用市场",
            "跨资产"
        ],
        "代表指标": [
            "Fear & Greed、VIX",
            "SPY回调、QQQ回调",
            "RSP相对SPY、IWM相对SPY",
            "HYG、JNK",
            "TLT、GLD"
        ],
        "当前判断": [
            f"{fear_status(fg)} / {vix_status(vix)}",
            f"SPY：{drawdown_status(spy_dd)}，QQQ：{drawdown_status(qqq_dd)}",
            f"RSP：{relative_status(rsp_vs_spy)}，IWM：{relative_status(iwm_vs_spy)}",
            f"HYG：{credit_status(hyg_change)}，JNK：{credit_status(jnk_change)}",
            cross_asset_status(tlt_change, gld_change)
        ],
        "解释": [
            "判断市场是恐惧、贪婪，还是机构正在买保险。",
            "判断指数距离高点有多远，是否已经进入回调区。",
            "判断上涨是否由多数股票推动，还是少数权重股支撑。",
            "判断企业融资环境是否恶化，是否存在系统性风险。",
            "判断利率、黄金和避险情绪是否出现异常联动。"
        ]
    }
)

st.dataframe(
    risk_source_table,
    use_container_width=True,
    hide_index=True
)

st.markdown("---")


# -----------------------
# 第四部分：核心图表
# -----------------------
st.subheader("四、核心指标图表")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "Fear & Greed",
        "VIX",
        "RSP相对SPY",
        "IWM相对SPY",
        "HYG近60日",
        "JNK近60日"
    ]
)

with tab1:
    show_line_chart(
        fg_hist_df,
        "Fear & Greed 恐惧贪婪指数",
        "分数",
        threshold_lines=[
            {"y": 25, "text": "25：极度恐惧"},
            {"y": 75, "text": "75：极度贪婪"}
        ]
    )
    st.caption("低于25代表极度恐惧，高于75代表极度贪婪。")

with tab2:
    show_line_chart(
        vix_hist_df,
        "VIX恐慌指数",
        "VIX",
        threshold_lines=[
            {"y": 15, "text": "15：过度乐观"},
            {"y": 30, "text": "30：恐慌区"}
        ]
    )
    st.caption("VIX越高，说明期权市场给风险保险支付的价格越高。")

with tab3:
    show_line_chart(
        rsp_vs_spy_series,
        "RSP相对SPY",
        "相对表现 %",
        threshold_lines=[
            {"y": 0, "text": "0：等权与市值加权持平"},
            {"y": -5, "text": "-5：广度明显偏弱"}
        ]
    )
    st.caption("RSP跑输SPY，说明上涨可能集中在少数大权重股票上。")

with tab4:
    show_line_chart(
        iwm_vs_spy_series,
        "IWM相对SPY",
        "相对表现 %",
        threshold_lines=[
            {"y": 0, "text": "0：小盘与大盘持平"},
            {"y": -5, "text": "-5：小盘明显跑输"}
        ]
    )
    st.caption("IWM跑输SPY，说明资金没有扩散到小盘股，市场广度偏弱。")

with tab5:
    show_line_chart(
        hyg_series,
        "HYG近60日变化",
        "涨跌幅 %",
        threshold_lines=[
            {"y": 0, "text": "0：持平"},
            {"y": -5, "text": "-5：信用风险升温"}
        ]
    )
    st.caption("HYG大跌说明高收益债承压，信用市场可能开始担心违约风险。")

with tab6:
    show_line_chart(
        jnk_series,
        "JNK近60日变化",
        "涨跌幅 %",
        threshold_lines=[
            {"y": 0, "text": "0：持平"},
            {"y": -5, "text": "-5：信用风险升温"}
        ]
    )
    st.caption("JNK与HYG互相验证，如果两者同步大跌，要警惕信用风险。")

st.markdown("---")


# -----------------------
# 第五部分：指标意义
# -----------------------
st.subheader("五、指标意义说明")

meaning_table = pd.DataFrame(
    {
        "指标": [
            "RSP相对SPY",
            "IWM相对SPY",
            "HYG近60日",
            "JNK近60日",
            "TLT近60日",
            "GLD近60日"
        ],
        "代表含义": [
            "市场广度：等权标普500相对市值加权标普500的表现。",
            "资金扩散：小盘股相对大盘股的表现。",
            "信用风险：高收益债ETF的价格变化。",
            "信用风险交叉验证：另一只高收益债ETF的表现。",
            "利率压力：长期美债价格变化，通常与长期利率反向。",
            "避险与通胀：黄金价格变化，反映避险需求或通胀担忧。"
        ],
        "怎么看": [
            "RSP跑输SPY，说明指数上涨可能由少数巨头推动，市场广度偏弱。",
            "IWM跑输SPY，说明资金没有扩散到小盘股，风险偏好不够强。",
            "HYG稳定，说明信用市场没失控；HYG大跌，要警惕融资压力。",
            "JNK和HYG一起跌，说明信用市场压力更可信。",
            "TLT上涨通常代表利率下行；TLT下跌通常代表利率上行，对科技股估值不利。",
            "GLD上涨加TLT上涨，多是避险或衰退担忧；GLD上涨但TLT下跌，可能是通胀或货币信用压力。"
        ],
        "交易含义": [
            "如果指数涨但RSP明显跑输SPY，不宜盲目追高。",
            "如果SPY涨但IWM弱，说明牛市扩散不充分。",
            "股市跌但HYG稳定，多数是估值调整，可以考虑分批加仓。",
            "股市跌且JNK/HYG同步大跌，不要急着抄底。",
            "美股跌且TLT也跌，可能是利率上行导致估值压缩，等利率稳定后再加仓。",
            "黄金涨要结合TLT看，区分是衰退避险还是通胀压力。"
        ]
    }
)

st.dataframe(
    meaning_table,
    use_container_width=True,
    hide_index=True
)

st.markdown("---")


# -----------------------
# 第六部分：加仓计划
# -----------------------
st.subheader("六、美股回调加仓计划")

st.info(advice)

plan = pd.DataFrame(
    {
        "等级": [
            "A级机会",
            "B级机会",
            "C级观察",
            "D级风险",
            "E级过热"
        ],
        "典型条件": [
            "VIX > 30，Fear & Greed < 25，信用市场稳定",
            "市场出现回调，信用市场没有失控",
            "情绪中性，指数接近高位，风险不高",
            "HYG/JNK同步大跌，信用市场恶化",
            "Fear & Greed > 75，VIX <= 15，市场FOMO"
        ],
        "动作": [
            "重点分批加仓",
            "按计划分批加仓",
            "正常定投，回调资金暂不动用",
            "暂停抄底，保留现金",
            "避免追高，适当降低进攻性"
        ],
        "预备资金使用": [
            "可投入30%~60%，视信用市场决定",
            "第一档30%，第二档再30%",
            "0%",
            "0%",
            "0%，必要时减仓"
        ]
    }
)

st.dataframe(
    plan,
    use_container_width=True,
    hide_index=True
)

st.markdown("---")

st.caption(
    f"更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)
```
