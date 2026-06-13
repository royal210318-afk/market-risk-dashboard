import streamlit as st
import requests
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

# =========================================================
# 页面设置
# =========================================================
st.set_page_config(
    page_title="市场风险仪表盘",
    page_icon="📊",
    layout="wide"
)

try:
    API_KEY = st.secrets["TWELVE_API_KEY"]
except Exception:
    API_KEY = ""


# =========================================================
# 明亮白底样式
# =========================================================
st.markdown("""
<style>
.stApp {
    background: #ffffff;
    color: #111827;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1180px;
}

.dashboard-header {
    padding: 1.2rem 0 1.4rem 0;
    border-bottom: 1px solid #e5e7eb;
    margin-bottom: 1.6rem;
}

.dashboard-title {
    font-size: 2rem;
    font-weight: 800;
    color: #111827;
    margin: 0;
    letter-spacing: -0.6px;
}

.dashboard-subtitle {
    font-size: 0.9rem;
    color: #6b7280;
    margin-top: 0.4rem;
}

h1, h2, h3 {
    color: #111827 !important;
    font-weight: 800 !important;
}

[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    padding: 1rem 1.1rem;
    box-shadow: 0 6px 18px rgba(17, 24, 39, 0.05);
}

[data-testid="stMetricLabel"] {
    color: #4b5563 !important;
    font-size: 0.82rem !important;
    font-weight: 650 !important;
}

[data-testid="stMetricValue"] {
    color: #111827 !important;
    font-size: 1.75rem !important;
    font-weight: 800 !important;
}

[data-testid="stMetricDelta"] {
    font-size: 0.78rem !important;
    font-weight: 650 !important;
}

.stAlert {
    border-radius: 14px !important;
    border: 1px solid #bfdbfe !important;
    background: #eff6ff !important;
    color: #1e3a8a !important;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 0.4rem;
    border-bottom: 1px solid #e5e7eb;
}

.stTabs [data-baseweb="tab"] {
    color: #374151 !important;
    font-weight: 650 !important;
    padding: 0.7rem 1rem !important;
}

.stTabs [aria-selected="true"] {
    color: #dc2626 !important;
    border-bottom: 3px solid #ef4444 !important;
}

.stDataFrame {
    border: 1px solid #e5e7eb !important;
    border-radius: 14px !important;
    overflow: hidden;
}

hr {
    border-color: #e5e7eb !important;
    margin: 2rem 0 !important;
}

.small-note {
    color: #6b7280;
    font-size: 0.86rem;
    line-height: 1.7;
}

.section-card {
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    padding: 1rem 1.1rem;
    margin: 0.8rem 0;
}

.badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 700;
}

.badge-green { background: #dcfce7; color: #166534; }
.badge-yellow { background: #fef9c3; color: #854d0e; }
.badge-orange { background: #ffedd5; color: #9a3412; }
.badge-red { background: #fee2e2; color: #991b1b; }
.badge-purple { background: #f3e8ff; color: #6b21a8; }
</style>
""", unsafe_allow_html=True)


# =========================================================
# 图表样式
# =========================================================
PLOTLY_LAYOUT = dict(
    paper_bgcolor="#ffffff",
    plot_bgcolor="#ffffff",
    font=dict(color="#111827", size=12),
    xaxis=dict(
        gridcolor="#e5e7eb",
        zerolinecolor="#d1d5db",
        linecolor="#d1d5db",
        tickfont=dict(color="#6b7280"),
    ),
    yaxis=dict(
        gridcolor="#e5e7eb",
        zerolinecolor="#d1d5db",
        linecolor="#d1d5db",
        tickfont=dict(color="#6b7280"),
    ),
    margin=dict(l=40, r=20, t=55, b=40),
    hovermode="x unified",
)

LINE_COLOR = "#2563eb"
THRESHOLD_COLOR = "#dc2626"


