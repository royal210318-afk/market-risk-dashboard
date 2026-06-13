import streamlit as st
import requests
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(
    page_title="市场风险仪表盘",
    page_icon="📈",
    layout="wide"
)

# -----------------------
# 全局样式注入
# -----------------------
st.markdown("""
<style>
/* ── 全局背景与字体 ── */
.stApp {
    background-color: #0d1117;
    color: #c9d1d9;
    font-family: 'Inter', 'SF Pro Display', -apple-system, sans-serif;
}

/* ── 顶部标题区 ── */
.dashboard-header {
    padding: 2rem 0 1.5rem 0;
    border-bottom: 1px solid #21262d;
    margin-bottom: 2rem;
}
.dashboard-title {
    font-size: 1.75rem;
    font-weight: 700;
    color: #e6edf3;
    letter-spacing: -0.5px;
    margin: 0;
}
.dashboard-subtitle {
    font-size: 0.8rem;
    color: #8b949e;
    margin-top: 4px;
    letter-spacing: 0.5px;
}

/* ── 分区标题 ── */
h2, h3, .stSubheader {
    color: #e6edf3 !important;
    font-weight: 600 !important;
    letter-spacing: -0.3px !important;
}

/* ── 指标卡片（st.metric）── */
[data-testid="metric-container"] {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    transition: border-color 0.2s;
}
[data-testid="metric-container"]:hover {
    border-color: #388bfd;
}
[data-testid="metric-container"] label {
    color: #8b949e !important;
    font-size: 0.72rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.6px !important;
    text-transform: uppercase !important;
}
[data-testid="metric-container"] [data-testid="metric-value"] {
    color: #e6edf3 !important;
    font-size: 1.5rem !important;
    font-weight: 700 !important;
}
[data-testid="metric-container"] [data-testid="metric-delta"] {
    font-size: 0.75rem !important;
    font-weight: 500 !important;
}

/* ── info / warning 提示框 ── */
.stAlert {
    background: #161b22 !important;
    border: 1px solid #21262d !important;
    border-left: 3px solid #388bfd !important;
    border-radius: 8px !important;
    color: #c9d1d9 !important;
}

/* ── 数据表格 ── */
.stDataFrame {
    border: 1px solid #21262d !important;
    border-radius: 10px !important;
    overflow: hidden;
}
[data-testid="stDataFrameContainer"] table {
    background: #161b22 !important;
}
[data-testid="stDataFrameContainer"] th {
    background: #0d1117 !important;
    color: #8b949e !important;
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.5px !important;
    text-transform: uppercase !important;
    border-bottom: 1px solid #21262d !important;
}
[data-testid="stDataFrameContainer"] td {
    color: #c9d1d9 !important;
    font-size: 0.82rem !important;
    border-bottom: 1px solid #21262d !important;
}

/* ── Tab 组件 ── */
.stTabs [data-baseweb="tab-list"] {
    background: #0d1117;
    border-bottom: 1px solid #21262d;
    gap: 0;
}
.stTabs [data-baseweb="tab"] {
    color: #8b949e !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    padding: 8px 16px !important;
    border-radius: 6px 6px 0 0 !important;
    border: none !important;
    background: transparent !important;
}
.stTabs [aria-selected="true"] {
    color: #e6edf3 !important;
    border-bottom: 2px solid #388bfd !important;
    background: transparent !important;
}
.stTabs [data-baseweb="tab-panel"] {
    background: #0d1117;
    padding-top: 1.5rem;
}

/* ── 日期选择器 ── */
[data-testid="stDateInput"] input {
    background: #161b22 !important;
    border: 1px solid #21262d !important;
    border-radius: 8px !important;
    color: #e6edf3 !important;
    font-size: 0.85rem !important;
}

/* ── Spinner ── */
.stSpinner > div {
    border-top-color: #388bfd !important;
}

/* ── 分隔线 ── */
hr {
    border-color: #21262d !important;
    margin: 2rem 0 !important;
}

/* ── caption ── */
.stCaption {
    color: #8b949e !important;
    font-size: 0.72rem !important;
}

/* ── 滚动条 ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0d1117; }
::-webkit-scrollbar-thumb { background: #21262d; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #30363d; }

/* ── markdown 正文 ── */
.stMarkdown p, .stMarkdown li {
    color: #c9d1d9 !important;
    font-size: 0.85rem !important;
    line-height: 1.7 !important;
}
.stMarkdown strong {
    color: #e6edf3 !important;
}

/* ── 状态徽章 ── */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.4px;
}
.badge-red    { background: #3d1a1a; color: #ff7b72; border: 1px solid #7d2020; }
.badge-orange { background: #2d1f0a; color: #ffa657; border: 1px solid #6e3b0f; }
.badge-yellow { background: #2d2a0a; color: #e3b341; border: 1px solid #6d5c0e; }
.badge-green  { background: #0a2d1a; color: #3fb950; border: 1px solid #0f5a2a; }
.badge-purple { background: #1e1a3d; color: #a371f7; border: 1px solid #422b7a; }
.badge-blue   { background: #0d1f3d; color: #79c0ff; border: 1px solid #1a4070; }
</style>
""", unsafe_allow_html=True)

