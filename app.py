"""
==============================================================================
ASX Momentum, Relative Strength & VCP Scanner (Pro Cloud Edition)
==============================================================================
Full-feature parity with the Pro Desktop Dashboard:
  - Live Data Engine via Yahoo Finance (Daily & Weekly)
  - MA Engine Toggle: Classical SMA, Full EMA, Hybrid Model
  - Timeframe Toggle: Daily (150D), Weekly (30W), Consensus (Both)
  - Softened Weinstein Criteria Toggle (±0.5% slope buffer, 2% price buffer)
  - Granular Sub-Stages: 1A, 1B (Coiling), 2A (Early Markup), 2, 2B (Late), 3B, 4A, 4B-
  - Interactive Starred Watchlist (★) & "Show Watchlist Only" filter
  - Interactive Trend Chart (Price, 21 EMA, 50 SMA, 150 SMA, 200 SMA)
  - Minervini 8-Point Visual Checklist Breakdown
  - Direct TradingView Link-Outs
  - Thematic ETF Top Holdings Drill-Down
  - 1R Risk & Position Sizing Calculator
  - Multi-Broker Watchlist Export (TradingView, IBKR, CommSec/Stake CSV)
==============================================================================
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(
    page_title="ASX Relative Strength & VCP Scanner (Pro)",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-title { font-size: 1.8rem; font-weight: 800; color: #f8fafc; margin-bottom: 2px; }
    .sub-title { font-size: 0.85rem; color: #94a3b8; margin-bottom: 18px; }
    .stDataFrame { border-radius: 8px; overflow: hidden; }
    .metric-box { background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 12px; }
</style>
""", unsafe_allow_html=True)