# =========================================================
# 数据获取
# =========================================================
@st.cache_data(ttl=1800)
def get_fear_greed_data():
    try:
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        r = requests.get(url, timeout=20)
        data = r.json()
        score = float(data["fear_and_greed"]["score"])

        rows = []
        historical = data.get("fear_and_greed_historical", {})
        hist_data = historical.get("data", []) if isinstance(historical, dict) else historical

        if isinstance(hist_data, list):
            for item in hist_data:
                x = item.get("x") or item.get("timestamp") or item.get("date")
                y = item.get("y") or item.get("score") or item.get("value")
                if x is None or y is None:
                    continue
                try:
                    if isinstance(x, (int, float)):
                        dt = pd.to_datetime(x, unit="ms") if x > 10000000000 else pd.to_datetime(x, unit="s")
                    else:
                        dt = pd.to_datetime(x)
                    rows.append({"date": dt, "value": float(y)})
                except Exception:
                    pass

        hist_df = pd.DataFrame(rows)
        if not hist_df.empty:
            hist_df = hist_df.dropna().sort_values("date").tail(90)

        return score, hist_df

    except Exception:
        return 50.0, pd.DataFrame(columns=["date", "value"])


@st.cache_data(ttl=1800)
def get_yf_history(symbol, period="6mo"):
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        if hist is None or hist.empty:
            return None
        hist = hist.reset_index()
        date_col = "Date" if "Date" in hist.columns else hist.columns[0]
        hist["date"] = pd.to_datetime(hist[date_col]).dt.tz_localize(None)
        hist["close"] = hist["Close"].astype(float)
        hist["high"] = hist["High"].astype(float)
        return hist[["date", "close", "high"]].sort_values("date")
    except Exception:
        return None


@st.cache_data(ttl=1800)
def get_twelve_history(symbol):
    if not API_KEY:
        return get_yf_history(symbol, period="1y")

    url = (
        f"https://api.twelvedata.com/time_series"
        f"?symbol={symbol}&interval=1day&outputsize=260&apikey={API_KEY}"
    )

    try:
        r = requests.get(url, timeout=30)
        data = r.json()

        if data.get("status") != "ok":
            return get_yf_history(symbol, period="1y")

        df = pd.DataFrame(data["values"])
        df["date"] = pd.to_datetime(df["datetime"])
        df["close"] = df["close"].astype(float)
        df["high"] = df["high"].astype(float)
        return df[["date", "close", "high"]].sort_values("date")

    except Exception:
        return get_yf_history(symbol, period="1y")


@st.cache_data(ttl=1800)
def get_vix_data():
    df = get_yf_history("^VIX", period="6mo")
    if df is None or df.empty:
        return None, pd.DataFrame(columns=["date", "value"])

    out = df[["date", "close"]].rename(columns={"close": "value"}).tail(120)
    latest = round(float(out.iloc[-1]["value"]), 2)
    return latest, out


# =========================================================
# 计算函数
# =========================================================
def latest_price(df):
    if df is None or df.empty:
        return None
    return round(float(df.iloc[-1]["close"]), 2)


def calc_drawdown(df):
    if df is None or df.empty:
        return None, None
    latest = float(df.iloc[-1]["close"])
    high52 = float(df["high"].max())
    dd = (latest - high52) / high52 * 100
    return round(latest, 2), round(dd, 2)


def calc_change(df, days=60):
    if df is None or df.empty or len(df) < days:
        return None
    latest = float(df.iloc[-1]["close"])
    past = float(df.iloc[-days]["close"])
    return round((latest - past) / past * 100, 2)


def make_return_series(df, days=60):
    if df is None or df.empty or len(df) < days:
        return pd.DataFrame(columns=["date", "value"])
    temp = df.tail(days).copy()
    start_price = float(temp.iloc[0]["close"])
    temp["value"] = ((temp["close"] / start_price - 1) * 100).round(2)
    return temp[["date", "value"]]


def make_relative_series(df_a, df_b, days=60):
    if df_a is None or df_b is None or df_a.empty or df_b.empty:
        return pd.DataFrame(columns=["date", "value"])

    a = df_a[["date", "close"]].rename(columns={"close": "a_close"})
    b = df_b[["date", "close"]].rename(columns={"close": "b_close"})
    merged = pd.merge(a, b, on="date", how="inner").sort_values("date")

    if len(merged) < days:
        return pd.DataFrame(columns=["date", "value"])

    merged = merged.tail(days)
    a_start = float(merged.iloc[0]["a_close"])
    b_start = float(merged.iloc[0]["b_close"])
    merged["a_return"] = (merged["a_close"] / a_start - 1) * 100
    merged["b_return"] = (merged["b_close"] / b_start - 1) * 100
    merged["value"] = (merged["a_return"] - merged["b_return"]).round(2)
    return merged[["date", "value"]]