# Plotly 深色主题配置
PLOTLY_THEME = dict(
    paper_bgcolor="#0d1117",
    plot_bgcolor="#161b22",
    font=dict(color="#c9d1d9", family="Inter, sans-serif", size=12),
    xaxis=dict(
        gridcolor="#21262d",
        linecolor="#21262d",
        tickcolor="#21262d",
        tickfont=dict(color="#8b949e", size=11),
    ),
    yaxis=dict(
        gridcolor="#21262d",
        linecolor="#21262d",
        tickcolor="#21262d",
        tickfont=dict(color="#8b949e", size=11),
    ),
    title=dict(font=dict(color="#e6edf3", size=14, family="Inter, sans-serif")),
    margin=dict(l=40, r=20, t=50, b=30),
    hovermode="x unified",
)

LINE_COLOR = "#388bfd"
THRESHOLD_COLOR = "#e3b341"

try:
    API_KEY = st.secrets["TWELVE_API_KEY"]
except Exception:
    API_KEY = ""

# 页头
st.markdown("""
<div class="dashboard-header">
    <p class="dashboard-title">📈 市场风险仪表盘</p>
    <p class="dashboard-subtitle">美股回调加仓版 · 情绪 · 波动率 · 市场广度 · 信用风险 · 跨资产联动</p>
</div>
""", unsafe_allow_html=True)


# -----------------------
# Fear & Greed
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
                    dt = pd.to_datetime(x, unit="ms") if x > 10000000000 else pd.to_datetime(x, unit="s")
                else:
                    dt = pd.to_datetime(x)
                rows.append({"date": dt, "value": float(y)})
            except Exception:
                continue
        hist_df = pd.DataFrame(rows)
        if not hist_df.empty:
            hist_df = hist_df.dropna().sort_values("date").tail(90)
        return score, hist_df
    except Exception:
        return 50.0, pd.DataFrame(columns=["date", "value"])