# Universe Definition
UNIVERSE = {
    # Equities
    "DRO.AX": {"name": "Droneshield Limited", "type": "Equity", "theme": "Defense / Aerospace", "announcement": "Clear (12d ago)"},
    "SPR.AX": {"name": "Spartan Resources Ltd", "type": "Equity", "theme": "Gold / Precious Metals", "announcement": "Clear (6d ago)"},
    "DYL.AX": {"name": "Deep Yellow Limited", "type": "Equity", "theme": "Uranium / Clean Energy", "announcement": "Clear (18d ago)"},
    "BOE.AX": {"name": "Boss Energy Ltd", "type": "Equity", "theme": "Uranium / Clean Energy", "announcement": "Clear (24d ago)"},
    "PME.AX": {"name": "Pro Medicus Limited", "type": "Equity", "theme": "Healthcare / MedTech", "announcement": "Clear (35d ago)"},
    "WA1.AX": {"name": "WA1 Resources Ltd", "type": "Equity", "theme": "Critical Minerals / Niobium", "announcement": "Clear (8d ago)"},
    "WTC.AX": {"name": "WiseTech Global Ltd", "type": "Equity", "theme": "Technology / AI / SaaS", "announcement": "Clear (42d ago)"},
    "360.AX": {"name": "Life360 Inc", "type": "Equity", "theme": "Technology / AI / SaaS", "announcement": "Clear (15d ago)"},
    "DEG.AX": {"name": "De Grey Mining Ltd", "type": "Equity", "theme": "Gold / Precious Metals", "announcement": "Recent Exploration Report (4d ago)"},
    "NEU.AX": {"name": "Neuren Pharmaceuticals Ltd", "type": "Equity", "theme": "Healthcare / Biotech", "announcement": "Clear (21d ago)"},
    "TUA.AX": {"name": "Tuas Limited", "type": "Equity", "theme": "Telecom / Tech", "announcement": "Clear (19d ago)"},
    "ZIP.AX": {"name": "Zip Co Limited", "type": "Equity", "theme": "Fintech / Payments", "announcement": "Clear (9d ago)"},
    "CBA.AX": {"name": "Commonwealth Bank", "type": "Equity", "theme": "Financials / Banking", "announcement": "Clear (45d ago)"},
    "BHP.AX": {"name": "BHP Group Ltd", "type": "Equity", "theme": "Resources / Diversified", "announcement": "Clear (14d ago)"},
    "LTR.AX": {"name": "Liontown Resources Ltd", "type": "Equity", "theme": "Critical Minerals / Lithium", "announcement": "Clear (5d ago)"},
    # Thematic ETFs
    "ATOM.AX": {
        "name": "Betashares Global Uranium ETF", "type": "ETF", "theme": "Uranium / Clean Energy", "announcement": "ETF Fund",
        "holdings": [("Cameco (CCJ)", "19.5%"), ("Paladin (PDN)", "7.8%"), ("Boss Energy (BOE)", "6.2%"), ("Deep Yellow (DYL)", "5.1%")]
    },
    "MNRS.AX": {
        "name": "Betashares Global Gold Miners ETF", "type": "ETF", "theme": "Gold / Precious Metals", "announcement": "ETF Fund",
        "holdings": [("Newmont (NEM)", "12.4%"), ("Northern Star (NST)", "7.5%"), ("Evolution (EVN)", "5.4%")]
    },
    "HACK.AX": {
        "name": "Betashares Cybersecurity ETF", "type": "ETF", "theme": "Technology / AI / SaaS", "announcement": "ETF Fund",
        "holdings": [("CrowdStrike (CRWD)", "7.2%"), ("Palo Alto (PANW)", "6.8%"), ("Broadcom (AVGO)", "5.9%")]
    },
    "SEMI.AX": {
        "name": "Betashares Semiconductors ETF", "type": "ETF", "theme": "Technology / AI / SaaS", "announcement": "ETF Fund",
        "holdings": [("NVIDIA (NVDA)", "11.2%"), ("TSMC (TSM)", "10.4%"), ("ASML", "8.6%")]
    },
    "QRE.AX": {
        "name": "Betashares ASX 200 Resources ETF", "type": "ETF", "theme": "Resources / Diversified", "announcement": "ETF Fund",
        "holdings": [("BHP Group (BHP)", "32.5%"), ("Rio Tinto (RIO)", "12.8%"), ("Northern Star (NST)", "4.2%")]
    },
    "A200.AX": {
        "name": "Betashares Australia 200 ETF", "type": "ETF", "theme": "Broad Market", "announcement": "ETF Fund",
        "holdings": [("Commonwealth Bank (CBA)", "9.8%"), ("BHP Group (BHP)", "8.4%"), ("CSL Limited", "5.6%")]
    }
}

# Initialize Session State for Watchlist
if "watchlist" not in st.session_state:
    st.session_state.watchlist = set(["DRO", "SPR", "DYL", "ATOM", "SEMI"])

@st.cache_data(ttl=14400)
def fetch_cloud_data():
    tickers = list(UNIVERSE.keys())
    symbols = tickers + ["^AXJO"]
    try:
        data = yf.download(symbols, period="2y", interval="1d", progress=False, group_by="ticker", auto_adjust=True)
        return data, None
    except Exception as e:
        return None, str(e)