def series_current(df):
    if df is None or df.empty:
        return None
    return round(float(df.iloc[-1]["value"]), 2)


def series_min(df):
    if df is None or df.empty:
        return None
    return round(float(df["value"].min()), 2)


def series_max(df):
    if df is None or df.empty:
        return None
    return round(float(df["value"].max()), 2)


def series_change(df, days=20):
    if df is None or df.empty or len(df) < days:
        return None
    return round(float(df.iloc[-1]["value"]) - float(df.iloc[-days]["value"]), 2)


# =========================================================
# 状态和评分
# =========================================================
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


def score_fear(fg):
    if fg is None:
        return None
    if fg < 25:
        return 80
    elif fg < 45:
        return 50
    elif fg < 75:
        return 20
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
    return 90


def score_relative(diff):
    if diff is None:
        return None
    if diff < -5:
        return 70
    elif diff < -2:
        return 45
    return 20


def score_credit(change):
    if change is None:
        return None
    if change < -5:
        return 85
    elif change < -2:
        return 55
    return 15


def score_cross_asset(tlt_change, gld_change):
    if tlt_change is None or gld_change is None:
        return None
    if gld_change > 5 and tlt_change < -3:
        return 75
    elif gld_change > 5 and tlt_change > 3:
        return 65
    elif tlt_change < -5:
        return 55
    elif tlt_change > 5:
        return 25
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
    return "高风险"


# =========================================================
# 图表
# =========================================================
def show_line_chart(df, title, y_title, threshold_lines=None):
    if df is None or df.empty:
        st.warning("暂无足够数据生成图表")
        return

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["value"],
            mode="lines",
            line=dict(color=LINE_COLOR, width=2.5),
            hovertemplate="%{y:.2f}<extra></extra>",
        )
    )

    if threshold_lines:
        for line in threshold_lines:
            fig.add_hline(
                y=line["y"],
                line_dash="dash",
                line_color=THRESHOLD_COLOR,
                line_width=1.4,
                annotation_text=line["text"],
                annotation_font_color="#991b1b",
                annotation_position="top left",
            )

    fig.update_layout(
        title=dict(text=title, font=dict(color="#111827", size=16)),
        yaxis_title=y_title,
        height=360,
        **PLOTLY_LAYOUT,
    )

    st.plotly_chart(fig, use_container_width=True)


def show_fear_greed_gauge(fg):
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=fg,
            title={"text": "Fear & Greed", "font": {"color": "#111827", "size": 15}},
            number={"font": {"color": "#111827", "size": 42}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#6b7280", "tickfont": {"color": "#6b7280"}},
                "bar": {"color": LINE_COLOR, "thickness": 0.25},
                "bgcolor": "#ffffff",
                "bordercolor": "#e5e7eb",
                "steps": [
                    {"range": [0, 25], "color": "#fee2e2"},
                    {"range": [25, 45], "color": "#fef3c7"},
                    {"range": [45, 75], "color": "#dbeafe"},
                    {"range": [75, 100], "color": "#dcfce7"},
                ],
                "threshold": {"line": {"color": THRESHOLD_COLOR, "width": 3}, "value": fg},
            },
        )
    )

    fig.update_layout(
        height=320,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(color="#111827"),
        margin=dict(l=30, r=30, t=50, b=10),
    )

    st.plotly_chart(fig, use_container_width=True)


def show_chart_summary(current, low, high, recent_change, status, unit="%"):
    a, b, c, d = st.columns(4)
    a.metric("当前值", current if current is not None else "获取失败")
    b.metric("区间低点", low if low is not None else "获取失败")
    c.metric("区间高点", high if high is not None else "获取失败")
    d.metric("近20日变化", f"{recent_change}{unit}" if recent_change is not None else "获取失败", status)


def badge_html(text, kind="green"):
    return f'<span class="badge badge-{kind}">{text}</span>'


# =========================================================
# 加载当前数据
# =========================================================
fg, fg_hist_df = get_fear_greed_data()
vix, vix_hist_df = get_vix_data()

spy_df = get_twelve_history("SPY")
qqq_df = get_twelve_history("QQQ")
rsp_df = get_twelve_history("RSP")
iwm_df = get_twelve_history("IWM")
hyg_df = get_twelve_history("HYG")
jnk_df = get_twelve_history("JNK")
tlt_df = get_twelve_history("TLT")
gld_df = get_twelve_history("GLD")

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