# -----------------------
# VIX
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
# Twelve Data
# -----------------------
@st.cache_data(ttl=1800)
def get_history(symbol):
    if not API_KEY:
        return None
    url = (
        f"https://api.twelvedata.com/time_series"
        f"?symbol={symbol}&interval=1day&outputsize=260&apikey={API_KEY}"
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
    return round((latest - past) / past * 100, 2)


def calc_recent_change_from_series(df, days=20):
    if df is None or df.empty or len(df) < days:
        return None
    return round(float(df.iloc[-1]["value"]) - float(df.iloc[-days]["value"]), 2)


def calc_min_from_series(df):
    if df is None or df.empty:
        return None
    return round(float(df["value"].min()), 2)


def calc_max_from_series(df):
    if df is None or df.empty:
        return None
    return round(float(df["value"].max()), 2)


def make_return_series(df, days=60):
    if df is None or df.empty or len(df) < days:
        return pd.DataFrame(columns=["date", "value"])
    temp = df.tail(days).copy()
    start_price = float(temp.iloc[0]["close"])
    if start_price == 0:
        return pd.DataFrame(columns=["date", "value"])
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
    if a_start == 0 or b_start == 0:
        return pd.DataFrame(columns=["date", "value"])
    merged["a_return"] = (merged["a_close"] / a_start - 1) * 100
    merged["b_return"] = (merged["b_close"] / b_start - 1) * 100
    merged["value"] = (merged["a_return"] - merged["b_return"]).round(2)
    return merged[["date", "value"]]


# -----------------------
# 状态解释
# -----------------------
def fear_status(fg):
    if fg < 25: return "极度恐惧"
    elif fg < 45: return "恐惧"
    elif fg < 75: return "中性"
    else: return "极度贪婪"

def vix_status(vix):
    if vix is None: return "获取失败"
    if vix <= 15: return "过度乐观"
    elif vix < 20: return "低波动"
    elif vix < 30: return "风险升温"
    else: return "恐慌区"

def drawdown_status(dd):
    if dd is None: return "获取失败"
    if dd > -5: return "接近高位"
    elif dd > -10: return "轻度回调"
    elif dd > -20: return "明显回调"
    else: return "深度回调"

def relative_status(diff):
    if diff is None: return "获取失败"
    if diff < -5: return "广度较差"
    elif diff < -2: return "广度偏弱"
    elif diff > 2: return "广度较好"
    else: return "广度正常"

def credit_status(change):
    if change is None: return "获取失败"
    if change < -5: return "信用风险升温"
    elif change < -2: return "信用偏弱"
    elif change > 2: return "信用稳定偏强"
    else: return "信用稳定"

def cross_asset_status(tlt_change, gld_change):
    if tlt_change is None or gld_change is None: return "获取失败"
    if gld_change > 5 and tlt_change < -3: return "通胀或货币信用压力"
    elif gld_change > 5 and tlt_change > 3: return "避险或衰退担忧"
    elif tlt_change < -5: return "利率压力偏大"
    elif tlt_change > 5: return "利率压力缓和"
    else: return "跨资产中性"


# -----------------------
# 单项评分
# -----------------------
def score_fear(fg):
    if fg is None: return None
    if fg < 25: return 80
    elif fg < 45: return 50
    elif fg < 75: return 20
    else: return 70

def score_vix(vix):
    if vix is None: return None
    if vix <= 15: return 25
    elif vix < 20: return 20
    elif vix < 30: return 50
    else: return 85

def score_drawdown(dd):
    if dd is None: return None
    if dd > -5: return 10
    elif dd > -10: return 40
    elif dd > -20: return 70
    else: return 90

def score_relative(diff):
    if diff is None: return None
    if diff < -5: return 70
    elif diff < -2: return 45
    else: return 20

def score_credit(change):
    if change is None: return None
    if change < -5: return 85
    elif change < -2: return 55
    else: return 15

def score_cross_asset(tlt_change, gld_change):
    if tlt_change is None or gld_change is None: return None
    if gld_change > 5 and tlt_change < -3: return 75
    elif gld_change > 5 and tlt_change > 3: return 65
    elif tlt_change < -5: return 55
    elif tlt_change > 5: return 25
    else: return 20

def average_score(values):
    valid = [v for v in values if v is not None]
    if not valid: return 0
    return round(sum(valid) / len(valid))

def risk_level(score):
    if score < 20: return "低风险"
    elif score < 40: return "轻度回调"
    elif score < 60: return "中等风险"
    else: return "高风险"


# -----------------------
# 图表函数（深色主题版）
# -----------------------
def show_line_chart(df, title, y_title, threshold_lines=None):
    if df is None or df.empty:
        st.warning("暂无足够数据生成图表")
        return

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["value"],
        mode="lines",
        line=dict(color=LINE_COLOR, width=2),
        fill="tozeroy",
        fillcolor="rgba(56,139,253,0.08)",
        hovertemplate="%{y:.2f}<extra></extra>",
    ))

    fig.update_layout(
        title=title,
        yaxis_title=y_title,
        height=340,
        **PLOTLY_THEME,
    )

    if threshold_lines:
        for line in threshold_lines:
            fig.add_hline(
                y=line["y"],
                line_dash="dot",
                line_color=THRESHOLD_COLOR,
                line_width=1,
                annotation_text=line["text"],
                annotation_font_color="#e3b341",
                annotation_position="top left",
            )

    st.plotly_chart(fig, use_container_width=True)


