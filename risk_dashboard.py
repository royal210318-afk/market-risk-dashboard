import math
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
import yfinance as yf


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
# 明亮专业版样式 (修改了头部的高度和排版)
# =========================================================
st.markdown("""
<style>
.stApp {
    background:
        radial-gradient(circle at top left, rgba(37, 99, 235, 0.10), transparent 32%),
        radial-gradient(circle at top right, rgba(249, 115, 22, 0.10), transparent 30%),
        linear-gradient(180deg, #f8fafc 0%, #ffffff 35%, #ffffff 100%);
    color: #111827;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
}

.block-container {
    padding-top: 1.2rem;
    padding-bottom: 3rem;
    max-width: 1220px;
}

/* 顶部 Hero 专业版 - 高度变窄 */
.hero {
    position: relative;
    overflow: hidden;
    background:
        linear-gradient(135deg, rgba(15, 23, 42, 0.96) 0%, rgba(30, 64, 175, 0.92) 52%, rgba(194, 65, 12, 0.90) 100%);
    border: 1px solid rgba(255,255,255,0.26);
    border-radius: 20px;
    padding: 1.25rem 1.8rem;
    margin: 0.3rem 0 1.5rem 0;
    box-shadow: 0 12px 30px rgba(15, 23, 42, 0.15);
}

.hero:before {
    content: "";
    position: absolute;
    width: 300px;
    height: 300px;
    right: -50px;
    top: -150px;
    border-radius: 999px;
    background: rgba(255,255,255,0.08);
}

.hero-top {
    position: relative;
    z-index: 2;
    display: flex;
    justify-content: space-between;
    align-items: center; /* 垂直居中对齐 */
    gap: 1.5rem;
    flex-wrap: wrap; /* 屏幕过小自动折行 */
}

.hero-left {
    flex: 1;
    min-width: 300px;
}

.hero-pill {
    display: inline-block;
    background: rgba(255,255,255,0.14);
    color: #dbeafe;
    border: 1px solid rgba(255,255,255,0.24);
    border-radius: 999px;
    padding: 0.25rem 0.65rem;
    font-size: 0.75rem;
    font-weight: 850;
    letter-spacing: 0.3px;
    margin-bottom: 0.5rem;
}

.hero-title {
    font-size: 2.1rem;
    line-height: 1.1;
    font-weight: 950;
    color: #ffffff;
    margin: 0;
    letter-spacing: -1px;
}

.hero-title-cn {
    font-size: 1.1rem;
    line-height: 1.35;
    font-weight: 850;
    color: #e0f2fe;
    margin-top: 0.3rem;
}

.hero-subtitle {
    font-size: 0.9rem;
    color: #93c5fd;
    margin-top: 0.4rem;
    line-height: 1.5;
}

/* 右侧卡片区域：横向排列 */
.hero-cards {
    display: flex;
    gap: 0.75rem;
    align-items: stretch;
    flex-shrink: 0;
}

.hero-card {
    background: rgba(255,255,255,0.14);
    border: 1px solid rgba(255,255,255,0.22);
    backdrop-filter: blur(8px);
    border-radius: 16px;
    padding: 0.8rem 1rem;
    min-width: 130px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.hero-card-label {
    color: #dbeafe;
    font-size: 0.78rem;
    font-weight: 800;
    margin-bottom: 0.2rem;
}

.hero-card-value {
    color: #ffffff;
    font-size: 1.4rem;
    font-weight: 950;
    letter-spacing: -0.4px;
}

/* 页面组件 */
h1, h2, h3 {
    color: #111827 !important;
    font-weight: 850 !important;
}

[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 18px;
    padding: 1.05rem 1.12rem;
    box-shadow: 0 8px 22px rgba(17, 24, 39, 0.06);
}

[data-testid="stMetricLabel"] {
    color: #4b5563 !important;
    font-size: 0.84rem !important;
    font-weight: 750 !important;
}

[data-testid="stMetricValue"] {
    color: #111827 !important;
    font-size: 1.78rem !important;
    font-weight: 900 !important;
}

[data-testid="stMetricDelta"] {
    font-size: 0.8rem !important;
    font-weight: 750 !important;
}

.stAlert {
    border-radius: 16px !important;
    border: 1px solid #bfdbfe !important;
    background: #eff6ff !important;
    color: #1e3a8a !important;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 0.45rem;
    border-bottom: 1px solid #e5e7eb;
}

.stTabs [data-baseweb="tab"] {
    color: #374151 !important;
    font-weight: 750 !important;
    padding: 0.78rem 1.05rem !important;
}

.stTabs [aria-selected="true"] {
    color: #dc2626 !important;
    border-bottom: 3px solid #ef4444 !important;
}

.stDataFrame {
    border: 1px solid #e5e7eb !important;
    border-radius: 16px !important;
    overflow: hidden;
}

hr {
    border-color: #e5e7eb !important;
    margin: 2rem 0 !important;
}

.big-action {
    background: #ffffff;
    border: 1px solid #dbeafe;
    border-left: 6px solid #2563eb;
    border-radius: 20px;
    padding: 1.25rem 1.35rem;
    margin: 0.9rem 0 1rem 0;
    box-shadow: 0 10px 26px rgba(37, 99, 235, 0.08);
}

.big-action-title {
    font-size: 1.2rem;
    font-weight: 900;
    color: #111827;
    margin-bottom: 0.55rem;
}

.big-action-body {
    font-size: 1rem;
    color: #374151;
    line-height: 1.75;
}

.mini-note {
    color: #64748b;
    font-size: 0.9rem;
    line-height: 1.65;
}

.signal-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.95rem;
    margin-top: 0.5rem;
}

.signal-card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 18px;
    padding: 1.05rem 1.1rem;
    box-shadow: 0 8px 22px rgba(17, 24, 39, 0.06);
    min-height: 168px;
}

.signal-title {
    color: #4b5563;
    font-size: 0.86rem;
    font-weight: 850;
    margin-bottom: 0.5rem;
}

.signal-value {
    color: #111827;
    font-size: 1.9rem;
    line-height: 1.1;
    font-weight: 950;
    letter-spacing: -0.6px;
    margin-bottom: 0.72rem;
}

.signal-status {
    display: inline-block;
    border-radius: 999px;
    padding: 0.22rem 0.62rem;
    font-size: 0.78rem;
    font-weight: 850;
    margin-bottom: 0.62rem;
}

.signal-desc {
    color: #4b5563;
    font-size: 0.86rem;
    line-height: 1.65;
}

.status-green {
    background: #dcfce7;
    color: #166534;
}

.status-blue {
    background: #dbeafe;
    color: #1e40af;
}

.status-yellow {
    background: #fef9c3;
    color: #854d0e;
}

.status-orange {
    background: #ffedd5;
    color: #9a3412;
}

.status-red {
    background: #fee2e2;
    color: #991b1b;
}

.status-gray {
    background: #f3f4f6;
    color: #4b5563;
}

@media (max-width: 900px) {
    .signal-grid {
        grid-template-columns: 1fr;
    }
}

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
@st.cache_data(ttl=600)
def get_fear_greed_data():
    """获取 CNN Fear & Greed 实时数据；失败返回 None，不用 50 冒充实时数据。"""
    url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json,text/plain,*/*",
            "Referer": "https://edition.cnn.com/markets/fear-and-greed",
        }
        r = requests.get(url, headers=headers, timeout=20)
        r.raise_for_status()
        data = r.json()

        fg_data = data.get("fear_and_greed", {})
        score = fg_data.get("score")

        if score is None:
            return None, pd.DataFrame(columns=["date", "value"])

        score = round(float(score), 1)

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
        return None, pd.DataFrame(columns=["date", "value"])


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


def up_to_date(df, d):
    if df is None or df.empty:
        return None
    x = df[df["date"] <= pd.Timestamp(d)]
    return x if not x.empty else None


def value_on_or_after(df, d):
    if df is None or df.empty:
        return None
    x = df[df["date"] >= pd.Timestamp(d)]
    if x.empty:
        return None
    return float(x.iloc[0]["close"])


def future_return(df, d, days):
    base_df = up_to_date(df, d)
    if base_df is None or base_df.empty:
        return None
    base = float(base_df.iloc[-1]["close"])
    future = value_on_or_after(df, pd.Timestamp(d) + pd.Timedelta(days=days))
    if base == 0 or future is None:
        return None
    return round((future - base) / base * 100, 2)


# =========================================================
# 状态与评分
# =========================================================
def fear_status(fg):
    if fg is None:
        return "获取失败"
    if fg < 25:
        return "极度恐惧"
    elif fg < 45:
        return "恐惧"
    elif fg < 75:
        return "中性"
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
    return "跨资产中性"



# =========================================================
# 状态说明文案
# =========================================================
BREADTH_EXPLANATIONS = {
    "广度正常": "市场普涨或回调正常，广度无异常。",
    "广度较差": "弱势股领跌或只有少数个股支撑，警惕风险。",
    "广度偏弱": "上涨动力减弱，资金参与度下降，建议保持审慎。",
    "广度较好": "资金扩散至中小盘，市场参与度高，利于多头。",
    "获取失败": "无法获取市场广度数据，请检查数据源。"
}

CREDIT_EXPLANATIONS = {
    "信用稳定": "垃圾债走势平稳，市场风险偏好正常，可持有风险资产。",
    "信用风险升温": "HYG/JNK 出现明显抛售，信用利差可能扩大，需降低高风险仓位。",
    "信用稳定偏强": "垃圾债反弹，信用风险溢价收窄，市场环境开始回暖。",
    "信用偏弱": "HYG/JNK 下跌趋势明显，需警惕流动性压力。",
    "获取失败": "无法获取信用市场数据，请检查数据源。"
}

CROSS_ASSET_EXPLANATIONS = {
    "跨资产中性": "宏观环境平稳，无显著压力，建议按原定投计划执行。",
    "通胀或货币信用压力": "黄金涨债跌，通胀忧虑升温，建议减仓高估值资产。",
    "避险或衰退担忧": "金债同涨，市场避险情绪浓，建议降低整体仓位。",
    "利率压力偏大": "长期美债大跌，利率上行抑制估值，建议检查杠杆。",
    "利率压力缓和": "长期美债大涨，融资环境改善，对成长股有利。",
    "获取失败": "无法获取宏观数据，请检查网络连接。"
}


def explanation_text(status, mapping):
    return mapping.get(status, "暂无说明。")


def status_class(status):
    green_status = [
        "极度恐惧", "广度较好", "信用稳定", "信用稳定偏强",
        "利率压力缓和"
    ]
    blue_status = [
        "中性", "广度正常", "跨资产中性", "低波动", "接近高位"
    ]
    yellow_status = [
        "恐惧", "风险升温", "轻度回调", "广度偏弱", "信用偏弱",
        "避险或衰退担忧"
    ]
    orange_status = [
        "极度贪婪", "明显回调", "通胀或货币信用压力", "利率压力偏大",
        "过度乐观"
    ]
    red_status = [
        "恐慌区", "深度回调", "广度较差", "信用风险升温", "获取失败"
    ]

    if status in green_status:
        return "status-green"
    if status in blue_status:
        return "status-blue"
    if status in yellow_status:
        return "status-yellow"
    if status in orange_status:
        return "status-orange"
    if status in red_status:
        return "status-red"
    return "status-gray"


def signal_card(title, value, status, desc):
    safe_value = value if value is not None else "获取失败"
    safe_status = status if status is not None else "获取失败"
    safe_desc = desc if desc else "暂无说明。"
    color = status_class(safe_status)

    return f"""
    <div class="signal-card">
        <div class="signal-title">{title}</div>
        <div class="signal-value">{safe_value}</div>
        <div class="signal-status {color}">{safe_status}</div>
        <div class="signal-desc">{safe_desc}</div>
    </div>
    """


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


def weighted_risk_score(emotion, trend, breadth, credit, cross_asset):
    return round(
        emotion * 0.30
        + trend * 0.20
        + breadth * 0.20
        + credit * 0.20
        + cross_asset * 0.10
    )


def risk_level(score):
    if score < 20:
        return "低风险"
    elif score < 40:
        return "轻度回调"
    elif score < 60:
        return "中等风险"
    return "高风险"


def decide_action(risk_score, fg, vix, hyg_change, jnk_change, rsp_vs_spy, iwm_vs_spy):
    """
    操作动作只保留六类：
    避免追高、暂停抄底、正常定投、加仓30%、再加仓30%、加仓剩余40%。
    """
    credit_warning = (
        (hyg_change is not None and hyg_change < -5)
        or (jnk_change is not None and jnk_change < -5)
    )

    fomo_warning = (
        vix is not None
        and fg is not None
        and vix <= 15
        and fg > 75
    )

    if credit_warning:
        return (
            "暂停抄底",
            "🔴 信用风险升温",
            "暂停抄底：不加仓，现金为主",
            "HYG/JNK 同步明显下跌，说明信用市场承压。此时不是普通估值回调，不要急着抄底，先等信用市场稳定。"
        )

    if fomo_warning:
        return (
            "避免追高",
            "🟣 市场过热",
            "避免追高：不加仓",
            "Fear & Greed 高于75，同时 VIX 低于或接近15，说明市场FOMO情绪较强，不适合继续大幅加仓。"
        )

    if risk_score < 20:
        return (
            "正常定投",
            "🟢 正常市场",
            "正常定投：不动用回调资金",
            "市场风险较低，按原计划持续定投即可。回调加仓资金暂不动用。"
        )

    if risk_score < 40:
        return (
            "加仓30%",
            "🟡 第一档回调",
            "第一档加仓：投入预备资金30%",
            "市场进入第一档回调区间，且信用市场未失控。建议投入预备资金的30%。累计投入30%，剩余现金70%。"
        )

    if risk_score < 60:
        return (
            "再加仓30%",
            "🟠 第二档回调",
            "第二档加仓：再投入预备资金30%",
            "市场进入第二档回调区间，且信用市场未失控。建议再投入预备资金的30%。累计投入60%，剩余现金40%。"
        )

    return (
        "加仓剩余40%",
        "🔴 第三档回调",
        "第三档加仓：投入剩余40%",
        "市场进入第三档回调区间。若 HYG/JNK 没有明显崩盘，建议投入剩余40%。累计投入100%，剩余现金0%。"
    )


def opportunity_stars(risk_score, vix, hyg_change, jnk_change):
    credit_bad = (
        (hyg_change is not None and hyg_change < -5)
        or (jnk_change is not None and jnk_change < -5)
    )

    if credit_bad:
        return "★★☆☆☆"

    if risk_score >= 75 and vix is not None and vix >= 30:
        return "★★★★★"
    elif risk_score >= 60:
        return "★★★★☆"
    elif risk_score >= 40:
        return "★★★☆☆"
    elif risk_score >= 20:
        return "★★☆☆☆"
    return "★☆☆☆☆"


# =========================================================
# 图表函数
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
    if fg is None:
        st.warning("Fear & Greed 实时数据获取失败")
        return

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


# =========================================================
# 当前数据
# =========================================================
fg_auto, fg_hist_df = get_fear_greed_data()

with st.sidebar:
    st.markdown("### Fear & Greed")
    st.markdown("[打开 CNN Fear & Greed](https://edition.cnn.com/markets/fear-and-greed)")
    st.markdown("[打开 MacroMicro 备用页](https://sc.macromicro.me/series/22748/cnn-fear-and-greed)")

    use_manual_fg = st.checkbox(
        "手动输入 Fear & Greed",
        value=(fg_auto is None)
    )

    manual_fg = st.number_input(
        "Fear & Greed 数值",
        min_value=0.0,
        max_value=100.0,
        value=50.0 if fg_auto is None else float(fg_auto),
        step=1.0
    )

if use_manual_fg:
    fg = round(float(manual_fg), 1)
    fg_source = "手动输入"
else:
    fg = fg_auto
    fg_source = "自动获取" if fg_auto is not None else "获取失败"

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

risk_score = weighted_risk_score(emotion_score, trend_score, breadth_score, credit_score, cross_asset_score)

buy_grade, scene, action_title, advice = decide_action(
    risk_score, fg, vix, hyg_change, jnk_change, rsp_vs_spy, iwm_vs_spy
)


# =========================================================
# 历史评分/排行榜/相似度
# =========================================================
def score_one_day(target_date, dfs):
    h_spy_q = up_to_date(dfs["SPY"], target_date)
    h_qqq_q = up_to_date(dfs["QQQ"], target_date)
    h_rsp_q = up_to_date(dfs["RSP"], target_date)
    h_iwm_q = up_to_date(dfs["IWM"], target_date)
    h_hyg_q = up_to_date(dfs["HYG"], target_date)
    h_jnk_q = up_to_date(dfs["JNK"], target_date)
    h_tlt_q = up_to_date(dfs["TLT"], target_date)
    h_gld_q = up_to_date(dfs["GLD"], target_date)
    h_vix_q = up_to_date(dfs["^VIX"], target_date)

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
    q_risk = weighted_risk_score(q_emotion, q_trend, q_breadth, q_credit, q_cross)

    q_grade, q_scene, q_action_title, q_action = decide_action(
        q_risk, None, q_vix, q_hyg_change, q_jnk_change, q_rsp_vs_spy, q_iwm_vs_spy
    )

    spy_30 = future_return(dfs["SPY"], target_date, 30)
    spy_60 = future_return(dfs["SPY"], target_date, 60)
    spy_120 = future_return(dfs["SPY"], target_date, 120)

    qqq_30 = future_return(dfs["QQQ"], target_date, 30)
    qqq_60 = future_return(dfs["QQQ"], target_date, 60)
    qqq_120 = future_return(dfs["QQQ"], target_date, 120)

    return {
        "日期": pd.Timestamp(target_date).strftime("%Y-%m-%d"),
        "风险评分": q_risk,
        "操作动作": q_grade,
        "市场状态": q_scene,
        "机会质量": opportunity_stars(q_risk, q_vix, q_hyg_change, q_jnk_change),
        "SPY回撤": q_spy_dd,
        "QQQ回撤": q_qqq_dd,
        "VIX": q_vix,
        "RSP相对SPY": q_rsp_vs_spy,
        "IWM相对SPY": q_iwm_vs_spy,
        "HYG近60日": q_hyg_change,
        "JNK近60日": q_jnk_change,
        "SPY30天后": spy_30,
        "SPY60天后": spy_60,
        "SPY120天后": spy_120,
        "QQQ30天后": qqq_30,
        "QQQ60天后": qqq_60,
        "QQQ120天后": qqq_120,
    }


@st.cache_data(ttl=86400)
def build_history_table(start_date, end_date):
    start_ts = pd.Timestamp(start_date)
    end_ts = pd.Timestamp(end_date)
    fetch_start = (start_ts - pd.Timedelta(days=430)).strftime("%Y-%m-%d")
    fetch_end = min(pd.Timestamp.today(), end_ts + pd.Timedelta(days=150)).strftime("%Y-%m-%d")

    symbols = ["SPY", "QQQ", "RSP", "IWM", "HYG", "JNK", "TLT", "GLD", "^VIX"]
    dfs = {s: get_history_range(s, fetch_start, fetch_end) for s in symbols}

    if dfs["SPY"] is None or dfs["SPY"].empty:
        return pd.DataFrame()

    trading_days = dfs["SPY"][
        (dfs["SPY"]["date"] >= start_ts) &
        (dfs["SPY"]["date"] <= end_ts)
    ]["date"].tolist()

    rows = []
    for d in trading_days:
        try:
            rows.append(score_one_day(d, dfs))
        except Exception:
            continue

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows)


def format_percent_value(x):
    if x is None or pd.isna(x):
        return "N/A"
    return f"{round(float(x), 2)}%"


def add_similarity_columns(df):
    if df is None or df.empty:
        return df

    current_vector = {
        "风险评分": risk_score,
        "VIX": vix,
        "SPY回撤": spy_dd,
        "QQQ回撤": qqq_dd,
        "RSP相对SPY": rsp_vs_spy,
        "IWM相对SPY": iwm_vs_spy,
        "HYG近60日": hyg_change,
        "JNK近60日": jnk_change,
    }

    # 每个指标的大致尺度，避免 VIX 和回撤的单位影响过大
    scales = {
        "风险评分": 100,
        "VIX": 40,
        "SPY回撤": 30,
        "QQQ回撤": 40,
        "RSP相对SPY": 20,
        "IWM相对SPY": 25,
        "HYG近60日": 10,
        "JNK近60日": 10,
    }

    similarities = []

    for _, row in df.iterrows():
        dist_sq = 0
        count = 0

        for k, scale in scales.items():
            cur = current_vector.get(k)
            hist = row.get(k)

            if cur is None or pd.isna(cur) or hist is None or pd.isna(hist):
                continue

            dist_sq += ((float(cur) - float(hist)) / scale) ** 2
            count += 1

        if count == 0:
            similarities.append(None)
        else:
            dist = math.sqrt(dist_sq / count)
            similarity = max(0, min(100, round((1 - dist) * 100, 1)))
            similarities.append(similarity)

    out = df.copy()
    out["与今日相似度"] = similarities
    return out


# =========================================================
# 页头
# =========================================================
st.markdown(f"""
<div class="hero">
  <div class="hero-top">
    <div class="hero-left">
      <span class="hero-pill">Market Risk Dashboard</span>
      <p class="hero-title">📈 市场风险仪表盘</p>
      <div class="hero-title-cn">美股回调加仓决策系统</div>
      <p class="hero-subtitle">情绪 30% · 趋势 20% · 广度 20% · 信用 20% · 跨资产 10%</p>
    </div>
    <div class="hero-cards">
      <div class="hero-card">
        <div class="hero-card-label">当前操作</div>
        <div class="hero-card-value">{buy_grade}</div>
      </div>
      <div class="hero-card">
        <div class="hero-card-label">综合风险</div>
        <div class="hero-card-value">{risk_score}/100</div>
      </div>
      <div class="hero-card">
        <div class="hero-card-label">市场状态</div>
        <div class="hero-card-value" style="font-size:1.15rem;">{scene}</div>
      </div>
    </div>
  </div>
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
    b.metric("操作动作", buy_grade)
    c.metric("综合风险评分", f"{risk_score}/100", risk_level(risk_score))

    st.markdown(
        f"""
<div class="big-action">
  <div class="big-action-title">{action_title}</div>
  <div class="big-action-body">{advice}</div>
</div>
""",
        unsafe_allow_html=True
    )

    st.markdown("---")
    st.subheader("二、核心指标")

    fg_status = fear_status(fg)
    vix_state = vix_status(vix)
    spy_status = drawdown_status(spy_dd)
    qqq_status = drawdown_status(qqq_dd)
    rsp_status = relative_status(rsp_vs_spy)
    iwm_status = relative_status(iwm_vs_spy)
    hyg_status = credit_status(hyg_change)
    jnk_status = credit_status(jnk_change)
    macro_status = cross_asset_status(tlt_change, gld_change)

    fg_desc_map = {
        "极度恐惧": "市场情绪极度悲观，若信用市场稳定，可能出现加仓窗口。",
        "恐惧": "市场情绪偏谨慎，适合观察是否进入回调加仓区。",
        "中性": "市场情绪没有明显极端信号，按模型综合评分执行。",
        "极度贪婪": "市场情绪偏FOMO，警惕追高风险。",
        "获取失败": "无法自动获取数据，可在左侧边栏手动输入。"
    }

    vix_desc_map = {
        "过度乐观": "期权市场风险定价偏低，需警惕市场过度乐观。",
        "低波动": "波动率处于低位，市场短期风险偏好较平稳。",
        "风险升温": "波动率上升，机构开始提高风险保险价格。",
        "恐慌区": "VIX进入恐慌区，若信用市场稳定，可能是重要加仓观察窗口。",
        "获取失败": "无法获取VIX数据，请检查数据源。"
    }

    drawdown_desc_map = {
        "接近高位": "指数距离52周高点较近，尚未形成明显回调。",
        "轻度回调": "指数出现小幅回撤，属于第一档观察区。",
        "明显回调": "指数回撤加深，需结合信用市场判断是否加仓。",
        "深度回调": "指数大幅回撤，若信用未失控，可能进入高性价比区域。",
        "获取失败": "无法获取指数回撤数据。"
    }

    signal_html = """
    <div class="signal-grid">
    """
    signal_html += signal_card(
        "恐惧贪婪指数",
        round(fg, 1) if fg is not None else "获取失败",
        fg_status,
        fg_desc_map.get(fg_status, "暂无说明。")
    )
    signal_html += signal_card(
        "VIX 恐慌指数",
        vix if vix is not None else "获取失败",
        vix_state,
        vix_desc_map.get(vix_state, "暂无说明。")
    )
    signal_html += signal_card(
        "SPY 标普500回调",
        f"{spy_dd}%" if spy_dd is not None else "获取失败",
        spy_status,
        drawdown_desc_map.get(spy_status, "暂无说明。")
    )
    signal_html += signal_card(
        "QQQ 纳斯达克100回调",
        f"{qqq_dd}%" if qqq_dd is not None else "获取失败",
        qqq_status,
        drawdown_desc_map.get(qqq_status, "暂无说明。")
    )
    signal_html += signal_card(
        "RSP 相对 SPY",
        f"{rsp_vs_spy}%" if rsp_vs_spy is not None else "获取失败",
        rsp_status,
        explanation_text(rsp_status, BREADTH_EXPLANATIONS)
    )
    signal_html += signal_card(
        "IWM 相对 SPY",
        f"{iwm_vs_spy}%" if iwm_vs_spy is not None else "获取失败",
        iwm_status,
        explanation_text(iwm_status, BREADTH_EXPLANATIONS)
    )
    signal_html += signal_card(
        "HYG 近60日",
        f"{hyg_change}%" if hyg_change is not None else "获取失败",
        hyg_status,
        explanation_text(hyg_status, CREDIT_EXPLANATIONS)
    )
    signal_html += signal_card(
        "JNK 近60日",
        f"{jnk_change}%" if jnk_change is not None else "获取失败",
        jnk_status,
        explanation_text(jnk_status, CREDIT_EXPLANATIONS)
    )
    signal_html += signal_card(
        "跨资产状态",
        macro_status,
        macro_status,
        explanation_text(macro_status, CROSS_ASSET_EXPLANATIONS)
    )
    signal_html += "</div>"

    st.markdown(signal_html, unsafe_allow_html=True)

    if fg is None:
        st.warning("Fear & Greed 未获取到实时数据。请在左侧边栏打开链接查看后，勾选“手动输入 Fear & Greed”并填入数值。")
    else:
        st.caption(f"Fear & Greed 数据来源：{fg_source}")

    st.markdown("---")
    st.subheader("三、五层风险来源拆解")

    s1, s2, s3, s4, s5 = st.columns(5)
    s1.metric("情绪风险 30%", f"{emotion_score}/100", risk_level(emotion_score))
    s2.metric("趋势风险 20%", f"{trend_score}/100", risk_level(trend_score))
    s3.metric("广度风险 20%", f"{breadth_score}/100", risk_level(breadth_score))
    s4.metric("信用风险 20%", f"{credit_score}/100", risk_level(credit_score))
    s5.metric("跨资产风险 10%", f"{cross_asset_score}/100", risk_level(cross_asset_score))

    risk_source_table = pd.DataFrame({
        "模块": ["情绪层", "趋势层", "市场广度", "信用市场", "跨资产"],
        "权重": ["30%", "20%", "20%", "20%", "10%"],
        "代表指标": ["Fear & Greed、VIX", "SPY回调、QQQ回调", "RSP相对SPY、IWM相对SPY", "HYG、JNK", "TLT、GLD"],
        "当前判断": [
            f"{fear_status(fg)} / {vix_status(vix)}",
            f"SPY：{drawdown_status(spy_dd)}，QQQ：{drawdown_status(qqq_dd)}",
            f"RSP：{relative_status(rsp_vs_spy)}，IWM：{relative_status(iwm_vs_spy)}",
            f"HYG：{credit_status(hyg_change)}，JNK：{credit_status(jnk_change)}",
            cross_asset_status(tlt_change, gld_change),
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
        st.markdown(f"当前值：**{round(fg, 1) if fg is not None else '获取失败'}** 当前状态：**{fear_status(fg)}**")
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
        st.info(f"当前广度判断：{relative_status(rsp_vs_spy)}。{explanation_text(relative_status(rsp_vs_spy), BREADTH_EXPLANATIONS)}")
        st.caption("RSP 是等权标普500，SPY 是市值加权标普500。RSP 跑输 SPY，通常说明上涨集中在少数大权重股票上。")

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
        st.info(f"当前广度判断：{relative_status(iwm_vs_spy)}。{explanation_text(relative_status(iwm_vs_spy), BREADTH_EXPLANATIONS)}")
        st.caption("IWM 是小盘股 ETF。IWM 跑赢 SPY，通常说明资金正在向中小盘扩散，市场参与度更好。")

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
# 历史回测 + 排行榜 + 相似度
# =========================================================
with backtest_tab:
    st.subheader("历史回测")
    st.caption("历史 Fear & Greed 免费接口无法稳定还原，因此历史模型主要使用 VIX、回撤、广度、信用和跨资产数据。")

    st.markdown("### 历史最佳加仓窗口排行榜")

    lb_col1, lb_col2, lb_col3 = st.columns([1, 1, 1])
    with lb_col1:
        lb_start = st.date_input("排行榜开始日期", value=pd.Timestamp("2026-02-01"), key="lb_start")
    with lb_col2:
        lb_end = st.date_input("排行榜结束日期", value=pd.Timestamp.today() - pd.Timedelta(days=1), key="lb_end")
    with lb_col3:
        top_n = st.number_input("显示前几名", min_value=5, max_value=50, value=10, step=5)

    if st.button("生成排行榜 + 相似度 + 后验收益"):
        with st.spinner("正在生成历史经验库，时间跨度越长等待越久…"):
            hist_table = build_history_table(lb_start, lb_end)

            if hist_table.empty:
                st.warning("没有生成有效结果，请换一个日期区间再试。")
            else:
                sim_table = add_similarity_columns(hist_table)

                leaderboard = sim_table.sort_values(["风险评分", "日期"], ascending=[False, True]).reset_index(drop=True)
                leaderboard.insert(0, "排名", range(1, len(leaderboard) + 1))

                similar = sim_table.dropna(subset=["与今日相似度"]).sort_values(
                    ["与今日相似度", "风险评分"],
                    ascending=[False, False]
                ).reset_index(drop=True)
                similar.insert(0, "排名", range(1, len(similar) + 1))

                display_cols = [
                    "排名", "日期", "机会质量", "风险评分", "操作动作",
                    "SPY回撤", "QQQ回撤", "VIX",
                    "HYG近60日", "JNK近60日",
                    "SPY30天后", "SPY60天后", "SPY120天后",
                    "QQQ30天后", "QQQ60天后", "QQQ120天后"
                ]

                show_leaderboard = leaderboard[display_cols].head(int(top_n)).copy()

                percent_cols = [
                    "SPY回撤", "QQQ回撤", "HYG近60日", "JNK近60日",
                    "SPY30天后", "SPY60天后", "SPY120天后",
                    "QQQ30天后", "QQQ60天后", "QQQ120天后"
                ]
                for col in percent_cols:
                    show_leaderboard[col] = show_leaderboard[col].apply(format_percent_value)

                st.markdown("#### A. 历史最佳加仓窗口排行榜")
                st.dataframe(show_leaderboard, use_container_width=True, hide_index=True)

                best = leaderboard.iloc[0]
                st.info(
                    f"区间内模型评分最高的日期是 {best['日期']}，"
                    f"风险评分 {best['风险评分']}/100，"
                    f"操作动作：{best['操作动作']}，"
                    f"SPY回撤：{format_percent_value(best['SPY回撤'])}，"
                    f"QQQ回撤：{format_percent_value(best['QQQ回撤'])}。"
                )

                st.markdown("#### B. 今日与历史机会最相似案例")

                sim_cols = [
                    "排名", "日期", "与今日相似度", "机会质量", "风险评分", "操作动作",
                    "SPY回撤", "QQQ回撤", "VIX",
                    "HYG近60日", "JNK近60日",
                    "SPY30天后", "SPY60天后", "SPY120天后",
                    "QQQ30天后", "QQQ60天后", "QQQ120天后"
                ]

                show_similar = similar[sim_cols].head(int(top_n)).copy()
                for col in percent_cols:
                    show_similar[col] = show_similar[col].apply(format_percent_value)

                show_similar["与今日相似度"] = show_similar["与今日相似度"].apply(
                    lambda x: f"{x}%" if pd.notna(x) else "N/A"
                )

                st.dataframe(show_similar, use_container_width=True, hide_index=True)

                top3 = similar.head(3)
                valid_spy_60 = [x for x in top3["SPY60天后"].tolist() if x is not None and not pd.isna(x)]
                valid_qqq_60 = [x for x in top3["QQQ60天后"].tolist() if x is not None and not pd.isna(x)]

                if not top3.empty:
                    best_sim = top3.iloc[0]
                    summary = (
                        f"与今天最相似的历史日期是 {best_sim['日期']}，"
                        f"相似度 {best_sim['与今日相似度']}%，"
                        f"当日风险评分 {best_sim['风险评分']}/100，"
                        f"操作动作：{best_sim['操作动作']}。"
                    )

                    if valid_spy_60:
                        summary += f" 最相似前三个案例的 SPY 60天后平均收益约 {round(sum(valid_spy_60)/len(valid_spy_60), 2)}%。"

                    if valid_qqq_60:
                        summary += f" QQQ 60天后平均收益约 {round(sum(valid_qqq_60)/len(valid_qqq_60), 2)}%。"

                    st.info(summary)

    st.markdown("---")
    st.markdown("### 单日回测")

    query_date = st.date_input(
        "选择查询日期",
        value=pd.Timestamp.today() - pd.Timedelta(days=1),
        min_value=pd.Timestamp("2018-01-01"),
        max_value=pd.Timestamp.today() - pd.Timedelta(days=1),
        format="YYYY/MM/DD",
    )

    if st.button("开始单日回测"):
        with st.spinner("正在计算历史数据…"):
            end = (pd.Timestamp(query_date) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
            start = (pd.Timestamp(query_date) - pd.Timedelta(days=430)).strftime("%Y-%m-%d")

            symbols = ["SPY", "QQQ", "RSP", "IWM", "HYG", "JNK", "TLT", "GLD", "^VIX"]
            dfs = {s: get_history_range(s, start, end) for s in symbols}

            row = score_one_day(query_date, dfs)

            st.markdown("### 回测结果")
            r1, r2, r3 = st.columns(3)
            r1.metric("市场状态", row["市场状态"])
            r2.metric("操作动作", row["操作动作"])
            r3.metric("综合风险评分", f"{row['风险评分']}/100", risk_level(row["风险评分"]))

            rr = pd.DataFrame({
                "指标": ["VIX", "SPY回撤", "QQQ回撤", "RSP相对SPY", "IWM相对SPY", "HYG近60日", "JNK近60日"],
                "数值": [
                    row["VIX"],
                    format_percent_value(row["SPY回撤"]),
                    format_percent_value(row["QQQ回撤"]),
                    format_percent_value(row["RSP相对SPY"]),
                    format_percent_value(row["IWM相对SPY"]),
                    format_percent_value(row["HYG近60日"]),
                    format_percent_value(row["JNK近60日"]),
                ],
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

    st.markdown("### 状态说明")
    status_table = pd.DataFrame({
        "类别": [
            "市场广度", "市场广度", "市场广度", "市场广度",
            "信用市场", "信用市场", "信用市场", "信用市场",
            "跨资产", "跨资产", "跨资产", "跨资产", "跨资产"
        ],
        "状态": [
            "广度正常", "广度较差", "广度偏弱", "广度较好",
            "信用稳定", "信用风险升温", "信用稳定偏强", "信用偏弱",
            "跨资产中性", "通胀或货币信用压力", "避险或衰退担忧", "利率压力偏大", "利率压力缓和"
        ],
        "说明": [
            BREADTH_EXPLANATIONS["广度正常"],
            BREADTH_EXPLANATIONS["广度较差"],
            BREADTH_EXPLANATIONS["广度偏弱"],
            BREADTH_EXPLANATIONS["广度较好"],
            CREDIT_EXPLANATIONS["信用稳定"],
            CREDIT_EXPLANATIONS["信用风险升温"],
            CREDIT_EXPLANATIONS["信用稳定偏强"],
            CREDIT_EXPLANATIONS["信用偏弱"],
            CROSS_ASSET_EXPLANATIONS["跨资产中性"],
            CROSS_ASSET_EXPLANATIONS["通胀或货币信用压力"],
            CROSS_ASSET_EXPLANATIONS["避险或衰退担忧"],
            CROSS_ASSET_EXPLANATIONS["利率压力偏大"],
            CROSS_ASSET_EXPLANATIONS["利率压力缓和"],
        ]
    })
    st.dataframe(status_table, use_container_width=True, hide_index=True)

    st.markdown("### 加仓规则")
    plan = pd.DataFrame({
        "操作动作": ["避免追高", "暂停抄底", "正常定投", "加仓30%", "再加仓30%", "加仓剩余40%"],
        "触发条件": [
            "Fear & Greed > 75 且 VIX <= 15，市场FOMO明显",
            "HYG/JNK 同步明显下跌，信用市场恶化",
            "风险评分 < 20",
            "风险评分 20~40，信用市场未失控",
            "风险评分 40~60，信用市场未失控",
            "风险评分 >= 60，且信用市场未崩盘",
        ],
        "资金动作": [
            "不加仓，避免追高",
            "不加仓，保留现金",
            "只执行原定投计划",
            "投入预备资金30%",
            "再投入预备资金30%",
            "投入剩余40%",
        ],
        "累计投入": ["0%", "0%", "0%", "30%", "60%", "100%"],
        "剩余现金": ["100%", "100%", "100%", "70%", "40%", "0%"],
    })

    st.dataframe(plan, use_container_width=True, hide_index=True)

st.markdown("---")
st.caption(f"更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