emotion_score = average_score([score_fear(fg), score_vix(vix)])
trend_score = average_score([score_drawdown(spy_dd), score_drawdown(qqq_dd)])
breadth_score = average_score([score_relative(rsp_vs_spy), score_relative(iwm_vs_spy)])
credit_score = average_score([score_credit(hyg_change), score_credit(jnk_change)])
cross_asset_score = average_score([score_cross_asset(tlt_change, gld_change)])

risk_score = average_score([emotion_score, trend_score, breadth_score, credit_score, cross_asset_score])

credit_warning = (hyg_change is not None and hyg_change < -5) or (jnk_change is not None and jnk_change < -5)
good_buy_window = vix is not None and fg is not None and vix > 30 and fg < 25 and not credit_warning
fomo_warning = vix is not None and fg is not None and vix <= 15 and fg > 75
breadth_warning = (rsp_vs_spy is not None and rsp_vs_spy < -5) or (iwm_vs_spy is not None and iwm_vs_spy < -5)
normal_pullback = risk_score >= 20 and risk_score < 60 and not credit_warning


if credit_warning:
    buy_grade = "D级风险"
    buy_action = "信用市场恶化，暂停抄底，优先保留现金。"
    scene = "🔴 信用风险升温"
    advice = "当前策略：暂停抄底，优先观察信用市场。\n\nHYG/JNK 同步大跌时，不要急着抄底，先等信用市场稳定。"
elif good_buy_window:
    buy_grade = "A级机会"
    buy_action = "恐慌充分但信用未失控，可以重点分批加仓。"
    scene = "🟠 优质加仓窗口"
    advice = "当前策略：重点关注加仓机会。\n\nVIX 超过30，Fear & Greed 低于25，同时信用市场稳定，是较好的分批加仓窗口。"
elif fomo_warning:
    buy_grade = "E级过热"
    buy_action = "市场过度乐观，不适合追高。"
    scene = "🟣 市场过热"
    advice = "当前策略：谨慎追高。\n\nVIX 极低且情绪过热时，市场不愿意给风险定价。"
elif normal_pullback:
    buy_grade = "B级机会"
    buy_action = "市场出现回调但信用未失控，可以按计划分批加仓。"
    if risk_score < 40:
        scene = "🟡 第一档回调"
        advice = "当前策略：执行第一档加仓。\n\n建议投入预备资金：30%。\n\n累计投入：30%，剩余现金：70%。"
    else:
        scene = "🟠 第二档回调"
        advice = "当前策略：执行第二档加仓。\n\n建议再投入预备资金：30%。\n\n累计投入：60%，剩余现金：40%。"
elif breadth_warning:
    buy_grade = "C级观察"
    buy_action = "上涨广度偏弱，谨慎观察，不盲目追高。"
    scene = "🟡 上涨广度偏弱"
    advice = "当前策略：谨慎观察。\n\nRSP 或 IWM 相对 SPY 明显走弱，说明上涨可能集中在少数权重股上。"
elif risk_score >= 60:
    buy_grade = "B级机会"
    buy_action = "恐慌较高，但仍需确认信用市场是否稳定。"
    scene = "🔴 极端恐慌"
    advice = "当前策略：执行第三档加仓。\n\n建议投入剩余资金：40%。\n\n但前提是 HYG/JNK 没有明显崩盘。"
else:
    buy_grade = "C级观察"
    buy_action = "市场风险较低，继续正常定投，回调资金暂不动用。"
    scene = "🟢 正常市场"
    advice = "当前策略：正常定投。\n\n市场风险较低，按原计划持续定投即可。\n\n回调加仓资金暂不动用。"


# =========================================================
# 页头
# =========================================================
st.markdown("""
<div class="dashboard-header">
    <p class="dashboard-title">📈 市场风险仪表盘</p>
    <p class="dashboard-subtitle">美股回调加仓版 · 情绪 · 波动率 · 市场广度 · 信用风险 · 跨资产联动</p>
</div>
""", unsafe_allow_html=True)

main_tab, backtest_tab, explain_tab = st.tabs(["当前市场", "历史回测", "指标解释"])