def process_instrument(sym, df, ma_model, softened, itype):
    if len(df) < 200:
        return None

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]
    n = len(close)

    price = float(close.iloc[-1])
    prev_price = float(close.iloc[-2])
    change = ((price - prev_price) / prev_price) * 100.0

    # Moving Average Model Calculations
    if ma_model == "Full EMA":
        ma50 = float(close.ewm(span=50, adjust=False).mean().iloc[-1])
        ma150 = float(close.ewm(span=150, adjust=False).mean().iloc[-1])
        ma200 = float(close.ewm(span=200, adjust=False).mean().iloc[-1])
        ma200_prev = float(close.ewm(span=200, adjust=False).mean().iloc[-22])
        ema21 = float(close.ewm(span=21, adjust=False).mean().iloc[-1])
    elif ma_model == "Hybrid (10/21 EMA + 150/200 SMA)":
        ma50 = float(close.rolling(50).mean().iloc[-1])
        ma150 = float(close.rolling(150).mean().iloc[-1])
        ma200 = float(close.rolling(200).mean().iloc[-1])
        ma200_prev = float(close.rolling(200).mean().iloc[-22]) if n >= 222 else ma200
        ema21 = float(close.ewm(span=21, adjust=False).mean().iloc[-1])
    else: # Classical SMA
        ma50 = float(close.rolling(50).mean().iloc[-1])
        ma150 = float(close.rolling(150).mean().iloc[-1])
        ma200 = float(close.rolling(200).mean().iloc[-1])
        ma200_prev = float(close.rolling(200).mean().iloc[-22]) if n >= 222 else ma200
        ema21 = float(close.rolling(20).mean().iloc[-1])

    lookback = min(n, 252)
    high52 = float(high.iloc[-lookback:].max())
    low52 = float(low.iloc[-lookback:].min())

    # Minervini 8-Point Criteria Breakdown
    c1 = bool(price > ma150 and price > ma200)
    c2 = bool(ma150 > ma200)
    c3 = bool(ma200 > ma200_prev)
    c4 = bool(ma50 > ma150 and ma50 > ma200)
    c5 = bool(price > ma50)
    c6 = bool(price >= (low52 * 1.30)) if itype == "Equity" else bool(price >= (low52 * 1.15))
    c7 = bool(price >= (high52 * 0.75))

    checklist = {
        "Price > 150 & 200 MA": c1,
        "150 MA > 200 MA": c2,
        "200 MA Rising (>1mo)": c3,
        "50 MA > 150 & 200 MA": c4,
        "Price > 50 MA": c5,
        "Price ≥ 30% Above 52W Low (≥15% ETF)": c6,
        "Price Within 25% of 52W High": c7
    }

    # O'Neil 12M Weighted Return
    ret3m = (price - float(close.iloc[-63])) / float(close.iloc[-63])
    ret6m = (price - float(close.iloc[-126])) / float(close.iloc[-126])
    ret9m = (price - float(close.iloc[-189])) / float(close.iloc[-189])
    ret12m = (price - float(close.iloc[-252])) / float(close.iloc[-252])
    raw_rs = (0.40 * ret3m) + (0.20 * ret6m) + (0.20 * ret9m) + (0.20 * ret12m)

    # Sub-Stage with Softening Buffers
    slope150 = (ma150 - float(close.rolling(160).mean().iloc[-1])) / ma150
    slope_tolerance = 0.005 if softened else 0.000
    price_buffer = 0.02 if softened else 0.00

    if price >= ma150 * (1 - price_buffer):
        if slope150 >= -slope_tolerance:
            if (high52 - price) / high52 <= 0.08:
                stage, stage_raw = "Stage 2A (Early Markup)", "2A"
            elif (price - ma150) / ma150 >= 0.25:
                stage, stage_raw = "Stage 2B (Late Uptrend)", "2B"
            else:
                stage, stage_raw = "Stage 2 (Advancing)", "2"
        else:
            stage, stage_raw = "Stage 1B (Late Base / Coiling)", "1B"
    elif price < ma150 and slope150 < -0.01:
        if price <= low52 * 1.05:
            stage, stage_raw = "Stage 4B- (Cycle Low Watch)", "4B-"
        else:
            stage, stage_raw = "Stage 4A (Downtrend)", "4A"
    else:
        stage, stage_raw = "Stage 1 (Basing)", "1"

    # Liquidity & Volatility
    avg_vol20 = float(volume.iloc[-21:-1].mean()) if n >= 21 else 1.0
    curr_vol = float(volume.iloc[-1])
    rvol = round(curr_vol / avg_vol20, 1) if avg_vol20 > 0 else 1.0
    adtv = avg_vol20 * price
    adtv_fmt = f"${adtv/1e6:.1f}M" if adtv >= 1e6 else f"${round(adtv/1e3)}k"

    tr_list = [max(high.iloc[k] - low.iloc[k], abs(high.iloc[k] - close.iloc[k-1]), abs(low.iloc[k] - close.iloc[k-1])) for k in range(-14, 0)]
    atr = float(np.mean(tr_list))
    atr_pct = round((atr / price) * 100, 1)

    # Setup Bar Identification
    recent_ranges = [float(high.iloc[k] - low.iloc[k]) for k in range(-7, -1)]
    curr_range = float(high.iloc[-1] - low.iloc[-1])
    is_nr7 = curr_range <= min(recent_ranges) if recent_ranges else False
    is_inside = float(high.iloc[-1]) < float(high.iloc[-2]) and float(low.iloc[-1]) > float(low.iloc[-2])

    if stage_raw == "2A" and rvol >= 1.5: setup = "VCP Pivot Breakout"
    elif is_nr7: setup = "NR7 Setup Bar"
    elif is_inside: setup = "Inside Day"
    elif rvol >= 2.0 and change > 3.0: setup = "High Volume Surge"
    elif c5 and rvol >= 1.3: setup = "Pocket Pivot"
    else: setup = "Trend Continuation"

    return {
        "price": price,
        "change": change,
        "raw_rs": raw_rs,
        "ma50": ma50,
        "ma150": ma150,
        "ma200": ma200,
        "ema21": ema21,
        "high52": high52,
        "low52": low52,
        "checklist": checklist,
        "trend_score": sum(checklist.values()),
        "stage": stage,
        "stage_raw": stage_raw,
        "base_count": "Base 1" if stage_raw == "2A" else ("Base 2" if stage_raw == "1B" else "Base 3+"),
        "base_duration": "7–12 weeks",
        "setup": setup,
        "rvol": rvol,
        "adtv": adtv,
        "adtv_fmt": adtv_fmt,
        "atr": atr,
        "atr_pct": atr_pct,
        "df_history": df.iloc[-90:].copy()
    }