def show_fear_greed_gauge(fg):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=fg,
        title={"text": "Fear & Greed", "font": {"color": "#e6edf3", "size": 14}},
        number={"font": {"color": "#e6edf3", "size": 40}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#8b949e", "tickfont": {"color": "#8b949e"}},
            "bar": {"color": LINE_COLOR, "thickness": 0.25},
            "bgcolor": "#161b22",
            "bordercolor": "#21262d",
            "steps": [
                {"range": [0, 25],  "color": "#3d1a1a"},
                {"range": [25, 45], "color": "#2d2a0a"},
                {"range": [45, 75], "color": "#0d1f3d"},
                {"range": [75, 100],"color": "#0a2d1a"},
            ],
            "threshold": {
                "line": {"color": "#ff7b72", "width": 3},
                "thickness": 0.75,
                "value": fg,
            },
        },
    ))
    fig.update_layout(
        height=300,
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        font=dict(color="#c9d1d9"),
        margin=dict(l=30, r=30, t=50, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)


def show_chart_summary(current, low, high, recent_change, status, unit="%"):
    a, b, c, d = st.columns(4)
    a.metric("当前值", current if current is not None else "获取失败")
    b.metric("区间低点", low if low is not None else "获取失败")
    c.metric("区间高点", high if high is not None else "获取失败")
    d.metric(
        "近20日变化",
        f"{recent_change}{unit}" if recent_change is not None else "获取失败",
        status,
    )


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


# -----------------------
# 子评分
# -----------------------
emotion_score    = average_score([score_fear(fg), score_vix(vix)])
breadth_score    = average_score([score_relative(rsp_vs_spy), score_relative(iwm_vs_spy)])
credit_score     = average_score([score_credit(hyg_change), score_credit(jnk_change)])
cross_asset_score= average_score([score_cross_asset(tlt_change, gld_change)])
trend_score      = average_score([score_drawdown(spy_dd), score_drawdown(qqq_dd)])
risk_score       = average_score([emotion_score, trend_score, breadth_score, credit_score, cross_asset_score])


# -----------------------
# 关键判断
# -----------------------
credit_warning  = (hyg_change is not None and hyg_change < -5) or (jnk_change is not None and jnk_change < -5)
good_buy_window = vix is not None and fg is not None and vix > 30 and fg < 25 and not credit_warning
fomo_warning    = vix is not None and fg is not None and vix <= 15 and fg > 75
breadth_warning = (rsp_vs_spy is not None and rsp_vs_spy < -5) or (iwm_vs_spy is not None and iwm_vs_spy < -5)
normal_pullback = risk_score >= 20 and risk_score < 60 and not credit_warning


# -----------------------
# 买入等级决策
# -----------------------
if credit_warning:
    buy_grade = "D级风险"; buy_action = "信用市场恶化，暂停抄底，优先保留现金。"
    scene = "🔴 信用风险升温"
    advice = "当前策略：暂停抄底，优先观察信用市场。\n\n如果股市下跌，同时 HYG/JNK 也明显下跌，说明市场不只是估值调整，而是在担心企业违约和融资压力。\n\n这种时候不要急着加仓，先等信用市场稳定。"
elif good_buy_window:
    buy_grade = "A级机会"; buy_action = "恐慌充分但信用未失控，可以重点分批加仓。"
    scene = "🟠 优质加仓窗口"
    advice = "当前策略：重点关注加仓机会。\n\nVIX超过30，Fear & Greed低于25，说明市场已经出现明显恐慌。\n\n如果 HYG/JNK 没有同步崩盘，这通常是比较好的分批加仓窗口。"
elif fomo_warning:
    buy_grade = "E级过热"; buy_action = "市场过度乐观，不适合追高。"
    scene = "🟣 市场过热"
    advice = "当前策略：谨慎追高。\n\nFear & Greed 高于75，同时 VIX 低于或接近15，说明市场不愿意给风险定价，FOMO情绪较强。\n\n这种环境不适合大幅加仓。"
elif normal_pullback:
    buy_grade = "B级机会"; buy_action = "市场出现回调但信用未失控，可以按计划分批加仓。"
    if risk_score < 40:
        scene = "🟡 第一档回调"
        advice = "当前策略：执行第一档加仓。\n\n建议投入预备资金：30%。\n\n累计投入：30%\n剩余现金：70%"
    else:
        scene = "🟠 第二档回调"
        advice = "当前策略：执行第二档加仓。\n\n建议再投入预备资金：30%。\n\n累计投入：60%\n剩余现金：40%"
elif breadth_warning:
    buy_grade = "C级观察"; buy_action = "上涨广度偏弱，谨慎观察，不盲目追高。"
    scene = "🟡 上涨广度偏弱"
    advice = "当前策略：谨慎观察。\n\nRSP相对SPY或IWM相对SPY明显走弱，说明指数上涨可能主要由少数权重股推动。\n\n这种上涨不够健康，不适合盲目追高。"
elif risk_score >= 60:
    buy_grade = "B级机会"; buy_action = "恐慌较高，但仍需确认信用市场是否稳定。"
    scene = "🔴 极端恐慌"
    advice = "当前策略：执行第三档加仓。\n\n建议投入剩余资金：40%。\n\n累计投入：100%\n剩余现金：0%\n\n但前提是：HYG/JNK 没有明显崩盘。"
else:
    buy_grade = "C级观察"; buy_action = "市场风险较低，继续正常定投，回调资金暂不动用。"
    scene = "🟢 正常市场"
    advice = "当前策略：正常定投。\n\n市场风险较低，按原计划持续定投即可。\n\n回调加仓资金暂不动用。"


# =======================
# 一、当前结论
# =======================
st.subheader("一、当前结论")

col_a, col_b, col_c = st.columns(3)
col_a.metric("当前市场状态", scene)
col_b.metric("当前买入等级", buy_grade)
col_c.metric("综合风险评分", f"{risk_score}/100", risk_level(risk_score))

st.info(buy_action)
st.markdown("---")


# =======================
# 二、核心指标
# =======================
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


# =======================
# 三、风险来源拆解
# =======================
st.subheader("三、风险来源拆解")

s1, s2, s3, s4, s5 = st.columns(5)
s1.metric("情绪风险", f"{emotion_score}/100", risk_level(emotion_score))
s2.metric("趋势风险", f"{trend_score}/100", risk_level(trend_score))
s3.metric("广度风险", f"{breadth_score}/100", risk_level(breadth_score))
s4.metric("信用风险", f"{credit_score}/100", risk_level(credit_score))
s5.metric("跨资产风险", f"{cross_asset_score}/100", risk_level(cross_asset_score))

risk_source_table = pd.DataFrame({
    "模块":   ["情绪层", "趋势层", "市场广度", "信用市场", "跨资产"],
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


# =======================
# 四、核心指标图表
# =======================
st.subheader("四、核心指标图表")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Fear & Greed", "VIX", "RSP相对SPY", "IWM相对SPY", "HYG近60日", "JNK近60日"
])

with tab1:
    st.markdown("#### Fear & Greed 恐惧贪婪指数")
    show_fear_greed_gauge(fg)
    st.markdown(f"当前值：**{round(fg, 1)}** · 当前状态：**{fear_status(fg)}**")
    st.markdown("- 0–25：极度恐惧  · 25–45：恐惧  · 45–75：中性  · 75–100：极度贪婪")
    if not fg_hist_df.empty:
        show_line_chart(fg_hist_df, "Fear & Greed 历史走势（近90日）", "分数",
            threshold_lines=[{"y": 25, "text": "25：极度恐惧"}, {"y": 75, "text": "75：极度贪婪"}])

with tab2:
    st.markdown("#### VIX 恐慌指数")
    vix_recent_change = calc_recent_change_from_series(vix_hist_df, 20)
    vix_low  = calc_min_from_series(vix_hist_df)
    vix_high = calc_max_from_series(vix_hist_df)
    show_chart_summary(vix, vix_low, vix_high, vix_recent_change, vix_status(vix), unit="")
    show_line_chart(vix_hist_df, "VIX 恐慌指数（近6个月）", "VIX",
        threshold_lines=[{"y": 15, "text": "15：过度乐观"}, {"y": 30, "text": "30：恐慌区"}])
    st.caption("VIX越高，说明期权市场为风险保险支付的价格越高。")

with tab3:
    st.markdown("#### RSP 相对 SPY")
    rsp_current      = round(float(rsp_vs_spy_series.iloc[-1]["value"]), 2) if not rsp_vs_spy_series.empty else None
    rsp_low          = calc_min_from_series(rsp_vs_spy_series)
    rsp_high         = calc_max_from_series(rsp_vs_spy_series)
    rsp_recent_change= calc_recent_change_from_series(rsp_vs_spy_series, 20)
    show_chart_summary(
        f"{rsp_current}%" if rsp_current is not None else None,
        f"{rsp_low}%"    if rsp_low    is not None else None,
        f"{rsp_high}%"   if rsp_high   is not None else None,
        rsp_recent_change, relative_status(rsp_vs_spy),
    )
    show_line_chart(rsp_vs_spy_series, "RSP 相对 SPY（近60日）", "相对表现 %",
        threshold_lines=[{"y": 0, "text": "0：等权与市值加权持平"}, {"y": -5, "text": "-5：广度明显偏弱"}])
    st.caption("RSP跑输SPY，说明上涨可能集中在少数大权重股票上。")

with tab4:
    st.markdown("#### IWM 相对 SPY")
    iwm_current      = round(float(iwm_vs_spy_series.iloc[-1]["value"]), 2) if not iwm_vs_spy_series.empty else None
    iwm_low          = calc_min_from_series(iwm_vs_spy_series)
    iwm_high         = calc_max_from_series(iwm_vs_spy_series)
    iwm_recent_change= calc_recent_change_from_series(iwm_vs_spy_series, 20)
    show_chart_summary(
        f"{iwm_current}%" if iwm_current is not None else None,
        f"{iwm_low}%"    if iwm_low    is not None else None,
        f"{iwm_high}%"   if iwm_high   is not None else None,
        iwm_recent_change, relative_status(iwm_vs_spy),
    )
    show_line_chart(iwm_vs_spy_series, "IWM 相对 SPY（近60日）", "相对表现 %",
        threshold_lines=[{"y": 0, "text": "0：小盘与大盘持平"}, {"y": -5, "text": "-5：小盘明显跑输"}])
    st.caption("IWM跑赢SPY，说明资金开始扩散到小盘股；IWM跑输SPY，说明市场广度偏弱。")

with tab5:
    st.markdown("#### HYG 近60日")
    hyg_current      = round(float(hyg_series.iloc[-1]["value"]), 2) if not hyg_series.empty else None
    hyg_low          = calc_min_from_series(hyg_series)
    hyg_high         = calc_max_from_series(hyg_series)
    hyg_recent_change= calc_recent_change_from_series(hyg_series, 20)
    show_chart_summary(
        f"{hyg_current}%" if hyg_current is not None else None,
        f"{hyg_low}%"    if hyg_low    is not None else None,
        f"{hyg_high}%"   if hyg_high   is not None else None,
        hyg_recent_change, credit_status(hyg_change),
    )
    show_line_chart(hyg_series, "HYG 近60日变化", "涨跌幅 %",
        threshold_lines=[{"y": 0, "text": "0：持平"}, {"y": -5, "text": "-5：信用风险升温"}])
    st.caption("HYG大跌说明高收益债承压，信用市场可能开始担心违约风险。")

with tab6:
    st.markdown("#### JNK 近60日")
    jnk_current      = round(float(jnk_series.iloc[-1]["value"]), 2) if not jnk_series.empty else None
    jnk_low          = calc_min_from_series(jnk_series)
    jnk_high         = calc_max_from_series(jnk_series)
    jnk_recent_change= calc_recent_change_from_series(jnk_series, 20)
    show_chart_summary(
        f"{jnk_current}%" if jnk_current is not None else None,
        f"{jnk_low}%"    if jnk_low    is not None else None,
        f"{jnk_high}%"   if jnk_high   is not None else None,
        jnk_recent_change, credit_status(jnk_change),
    )
    show_line_chart(jnk_series, "JNK 近60日变化", "涨跌幅 %",
        threshold_lines=[{"y": 0, "text": "0：持平"}, {"y": -5, "text": "-5：信用风险升温"}])
    st.caption("JNK与HYG互相验证，如果两者同步大跌，要警惕信用风险。")

st.markdown("---")


# =======================
# 五、历史交易日查询
# =======================
st.subheader("五、历史交易日查询")
st.caption("选择任意历史交易日，查询当天各指标数值及系统生成的加仓决策。")

query_date = st.date_input(
    "选择查询日期",
    value=None,
    min_value=pd.Timestamp("2018-01-01"),
    max_value=pd.Timestamp.today() - pd.Timedelta(days=1),
    format="YYYY/MM/DD",
)

if query_date is not None:
    with st.spinner("正在拉取历史数据，请稍候…"):

        @st.cache_data(ttl=86400)
        def get_history_range(symbol, start, end):
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(start=start, end=end)
                if hist is None or hist.empty:
                    return None
                hist = hist.reset_index()
                hist["date"]  = pd.to_datetime(hist["Date"]).dt.tz_localize(None)
                hist["close"] = hist["Close"].astype(float)
                hist["high"]  = hist["High"].astype(float)
                return hist[["date", "close", "high"]].sort_values("date")
            except Exception:
                return None

        hist_end   = (pd.Timestamp(query_date) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        hist_start = (pd.Timestamp(query_date) - pd.Timedelta(days=400)).strftime("%Y-%m-%d")

        h_spy = get_history_range("SPY",  hist_start, hist_end)
        h_qqq = get_history_range("QQQ",  hist_start, hist_end)
        h_rsp = get_history_range("RSP",  hist_start, hist_end)
        h_iwm = get_history_range("IWM",  hist_start, hist_end)
        h_hyg = get_history_range("HYG",  hist_start, hist_end)
        h_jnk = get_history_range("JNK",  hist_start, hist_end)
        h_tlt = get_history_range("TLT",  hist_start, hist_end)
        h_gld = get_history_range("GLD",  hist_start, hist_end)
        h_vix = get_history_range("^VIX", hist_start, hist_end)

        def get_df_up_to_date(df, target_date):
            if df is None or df.empty:
                return None
            subset = df[df["date"] <= pd.Timestamp(target_date)].copy()
            return subset if not subset.empty else None

        def get_value_on_date(df, target_date):
            subset = get_df_up_to_date(df, target_date)
            if subset is None:
                return None
            return round(float(subset.iloc[-1]["close"]), 2)

        h_spy_q = get_df_up_to_date(h_spy, query_date)
        h_qqq_q = get_df_up_to_date(h_qqq, query_date)
        h_rsp_q = get_df_up_to_date(h_rsp, query_date)
        h_iwm_q = get_df_up_to_date(h_iwm, query_date)
        h_hyg_q = get_df_up_to_date(h_hyg, query_date)
        h_jnk_q = get_df_up_to_date(h_jnk, query_date)
        h_tlt_q = get_df_up_to_date(h_tlt, query_date)
        h_gld_q = get_df_up_to_date(h_gld, query_date)

        q_vix              = get_value_on_date(h_vix, query_date)
        q_spy_price, q_spy_dd = calc_drawdown(h_spy_q)
        q_qqq_price, q_qqq_dd = calc_drawdown(h_qqq_q)

        q_spy_change = calc_change(h_spy_q, 60)
        q_rsp_change = calc_change(h_rsp_q, 60)
        q_iwm_change = calc_change(h_iwm_q, 60)
        q_hyg_change = calc_change(h_hyg_q, 60)
        q_jnk_change = calc_change(h_jnk_q, 60)
        q_tlt_change = calc_change(h_tlt_q, 60)
        q_gld_change = calc_change(h_gld_q, 60)

        q_rsp_vs_spy = round(q_rsp_change - q_spy_change, 2) if q_rsp_change is not None and q_spy_change is not None else None
        q_iwm_vs_spy = round(q_iwm_change - q_spy_change, 2) if q_iwm_change is not None and q_spy_change is not None else None

        q_emotion_score = average_score([score_vix(q_vix)])
        q_trend_score   = average_score([score_drawdown(q_spy_dd), score_drawdown(q_qqq_dd)])
        q_breadth_score = average_score([score_relative(q_rsp_vs_spy), score_relative(q_iwm_vs_spy)])
        q_credit_score  = average_score([score_credit(q_hyg_change), score_credit(q_jnk_change)])
        q_cross_score   = average_score([score_cross_asset(q_tlt_change, q_gld_change)])
        q_risk_score    = average_score([q_emotion_score, q_trend_score, q_breadth_score, q_credit_score, q_cross_score])

        q_credit_warning = (q_hyg_change is not None and q_hyg_change < -5) or (q_jnk_change is not None and q_jnk_change < -5)
        q_good_buy       = q_vix is not None and q_vix > 30 and not q_credit_warning
        q_fomo           = q_vix is not None and q_vix <= 15
        q_breadth_warn   = (q_rsp_vs_spy is not None and q_rsp_vs_spy < -5) or (q_iwm_vs_spy is not None and q_iwm_vs_spy < -5)
        q_normal_pullback= q_risk_score >= 20 and q_risk_score < 60 and not q_credit_warning

        if q_credit_warning:
            q_grade = "D级风险"; q_scene = "🔴 信用风险升温"; q_action = "信用市场恶化，暂停抄底，优先保留现金。"
        elif q_good_buy:
            q_grade = "A级机会"; q_scene = "🟠 优质加仓窗口"; q_action = "VIX超过30，信用市场未失控，可以重点分批加仓。"
        elif q_fomo:
            q_grade = "E级过热"; q_scene = "🟣 市场过热"; q_action = "VIX极低，市场FOMO情绪较强，不适合追高。"
        elif q_normal_pullback:
            q_grade = "B级机会"
            q_scene = "🟡 第一档回调" if q_risk_score < 40 else "🟠 第二档回调"
            q_action = "市场出现回调但信用未失控，可按计划分批加仓。"
        elif q_breadth_warn:
            q_grade = "C级观察"; q_scene = "🟡 上涨广度偏弱"; q_action = "RSP或IWM相对SPY走弱，谨慎观察，不盲目追高。"
        elif q_risk_score >= 60:
            q_grade = "B级机会"; q_scene = "🔴 极端恐慌"; q_action = "恐慌较高，仍需确认信用市场是否稳定。"
        else:
            q_grade = "C级观察"; q_scene = "🟢 正常市场"; q_action = "市场风险较低，继续正常定投，回调资金暂不动用。"

    actual_date_label = str(query_date)
    if h_spy_q is not None and not h_spy_q.empty:
        actual_date_label = h_spy_q.iloc[-1]["date"].strftime("%Y-%m-%d")
        if actual_date_label != str(query_date):
            st.caption(f"⚠️ {query_date} 非交易日，已自动使用前一个交易日 {actual_date_label} 的数据。")

    st.markdown(f"#### {actual_date_label} 市场快照")

    qa, qb, qc = st.columns(3)
    qa.metric("市场状态", q_scene)
    qb.metric("买入等级", q_grade)
    qc.metric("综合风险评分", f"{q_risk_score}/100", risk_level(q_risk_score))

    st.info(q_action)

    qc1, qc2, qc3, qc4, qc5, qc6 = st.columns(6)
    qc1.metric("VIX",       q_vix         if q_vix         is not None else "N/A", vix_status(q_vix))
    qc2.metric("SPY 回调",  f"{q_spy_dd}%" if q_spy_dd     is not None else "N/A", drawdown_status(q_spy_dd))
    qc3.metric("QQQ 回调",  f"{q_qqq_dd}%" if q_qqq_dd    is not None else "N/A", drawdown_status(q_qqq_dd))
    qc4.metric("RSP/SPY",   f"{q_rsp_vs_spy}%" if q_rsp_vs_spy is not None else "N/A", relative_status(q_rsp_vs_spy))
    qc5.metric("HYG 60日",  f"{q_hyg_change}%" if q_hyg_change is not None else "N/A", credit_status(q_hyg_change))
    qc6.metric("JNK 60日",  f"{q_jnk_change}%" if q_jnk_change is not None else "N/A", credit_status(q_jnk_change))

    qs1, qs2, qs3, qs4, qs5 = st.columns(5)
    qs1.metric("情绪风险",   f"{q_emotion_score}/100", risk_level(q_emotion_score))
    qs2.metric("趋势风险",   f"{q_trend_score}/100",   risk_level(q_trend_score))
    qs3.metric("广度风险",   f"{q_breadth_score}/100", risk_level(q_breadth_score))
    qs4.metric("信用风险",   f"{q_credit_score}/100",  risk_level(q_credit_score))
    qs5.metric("跨资产风险", f"{q_cross_score}/100",   risk_level(q_cross_score))

    st.caption("⚠️ 历史 Fear & Greed 无法从免费接口还原，情绪层评分仅基于 VIX，偏保守。")

st.markdown("---")


# =======================
# 六、加仓计划
# =======================
st.subheader("六、美股回调加仓计划")

st.info(advice)

plan = pd.DataFrame({
    "等级":       ["A级机会", "B级机会", "C级观察", "D级风险", "E级过热"],
    "典型条件":   [
        "VIX > 30，Fear & Greed < 25，信用市场稳定",
        "市场出现回调，信用市场没有失控",
        "情绪中性，指数接近高位，风险不高",
        "HYG/JNK同步大跌，信用市场恶化",
        "Fear & Greed > 75，VIX ≤ 15，市场FOMO",
    ],
    "动作": [
        "重点分批加仓",
        "按计划分批加仓",
        "正常定投，回调资金暂不动用",
        "暂停抄底，保留现金",
        "避免追高，适当降低进攻性",
    ],
    "预备资金使用": [
        "可投入30%~60%，视信用市场决定",
        "第一档30%，第二档再30%",
        "0%",
        "0%",
        "0%，必要时减仓",
    ],
})
st.dataframe(plan, use_container_width=True, hide_index=True)

st.markdown("---")
st.caption(f"更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