# =========================================================
# 当前市场
# =========================================================
with main_tab:
    st.subheader("一、当前结论")

    a, b, c = st.columns(3)
    a.metric("当前市场状态", scene)
    b.metric("当前买入等级", buy_grade)
    c.metric("综合风险评分", f"{risk_score}/100", risk_level(risk_score))

    st.info(buy_action)

    st.markdown("---")
    st.subheader("二、核心指标")

    c1, c2, c3 = st.columns(3)
    c1.metric("恐惧贪婪指数", round(fg, 1), fear_status(fg))
    c2.metric("VIX 恐慌指数", vix if vix is not None else "获取失败", vix_status(vix))
    c3.metric("SPY 标普500回调", f"{spy_dd}%" if spy_dd is not None else "获取失败", drawdown_status(spy_dd))

    c4, c5, c6 = st.columns(3)
    c4.metric("QQQ 纳斯达克100回调", f"{qqq_dd}%" if qqq_dd is not None else "获取失败", drawdown_status(qqq_dd))
    c5.metric("RSP 相对 SPY", f"{rsp_vs_spy}%" if rsp_vs_spy is not None else "获取失败", relative_status(rsp_vs_spy))
    c6.metric("IWM 相对 SPY", f"{iwm_vs_spy}%" if iwm_vs_spy is not None else "获取失败", relative_status(iwm_vs_spy))

    c7, c8, c9 = st.columns(3)
    c7.metric("HYG 近60日", f"{hyg_change}%" if hyg_change is not None else "获取失败", credit_status(hyg_change))
    c8.metric("JNK 近60日", f"{jnk_change}%" if jnk_change is not None else "获取失败", credit_status(jnk_change))
    c9.metric("跨资产状态", cross_asset_status(tlt_change, gld_change))

    st.markdown("---")
    st.subheader("三、风险来源拆解")

    s1, s2, s3, s4, s5 = st.columns(5)
    s1.metric("情绪风险", f"{emotion_score}/100", risk_level(emotion_score))
    s2.metric("趋势风险", f"{trend_score}/100", risk_level(trend_score))
    s3.metric("广度风险", f"{breadth_score}/100", risk_level(breadth_score))
    s4.metric("信用风险", f"{credit_score}/100", risk_level(credit_score))
    s5.metric("跨资产风险", f"{cross_asset_score}/100", risk_level(cross_asset_score))

    risk_source_table = pd.DataFrame({
        "模块": ["情绪层", "趋势层", "市场广度", "信用市场", "跨资产"],
        "代表指标": ["Fear & Greed、VIX", "SPY回调、QQQ回调", "RSP相对SPY、IWM相对SPY", "HYG、JNK", "TLT、GLD"],
        "当前判断": [
            f"{fear_status(fg)} / {vix_status(vix)}",
            f"SPY：{drawdown_status(spy_dd)}，QQQ：{drawdown_status(qqq_dd)}",
            f"RSP：{relative_status(rsp_vs_spy)}，IWM：{relative_status(iwm_vs_spy)}",
            f"HYG：{credit_status(hyg_change)}，JNK：{credit_status(jnk_change)}",
            cross_asset_status(tlt_change, gld_change),
        ],
        "解释": [
            "判断市场是恐惧、贪婪，还是机构正在买保险。",
            "判断指数距离高点有多远，是否已经进入回调区。",
            "判断上涨是否由多数股票推动，还是少数权重股支撑。",
            "判断企业融资环境是否恶化，是否存在系统性风险。",
            "判断利率、黄金和避险情绪是否出现异常联动。",
        ],
    })
    st.dataframe(risk_source_table, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("四、核心指标图表")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        ["Fear & Greed", "VIX", "RSP相对SPY", "IWM相对SPY", "HYG近60日", "JNK近60日"]
    )

    with tab1:
        st.markdown("### Fear & Greed 恐惧贪婪指数")
        show_fear_greed_gauge(fg)
        st.markdown(f"当前值：**{round(fg, 1)}**  当前状态：**{fear_status(fg)}**")
        st.markdown("- 0–25：极度恐惧；25–45：恐惧；45–75：中性；75–100：极度贪婪")
        if not fg_hist_df.empty:
            show_line_chart(
                fg_hist_df,
                "Fear & Greed 历史走势",
                "分数",
                threshold_lines=[
                    {"y": 25, "text": "25：极度恐惧"},
                    {"y": 75, "text": "75：极度贪婪"},
                ],
            )

    with tab2:
        st.markdown("### VIX 恐慌指数")
        show_chart_summary(vix, series_min(vix_hist_df), series_max(vix_hist_df), series_change(vix_hist_df, 20), vix_status(vix), unit="")
        show_line_chart(
            vix_hist_df,
            "VIX 恐慌指数",
            "VIX",
            threshold_lines=[
                {"y": 15, "text": "15：过度乐观"},
                {"y": 30, "text": "30：恐慌区"},
            ],
        )

    with tab3:
        st.markdown("### RSP 相对 SPY")
        cur = series_current(rsp_vs_spy_series)
        show_chart_summary(
            f"{cur}%" if cur is not None else None,
            f"{series_min(rsp_vs_spy_series)}%" if series_min(rsp_vs_spy_series) is not None else None,
            f"{series_max(rsp_vs_spy_series)}%" if series_max(rsp_vs_spy_series) is not None else None,
            series_change(rsp_vs_spy_series, 20),
            relative_status(rsp_vs_spy),
        )
        show_line_chart(
            rsp_vs_spy_series,
            "RSP 相对 SPY",
            "相对表现 %",
            threshold_lines=[
                {"y": 0, "text": "0：持平"},
                {"y": -5, "text": "-5：广度明显偏弱"},
            ],
        )
        st.caption("蓝线代表 RSP 近60日涨跌幅减去 SPY 近60日涨跌幅，不是 RSP 或 SPY 的价格线。")

    with tab4:
        st.markdown("### IWM 相对 SPY")
        cur = series_current(iwm_vs_spy_series)
        show_chart_summary(
            f"{cur}%" if cur is not None else None,
            f"{series_min(iwm_vs_spy_series)}%" if series_min(iwm_vs_spy_series) is not None else None,
            f"{series_max(iwm_vs_spy_series)}%" if series_max(iwm_vs_spy_series) is not None else None,
            series_change(iwm_vs_spy_series, 20),
            relative_status(iwm_vs_spy),
        )
        show_line_chart(
            iwm_vs_spy_series,
            "IWM 相对 SPY",
            "相对表现 %",
            threshold_lines=[
                {"y": 0, "text": "0：小盘与大盘持平"},
                {"y": -5, "text": "-5：小盘明显跑输"},
            ],
        )
        st.caption("蓝线代表 IWM 近60日涨跌幅减去 SPY 近60日涨跌幅；高于0说明小盘股跑赢大盘。")

    with tab5:
        st.markdown("### HYG 近60日")
        cur = series_current(hyg_series)
        show_chart_summary(
            f"{cur}%" if cur is not None else None,
            f"{series_min(hyg_series)}%" if series_min(hyg_series) is not None else None,
            f"{series_max(hyg_series)}%" if series_max(hyg_series) is not None else None,
            series_change(hyg_series, 20),
            credit_status(hyg_change),
        )
        show_line_chart(
            hyg_series,
            "HYG 近60日变化",
            "涨跌幅 %",
            threshold_lines=[
                {"y": 0, "text": "0：持平"},
                {"y": -5, "text": "-5：信用风险升温"},
            ],
        )

    with tab6:
        st.markdown("### JNK 近60日")
        cur = series_current(jnk_series)
        show_chart_summary(
            f"{cur}%" if cur is not None else None,
            f"{series_min(jnk_series)}%" if series_min(jnk_series) is not None else None,
            f"{series_max(jnk_series)}%" if series_max(jnk_series) is not None else None,
            series_change(jnk_series, 20),
            credit_status(jnk_change),
        )
        show_line_chart(
            jnk_series,
            "JNK 近60日变化",
            "涨跌幅 %",
            threshold_lines=[
                {"y": 0, "text": "0：持平"},
                {"y": -5, "text": "-5：信用风险升温"},
            ],
        )