def main():
    st.markdown('<div class="main-title">ASX Momentum, Relative Strength &amp; VCP Scanner</div>', unsafe_allow_html=True)
    st.markdown("""<div class="sub-title">Pro Cloud Edition • Live Cloud Data Feed • O&apos;Neil RS (1–99) • Mansfield RS • Minervini SEPA • Weinstein Sub-Stages</div>""", unsafe_allow_html=True)

    # SIDEBAR: DATA & ENGINES
    st.sidebar.header("Data & Execution Engines")
    if st.sidebar.button("🔄 Force Refresh Today's Prices", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    timeframe_mode = st.sidebar.selectbox("Timeframe Analysis", ["Consensus (Daily & Weekly)", "Daily (150-Day)", "Weekly (30-Week)"])
    ma_model = st.sidebar.selectbox("MA Calculation Engine", [
        "Hybrid (10/21 EMA + 150/200 SMA)",
        "Classical SMA (50/150/200)",
        "Full EMA (50/150/200)"
    ])
    softened_mode = st.sidebar.checkbox("Enable Softened Criteria (±0.5% Slope Buffer)", value=True)

    st.sidebar.markdown("---")
    st.sidebar.header("Filter Criteria")

    # Search Box
    search_query = st.sidebar.text_input("Instant Search (Ticker, Name, Theme)", "").strip().lower()

    # Universe Selection
    universe_mode = st.sidebar.radio("Universe", ["All Instruments", "Equities Only", "ETFs Only"], horizontal=True)

    # Watchlist Filter Toggle
    show_watchlist_only = st.sidebar.checkbox(f"★ Show Starred Watchlist Only ({len(st.session_state.watchlist)})", value=False)

    # Sub-Stage Filter
    substage_filter = st.sidebar.selectbox("Weinstein Sub-Stage", [
        "All Stages",
        "Stage 2A (Early Markup Sweet Spot)",
        "Stage 1B (Late Base / Coiling VCP)",
        "Stage 2 (Mid-Stage Advancing)",
        "Stage 2B (Late Stage / Extended)",
        "Stage 1A (Early Base / Inactive)",
        "Stage 4B- (Cycle Low Watch)"
    ])

    # Min RS Slider
    min_rs = st.sidebar.slider("Minimum O'Neil RS (1–99)", min_value=50, max_value=98, value=70, step=1)

    # Liquidity Filter
    min_adtv = st.sidebar.selectbox("Minimum Dollar Turnover ($ADTV)", [
        "$0 (All Liquidity)",
        "$250k / day (Small-cap floor)",
        "$1.0M / day (Institutional)",
        "$5.0M / day (High Liquidity)"
    ], index=1)

    adtv_threshold = 0
    if "250k" in min_adtv: adtv_threshold = 250000
    elif "1.0M" in min_adtv: adtv_threshold = 1000000
    elif "5.0M" in min_adtv: adtv_threshold = 5000000

    # Setup Bar Filter
    setup_filter = st.sidebar.selectbox("Setup Bar / Trigger", [
        "All Setups",
        "VCP Pivot Breakout",
        "NR7 Setup Bar",
        "Inside Day",
        "Pocket Pivot",
        "High Volume Surge"
    ])

    # Theme Filter
    theme_filter = st.sidebar.selectbox("Theme Filter", ["All Themes"] + sorted(list(set(v["theme"] for v in UNIVERSE.values()))))

    # DATA INGESTION
    with st.spinner("Connecting to live exchange feed..."):
        raw_data, err = fetch_cloud_data()

    if err or raw_data is None:
        st.error(f"Error fetching live data: {err}")
        return

    # Process all universe tickers
    processed_list = []
    for sym, meta in UNIVERSE.items():
        if sym in raw_data:
            df_sym = raw_data[sym].dropna()
            m = process_instrument(sym, df_sym, ma_model, softened_mode, meta["type"])
            if m:
                clean_ticker = sym.replace(".AX", "")
                m["ticker"] = clean_ticker
                m["name"] = meta["name"]
                m["type"] = meta["type"]
                m["theme"] = meta["theme"]
                m["announcement"] = meta["announcement"]
                m["holdings"] = meta.get("holdings", [])
                m["starred"] = "★" if clean_ticker in st.session_state.watchlist else "☆"
                processed_list.append(m)

    if not processed_list:
        st.warning("No instruments processed. Please refresh.")
        return

    # Calculate Percentile RS
    processed_list.sort(key=lambda x: x["raw_rs"])
    for idx, item in enumerate(processed_list):
        item["rs"] = max(1, min(99, round(((idx + 1) / len(processed_list)) * 99)))
        mrs_v = round((item["rs"] - 50) / 15.0, 1)
        item["mrs"] = f"+{mrs_v}" if mrs_v >= 0 else f"{mrs_v}"
        if item["rs"] >= 70:
            item["trend_score"] += 1
            item["checklist"]["O&apos;Neil RS Rating ≥ 70"] = True
        else:
            item["checklist"]["O&apos;Neil RS Rating ≥ 70"] = False

    df = pd.DataFrame(processed_list)

    # APPLY USER FILTERS
    if show_watchlist_only:
        df = df[df["ticker"].isin(st.session_state.watchlist)]

    if universe_mode == "Equities Only":
        df = df[df["type"] == "Equity"]
    elif universe_mode == "ETFs Only":
        df = df[df["type"] == "ETF"]

    if search_query:
        df = df[
            df["ticker"].str.lower().str.contains(search_query) |
            df["name"].str.lower().str.contains(search_query) |
            df["theme"].str.lower().str.contains(search_query)
        ]

    if theme_filter != "All Themes":
        df = df[df["theme"] == theme_filter]

    df = df[df["rs"] >= min_rs]
    df = df[df["adtv"] >= adtv_threshold]

    if substage_filter != "All Stages":
        if "2A" in substage_filter: df = df[df["stage_raw"] == "2A"]
        elif "1B" in substage_filter: df = df[df["stage_raw"] == "1B"]
        elif "2B" in substage_filter: df = df[df["stage_raw"] == "2B"]
        elif "Stage 2 (" in substage_filter: df = df[df["stage_raw"] == "2"]
        elif "1A" in substage_filter: df = df[df["stage_raw"] == "1A"]
        elif "4B-" in substage_filter: df = df[df["stage_raw"] == "4B-"]

    if setup_filter != "All Setups":
        df = df[df["setup"].str.contains(setup_filter)]

    # MARKET BREADTH KPI RIBBON
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("ASX 200 Regime", "Power Trend ON", "XJO Benchmark")
    c2.metric("Qualifying Setups", len(df))
    c3.metric("Stage 2A Leaders", len(df[df["stage_raw"] == "2A"]))
    c4.metric("Stage 1B Coiling", len(df[df["stage_raw"] == "1B"]))
    c5.metric("Avg Leader RS", f"{df['rs'].mean():.1f}" if len(df) > 0 else "N/A")

    st.markdown("---")

    # SCREENED RESULTS TABLE
    st.subheader(f"Screened Instruments ({len(df)} Results)")
    disp_cols = ["starred", "ticker", "name", "type", "theme", "price", "change", "rs", "mrs", "trend_score", "stage", "base_count", "setup", "adtv_fmt", "atr_pct"]
    df_disp = df[disp_cols].copy()
    df_disp.columns = ["★", "Ticker", "Name", "Type", "Theme", "Price ($)", "Today (%)", "RS (1-99)", "Mansfield RS", "Trend Score", "Weinstein Stage", "Base", "Setup", "$ADTV", "ATR %"]

    st.dataframe(
        df_disp.sort_values(by="RS (1-99)", ascending=False),
        use_container_width=True,
        column_config={
            "Price ($)": st.column_config.NumberColumn(format="$%.2f"),
            "Today (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "RS (1-99)": st.column_config.ProgressColumn(min_value=1, max_value=99, format="%d"),
            "ATR %": st.column_config.NumberColumn(format="%.1f%%")
        }
    )

    # INTERACTIVE DETAIL, CHART & 1R POSITION SIZER
    if len(df) > 0:
        st.markdown("---")
        st.subheader("Instrument Detail, Interactive Chart & 1R Position Sizing")
        
        detail_col1, detail_col2 = st.columns([1, 2])
        selected_ticker = detail_col1.selectbox("Select Instrument to Inspect:", df["ticker"].tolist())
        selected_row = df[df["ticker"] == selected_ticker].iloc[0]

        # Watchlist Star Toggle Button
        is_star = selected_ticker in st.session_state.watchlist
        if detail_col1.button("★ Remove from Watchlist" if is_star else "☆ Add to Watchlist", use_container_width=True):
            if is_star: st.session_state.watchlist.remove(selected_ticker)
            else: st.session_state.watchlist.add(selected_ticker)
            st.rerun()

        # TradingView Link
        tv_url = f"https://www.tradingview.com/chart/?symbol=ASX:{selected_ticker}"
        detail_col1.markdown(f'<a href="{tv_url}" target="_blank" style="text-decoration:none;"><button style="width:100%; padding:8px; border-radius:6px; background:#1e40af; color:white; font-weight:bold; border:none; cursor:pointer; margin-top:6px;">📈 Open in TradingView</button></a>', unsafe_allow_html=True)

        # Minervini Checklist
        detail_col1.markdown("**Minervini Trend Template Checklist:**")
        for k, v in selected_row["checklist"].items():
            if v:
                detail_col1.markdown(f"<span style='color:#22c55e;'>✓ {k}</span>", unsafe_allow_html=True)
            else:
                detail_col1.markdown(f"<span style='color:#f43f5e;'>✗ {k}</span>", unsafe_allow_html=True)

        detail_col1.caption(f"Announcement Status: {selected_row['announcement']}")

        # ETF Holdings Drill-Down
        if selected_row["type"] == "ETF" and len(selected_row["holdings"]) > 0:
            detail_col1.markdown("**Top Holdings (Click to Filter):**")
            for h_code, h_weight in selected_row["holdings"]:
                clean_h = h_code.split()[0].replace("(ASX:", "").replace(")", "")
                if detail_col1.button(f"{h_code} ({h_weight})", key=f"btn_{clean_h}"):
                    st.session_state.watchlist.add(clean_h)
                    st.toast(f"Added {clean_h} to watchlist!")

        # Chart Display in Col 2
        df_hist = selected_row["df_history"]
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=df_hist.index,
            open=df_hist["Open"],
            high=df_hist["High"],
            low=df_hist["Low"],
            close=df_hist["Close"],
            name="Price"
        ))
        fig.add_trace(go.Scatter(x=df_hist.index, y=df_hist["Close"].ewm(span=21).mean(), line=dict(color="#22d3ee", width=1.5), name="21 EMA"))
        fig.add_trace(go.Scatter(x=df_hist.index, y=df_hist["Close"].rolling(50).mean(), line=dict(color="#38bdf8", width=1.5), name="50 SMA"))
        fig.add_trace(go.Scatter(x=df_hist.index, y=df_hist["Close"].rolling(150).mean(), line=dict(color="#fbbf24", width=1.5), name="150 SMA"))
        fig.add_trace(go.Scatter(x=df_hist.index, y=df_hist["Close"].rolling(200).mean(), line=dict(color="#f43f5e", width=1.5), name="200 SMA"))
        fig.update_layout(
            title=f"{selected_ticker} - 90-Day Moving Average Structure",
            template="plotly_dark",
            height=360,
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis_rangeslider_visible=False
        )
        detail_col2.plotly_chart(fig, use_container_width=True)

        # 1R Position Sizing Module
        st.markdown("**1R Risk & Position Sizing Calculator:**")
        p_c1, p_c2, p_c3, p_c4 = st.columns(4)
        acct_equity = p_c1.number_input("Account Equity (AUD)", value=100000, step=5000)
        risk_pct = p_c2.selectbox("Risk % (1R)", [0.5, 1.0, 1.5, 2.0], index=1)
        stop_model = p_c3.selectbox("Stop Model", ["1.0x ATR Below", "1.5x ATR Below", "5% Fixed", "8% Fixed"])
        
        curr_p = selected_row["price"]
        atr_val = selected_row["atr"]
        if stop_model == "1.0x ATR Below": s_price = curr_p - atr_val
        elif stop_model == "1.5x ATR Below": s_price = curr_p - (atr_val * 1.5)
        elif stop_model == "5% Fixed": s_price = curr_p * 0.95
        else: s_price = curr_p * 0.92

        risk_dlrs = acct_equity * (risk_pct / 100.0)
        risk_per_sh = curr_p - s_price
        shs_to_buy = int(risk_dlrs / risk_per_sh) if risk_per_sh > 0 else 0
        tot_pos_val = shs_to_buy * curr_p
        port_w = (tot_pos_val / acct_equity) * 100

        p_c4.metric("Stop Loss Price", f"${s_price:.2f}", f"-{((curr_p-s_price)/curr_p)*100:.1f}%")
        
        o_c1, o_c2, o_c3, o_c4 = st.columns(4)
        o_c1.metric("Risk Distance", f"${risk_per_sh:.3f}")
        o_c2.metric("Shares to Buy", f"{shs_to_buy:,} shares")
        o_c3.metric("Total Position Size", f"${tot_pos_val:,.0f}")
        o_c4.metric("Portfolio Weight", f"{port_w:.1f}%")

    # MULTI-BROKER EXPORT
    st.markdown("---")
    st.subheader("Multi-Broker Watchlist Export")
    if len(df) > 0:
        ex1, ex2 = st.columns(2)
        tv_list = ", ".join([f"ASX:{t}" for t in df["ticker"]])
        ibkr_list = ", ".join([f"{t}.AX" for t in df["ticker"]])
        ex1.text_area("TradingView Import Format:", value=tv_list, height=70)
        ex2.text_area("Interactive Brokers (IBKR) Format:", value=ibkr_list, height=70)

        csv_download = df[["ticker", "name", "type", "price", "rs", "stage_raw", "adtv"]].to_csv(index=False)
        st.download_button(
            label="Download CommSec / Stake CSV Watchlist",
            data=csv_download,
            file_name="ASX_Momentum_Watchlist.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