# =========================================================
# 历史回测
# =========================================================
with backtest_tab:
    st.subheader("历史回测")
    st.caption("选择历史交易日，查看该日风险评分与加仓等级。历史 Fear & Greed 免费接口无法稳定还原，因此历史情绪层主要使用 VIX。")

    query_date = st.date_input(
        "选择查询日期",
        value=pd.Timestamp.today() - pd.Timedelta(days=1),
        min_value=pd.Timestamp("2018-01-01"),
        max_value=pd.Timestamp.today() - pd.Timedelta(days=1),
        format="YYYY/MM/DD",
    )

    @st.cache_data(ttl=86400)
    def get_history_range(symbol, start, end):
        try:
            hist = yf.Ticker(symbol).history(start=start, end=end)
            if hist is None or hist.empty:
                return None
            hist = hist.reset_index()
            date_col = "Date" if "Date" in hist.columns else hist.columns[0]
            hist["date"] = pd.to_datetime(hist[date_col]).dt.tz_localize(None)
            hist["close"] = hist["Close"].astype(float)
            hist["high"] = hist["High"].astype(float)
            return hist[["date", "close", "high"]].sort_values("date")
        except Exception:
            return None

    if st.button("开始回测"):
        with st.spinner("正在计算历史数据…"):
            end = (pd.Timestamp(query_date) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
            start = (pd.Timestamp(query_date) - pd.Timedelta(days=430)).strftime("%Y-%m-%d")

            h_spy = get_history_range("SPY", start, end)
            h_qqq = get_history_range("QQQ", start, end)
            h_rsp = get_history_range("RSP", start, end)
            h_iwm = get_history_range("IWM", start, end)
            h_hyg = get_history_range("HYG", start, end)
            h_jnk = get_history_range("JNK", start, end)
            h_tlt = get_history_range("TLT", start, end)
            h_gld = get_history_range("GLD", start, end)
            h_vix = get_history_range("^VIX", start, end)

            def up_to(df, d):
                if df is None or df.empty:
                    return None
                x = df[df["date"] <= pd.Timestamp(d)]
                return x if not x.empty else None

            h_spy_q = up_to(h_spy, query_date)
            h_qqq_q = up_to(h_qqq, query_date)
            h_rsp_q = up_to(h_rsp, query_date)
            h_iwm_q = up_to(h_iwm, query_date)
            h_hyg_q = up_to(h_hyg, query_date)
            h_jnk_q = up_to(h_jnk, query_date)
            h_tlt_q = up_to(h_tlt, query_date)
            h_gld_q = up_to(h_gld, query_date)
            h_vix_q = up_to(h_vix, query_date)

            q_vix = latest_price(h_vix_q)
            _, q_spy_dd = calc_drawdown(h_spy_q)
            _, q_qqq_dd = calc_drawdown(h_qqq_q)

            q_spy_change = calc_change(h_spy_q, 60)
            q_rsp_change = calc_change(h_rsp_q, 60)
            q_iwm_change = calc_change(h_iwm_q, 60)
            q_hyg_change = calc_change(h_hyg_q, 60)
            q_jnk_change = calc_change(h_jnk_q, 60)
            q_tlt_change = calc_change(h_tlt_q, 60)
            q_gld_change = calc_change(h_gld_q, 60)

            q_rsp_vs_spy = round(q_rsp_change - q_spy_change, 2) if q_rsp_change is not None and q_spy_change is not None else None
            q_iwm_vs_spy = round(q_iwm_change - q_spy_change, 2) if q_iwm_change is not None and q_spy_change is not None else None

            q_emotion = average_score([score_vix(q_vix)])
            q_trend = average_score([score_drawdown(q_spy_dd), score_drawdown(q_qqq_dd)])
            q_breadth = average_score([score_relative(q_rsp_vs_spy), score_relative(q_iwm_vs_spy)])
            q_credit = average_score([score_credit(q_hyg_change), score_credit(q_jnk_change)])
            q_cross = average_score([score_cross_asset(q_tlt_change, q_gld_change)])
            q_risk = average_score([q_emotion, q_trend, q_breadth, q_credit, q_cross])

            q_credit_warning = (q_hyg_change is not None and q_hyg_change < -5) or (q_jnk_change is not None and q_jnk_change < -5)
            if q_credit_warning:
                q_grade, q_scene, q_action = "D级风险", "🔴 信用风险升温", "暂停抄底，保留现金。"
            elif q_vix is not None and q_vix > 30 and not q_credit_warning:
                q_grade, q_scene, q_action = "A级机会", "🟠 优质加仓窗口", "VIX超过30且信用稳定，可以重点分批加仓。"
            elif 20 <= q_risk < 60 and not q_credit_warning:
                q_grade, q_scene, q_action = "B级机会", "🟡/🟠 回调区", "市场回调但信用未失控，可以按计划分批加仓。"
            elif q_risk >= 60:
                q_grade, q_scene, q_action = "B级机会", "🔴 极端恐慌", "恐慌较高，但需确认信用市场是否稳定。"
            else:
                q_grade, q_scene, q_action = "C级观察", "🟢 正常市场", "正常定投，回调资金暂不动用。"

            st.markdown("### 回测结果")

            r1, r2, r3 = st.columns(3)
            r1.metric("市场状态", q_scene)
            r2.metric("买入等级", q_grade)
            r3.metric("综合风险评分", f"{q_risk}/100", risk_level(q_risk))

            st.info(q_action)

            rr = pd.DataFrame({
                "指标": ["VIX", "SPY回调", "QQQ回调", "RSP相对SPY", "IWM相对SPY", "HYG近60日", "JNK近60日"],
                "数值": [
                    q_vix,
                    f"{q_spy_dd}%" if q_spy_dd is not None else "N/A",
                    f"{q_qqq_dd}%" if q_qqq_dd is not None else "N/A",
                    f"{q_rsp_vs_spy}%" if q_rsp_vs_spy is not None else "N/A",
                    f"{q_iwm_vs_spy}%" if q_iwm_vs_spy is not None else "N/A",
                    f"{q_hyg_change}%" if q_hyg_change is not None else "N/A",
                    f"{q_jnk_change}%" if q_jnk_change is not None else "N/A",
                ],
                "状态": [
                    vix_status(q_vix),
                    drawdown_status(q_spy_dd),
                    drawdown_status(q_qqq_dd),
                    relative_status(q_rsp_vs_spy),
                    relative_status(q_iwm_vs_spy),
                    credit_status(q_hyg_change),
                    credit_status(q_jnk_change),
                ]
            })
            st.dataframe(rr, use_container_width=True, hide_index=True)


# =========================================================
# 指标解释
# =========================================================
with explain_tab:
    st.subheader("指标解释")

    meaning_table = pd.DataFrame({
        "指标": ["Fear & Greed", "VIX", "RSP相对SPY", "IWM相对SPY", "HYG近60日", "JNK近60日", "TLT近60日", "GLD近60日"],
        "代表含义": [
            "CNN综合情绪指数，0到100，越低越恐惧，越高越贪婪。",
            "期权市场的保险费，越高说明机构越愿意为风险付费。",
            "等权标普500相对市值加权标普500，判断上涨是否集中于少数权重股。",
            "小盘股相对大盘股，判断资金是否扩散到更广泛的股票。",
            "高收益债ETF表现，观察信用市场是否承压。",
            "另一只高收益债ETF，用于和HYG交叉验证。",
            "长期美债ETF，通常与长期利率反向，反映利率压力。",
            "黄金ETF，反映避险需求、通胀担忧或货币信用担忧。",
        ],
        "交易含义": [
            "低于25常见于恐慌区，高于75说明FOMO较强。",
            "VIX超过30且信用稳定，常是较好的加仓观察窗口。",
            "RSP跑输SPY说明指数可能由少数巨头支撑，不宜盲目追高。",
            "IWM跑赢SPY说明资金扩散，小盘股参与上涨，市场广度改善。",
            "股市跌但HYG稳定，多数是估值调整；HYG大跌要警惕信用风险。",
            "JNK和HYG同步大跌，信用压力更可信，不宜急着抄底。",
            "美股跌且TLT跌，可能是利率上行压制估值，科技股压力较大。",
            "GLD涨要结合TLT看，黄金涨且TLT跌可能是通胀或货币信用压力。",
        ],
    })

    st.dataframe(meaning_table, use_container_width=True, hide_index=True)

    st.markdown("### 加仓规则")
    plan = pd.DataFrame({
        "等级": ["A级机会", "B级机会", "C级观察", "D级风险", "E级过热"],
        "典型条件": [
            "VIX > 30，Fear & Greed < 25，信用市场稳定",
            "市场出现回调，信用市场没有失控",
            "情绪中性，指数接近高位，风险不高",
            "HYG/JNK同步大跌，信用市场恶化",
            "Fear & Greed > 75，VIX <= 15，市场FOMO",
        ],
        "动作": ["重点分批加仓", "按计划分批加仓", "正常定投", "暂停抄底", "避免追高"],
        "预备资金使用": ["可投入30%~60%", "第一档30%，第二档再30%", "0%", "0%", "0%，必要时减仓"],
    })

    st.dataframe(plan, use_container_width=True, hide_index=True)

st.markdown("---")
st.caption(f"更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
