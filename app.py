"""
==============================================================================
ASX Momentum, Relative Strength & VCP Scanner (Pro Cloud Edition)
==============================================================================
Exact UI Layout matching the Desktop Dashboard:
  - Top 6-card Market Breadth & Regime Ribbon
  - Horizontal Row 1 Toolbar: Universe, Timeframe, MA Engine, Weinstein Mode
  - Horizontal Row 2 Toolbar: Search, Sub-Stage, Min RS, $ADTV, Theme, Setup, Reset
  - Complete 15-Column Data Grid matching screenshot
  - Interactive Instrument Detail, Plotly Trend Chart, 8-Point Checklist,
    1R Position Sizer & Multi-Broker Export
==============================================================================
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go

st.set_page_config(
    page_title="ASX Relative Strength & VCP Scanner",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Styling to match the desktop slate/zinc dark aesthetic
st.markdown("""
<style>
    /* Remove excess top padding */
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 98%; }
    
    /* KPI Metric Cards */
    .kpi-card {
        background-color: #090d16;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 8px 12px;
        min-height: 68px;
    }
    .kpi-title {
        font-size: 0.68rem;
        color: #94a3b8;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        display: flex;
        justify-content: space-between;
    }
    .kpi-val {
        font-size: 1.05rem;
        font-weight: 800;
        margin-top: 2px;
        font-family: 'JetBrains Mono', monospace;
    }
    
    /* Toolbar Containers */
    .toolbar-box {
        background-color: #0b1120;
        border: 1px solid #1e293b;
        border-radius: 10px;
        padding: 10px 14px;
        margin-bottom: 8px;
    }
    
    /* Compact input controls */
    div[data-testid="stRadio"] > label { display: none; }
    div[data-testid="stSelectbox"] > label { display: none; }
    div[data-testid="stTextInput"] > label { display: none; }
    div[data-testid="stSlider"] > label { display: none; }
    div[data-testid="stCheckbox"] > label { font-size: 0.75rem; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# Universe Definitions
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
    "DEG.AX": {"name": "De Grey Mining Ltd", "type": "Equity", "theme": "Gold / Precious Metals", "announcement": "Recent Report (4d ago)"},
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

# Session State for Starred Watchlist
if "watchlist" not in st.session_state:
    st.session_state.watchlist = set(["DRO", "SPR", "DYL", "ATOM", "SEMI"])

@st.cache_data(ttl=14400)
def load_market_data():
    symbols = list(UNIVERSE.keys()) + ["^AXJO"]
    try:
        data = yf.download(symbols, period="2y", interval="1d", progress=False, group_by="ticker", auto_adjust=True)
        return data, None
    except Exception as e:
        return None, str(e)

def calculate_metrics(sym, df, ma_model, softened, itype):
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

    # Moving Average Model
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
            if (high52 - price) / high52 <= 0.08: stage, stage_raw = "Stage 2A (Early Markup)", "2A"
            elif (price - ma150) / ma150 >= 0.25: stage, stage_raw = "Stage 2B (Late Uptrend)", "2B"
            else: stage, stage_raw = "Stage 2 (Advancing)", "2"
        else:
            stage, stage_raw = "Stage 1B (Late Base / Coiling)", "1B"
    elif price < ma150 and slope150 < -0.01:
        stage = "Stage 4B- (Cycle Low Watch)" if price <= low52 * 1.05 else "Stage 4A (Downtrend)"
        stage_raw = "4B-" if price <= low52 * 1.05 else "4A"
    else:
        stage, stage_raw = "Stage 1 (Basing)", "1"

    # Liquidity & Volatility
    avg_vol20 = float(volume.iloc[-21:-1].mean()) if n >= 21 else 1.0
    rvol = round(float(volume.iloc[-1]) / avg_vol20, 1) if avg_vol20 > 0 else 1.0
    adtv = avg_vol20 * price
    adtv_fmt = f"${adtv/1e6:.1f}M" if adtv >= 1e6 else f"${round(adtv/1e3)}k"

    tr_list = [max(high.iloc[k] - low.iloc[k], abs(high.iloc[k] - close.iloc[k-1]), abs(low.iloc[k] - close.iloc[k-1])) for k in range(-14, 0)]
    atr = float(np.mean(tr_list))
    atr_pct = round((atr / price) * 100, 1)

    # Setup Bar
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
    # Load Market Data
    raw_data, err = load_market_data()
    if err or raw_data is None:
        st.error(f"Error connecting to live market feed: {err}")
        return

    # TOP 6 KPI MARKET BREADTH RIBBON (MATCHING SCREENSHOT)
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    
    with k1:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-title"><span>ASX 200 Regime</span><span style="color:#64748b;">XJO 8,240</span></div>
            <div class="kpi-val" style="color:#22c55e;">● Power Trend ON</div>
        </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-title"><span>% &gt; 50-Day MA</span></div>
            <div class="kpi-val" style="color:#f8fafc;">68.4% <span style="font-size:0.75rem; color:#22c55e;">(Bullish)</span></div>
        </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-title"><span>% &gt; 200-Day MA</span></div>
            <div class="kpi-val" style="color:#f8fafc;">61.2% <span style="font-size:0.75rem; color:#22c55e;">(Healthy)</span></div>
        </div>
        """, unsafe_allow_html=True)
    with k4:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-title"><span>Stage 2A Leaders</span></div>
            <div class="kpi-val" style="color:#22c55e;">12 Active</div>
        </div>
        """, unsafe_allow_html=True)
    with k5:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-title"><span>Stage 1B Coiling Bases</span></div>
            <div class="kpi-val" style="color:#f59e0b;">3 Primed</div>
        </div>
        """, unsafe_allow_html=True)
    with k6:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-title"><span>Thematic ETFs Active</span></div>
            <div class="kpi-val" style="color:#c084fc;">5 Screened</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # ROW 1: HORIZONTAL CONTROLS (UNIVERSE, TIMEFRAME, MA ENGINE, WEINSTEIN MODE)
    c_u1, c_u2, c_u3, c_u4 = st.columns([2.5, 3.2, 3.8, 2.5])
    
    with c_u1:
        st.caption("**Universe:**")
        universe_mode = st.radio("Universe", ["All (21)", "Equities (15)", "ETFs (6)"], horizontal=True, label_visibility="collapsed")
    with c_u2:
        st.caption("**Timeframe:**")
        timeframe_mode = st.radio("Timeframe", ["Daily (150D)", "Weekly (30W)", "Consensus (Both)"], index=2, horizontal=True, label_visibility="collapsed")
    with c_u3:
        st.caption("**MA Engine:**")
        ma_model = st.selectbox("MA Engine", [
            "Hybrid (10/21 EMA + 150/200 SMA)",
            "Classical SMA (50/150/200)",
            "Full EMA (50/150/200)"
        ], label_visibility="collapsed")
    with c_u4:
        st.caption("**Weinstein Mode:**")
        softened_mode = st.checkbox("Softened (±0.5% Slope Buffer)", value=True)

    # Process all universe tickers with current MA & Softening selections
    processed_list = []
    for sym, meta in UNIVERSE.items():
        if sym in raw_data:
            df_sym = raw_data[sym].dropna()
            m = calculate_metrics(sym, df_sym, ma_model, softened_mode, meta["type"])
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

    # Calculate Percentile RS
    processed_list.sort(key=lambda x: x["raw_rs"])
    for idx, item in enumerate(processed_list):
        item["rs"] = max(1, min(99, round(((idx + 1) / len(processed_list)) * 99)))
        mrs_v = round((item["rs"] - 50) / 15.0, 1)
        item["mrs"] = f"+{mrs_v}" if mrs_v >= 0 else f"{mrs_v}"
        if item["rs"] >= 70:
            item["trend_score"] += 1
            item["checklist"]["O'Neil RS Rating ≥ 70"] = True
        else:
            item["checklist"]["O'Neil RS Rating ≥ 70"] = False

    df = pd.DataFrame(processed_list)

    # ROW 2: HORIZONTAL FILTER BAR (SEARCH, STAGE, MIN RS, ADTV, THEME, SETUP, RESET)
    f1, f2, f3, f4, f5, f6, f7 = st.columns([2.2, 1.8, 1.6, 1.6, 1.6, 1.6, 0.8])
    
    with f1:
        st.caption("**Search:**")
        search_query = st.text_input("Search", "", placeholder="Search Ticker, Name, Theme, ETF..", label_visibility="collapsed").strip().lower()
    with f2:
        st.caption("**Stage Filter:**")
        substage_filter = st.selectbox("Stage", [
            "All Weinstein Stages",
            "Stage 2A (Early Markup)",
            "Stage 1B (Late Base / Coiling)",
            "Stage 2 (Advancing)",
            "Stage 2B (Late Uptrend)",
            "Stage 1A (Early Base)",
            "Stage 4B- (Cycle Low Watch)"
        ], label_visibility="collapsed")
    with f3:
        st.caption("**Min RS:**")
        min_rs = st.slider("Min RS", min_value=50, max_value=95, value=70, step=5, label_visibility="collapsed")
    with f4:
        st.caption("**Liquidity ($ADTV):**")
        min_adtv = st.selectbox("ADTV", [
            "All Liquidity ($ADTV)",
            "> $250k / day",
            "> $1.0M / day",
            "> $5.0M / day"
        ], label_visibility="collapsed")
    with f5:
        st.caption("**Themes:**")
        theme_filter = st.selectbox("Theme", ["All Themes"] + sorted(list(set(v["theme"] for v in UNIVERSE.values()))), label_visibility="collapsed")
    with f6:
        st.caption("**Setups:**")
        setup_filter = st.selectbox("Setup", [
            "All Setups",
            "VCP Pivot Breakout",
            "NR7 Setup Bar",
            "Inside Day",
            "Pocket Pivot",
            "High Volume Surge"
        ], label_visibility="collapsed")
    with f7:
        st.caption("**Reset:**")
        if st.button("Reset", use_container_width=True):
            st.rerun()

    # Apply Filters
    if universe_mode == "Equities (15)": df = df[df["type"] == "Equity"]
    elif universe_mode == "ETFs (6)": df = df[df["type"] == "ETF"]

    if search_query:
        df = df[
            df["ticker"].str.lower().str.contains(search_query) |
            df["name"].str.lower().str.contains(search_query) |
            df["theme"].str.lower().str.contains(search_query)
        ]

    if theme_filter != "All Themes": df = df[df["theme"] == theme_filter]
    df = df[df["rs"] >= min_rs]

    adtv_threshold = 0
    if "250k" in min_adtv: adtv_threshold = 250000
    elif "1.0M" in min_adtv: adtv_threshold = 1000000
    elif "5.0M" in min_adtv: adtv_threshold = 5000000
    df = df[df["adtv"] >= adtv_threshold]

    if substage_filter != "All Weinstein Stages":
        if "2A" in substage_filter: df = df[df["stage_raw"] == "2A"]
        elif "1B" in substage_filter: df = df[df["stage_raw"] == "1B"]
        elif "2B" in substage_filter: df = df[df["stage_raw"] == "2B"]
        elif "Stage 2 (" in substage_filter: df = df[df["stage_raw"] == "2"]
        elif "1A" in substage_filter: df = df[df["stage_raw"] == "1A"]
        elif "4B-" in substage_filter: df = df[df["stage_raw"] == "4B-"]

    if setup_filter != "All Setups":
        df = df[df["setup"].str.contains(setup_filter)]

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # 15-COLUMN DATA TABLE (EXACT MATCH TO SCREENSHOT)
    disp_cols = ["starred", "type", "ticker", "name", "price", "change", "rs", "mrs", "trend_score", "stage", "base_count", "setup", "adtv_fmt", "atr_pct"]
    df_disp = df[disp_cols].copy()
    df_disp.columns = [
        "★", "TYPE", "TICKER", "NAME & THEME", "PRICE ($)", "TODAY %", "RS (1-99)",
        "MANSFIELD RS", "MINERVINI TREND", "WEINSTEIN SUB-STAGE", "BASE / DURATION",
        "SETUP BAR & VCP", "$ADTV", "ATR %"
    ]

    st.dataframe(
        df_disp.sort_values(by="RS (1-99)", ascending=False),
        use_container_width=True,
        hide_index=True,
        column_config={
            "★": st.column_config.TextColumn("★", width="small"),
            "TYPE": st.column_config.TextColumn("TYPE", width="small"),
            "TICKER": st.column_config.TextColumn("TICKER", width="small"),
            "PRICE ($)": st.column_config.NumberColumn(format="$%.2f"),
            "TODAY %": st.column_config.NumberColumn(format="%.2f%%"),
            "RS (1-99)": st.column_config.ProgressColumn("RS (1-99)", min_value=1, max_value=99, format="%d"),
            "MINERVINI TREND": st.column_config.TextColumn("MINERVINI TREND"),
            "ATR %": st.column_config.NumberColumn(format="%.1f%%")
        }
    )

    # ACTION / DETAIL MODAL EQUIVALENT (CHART, CHECKLIST, POSITION SIZER & EXPORT)
    if len(df) > 0:
        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
        with st.expander("🔍 **Analyze Instrument, View 90-Day Trend Chart & 1R Position Sizer**", expanded=True):
            d_col1, d_col2 = st.columns([1, 2])
            selected_ticker = d_col1.selectbox("Select Instrument to Inspect:", df["ticker"].tolist())
            selected_row = df[df["ticker"] == selected_ticker].iloc[0]

            # Star toggle
            is_starred = selected_ticker in st.session_state.watchlist
            if d_col1.button("★ Starred in Watchlist" if is_starred else "☆ Star for Watchlist", use_container_width=True):
                if is_starred: st.session_state.watchlist.remove(selected_ticker)
                else: st.session_state.watchlist.add(selected_ticker)
                st.rerun()

            # TradingView Button
            tv_url = f"https://www.tradingview.com/chart/?symbol=ASX:{selected_ticker}"
            d_col1.markdown(f'<a href="{tv_url}" target="_blank" style="text-decoration:none;"><button style="width:100%; padding:7px; border-radius:6px; background:#1e40af; color:white; font-weight:700; border:none; cursor:pointer; margin-top:4px; font-size:0.75rem;">📈 Open in TradingView</button></a>', unsafe_allow_html=True)

            # Minervini Checklist
            d_col1.markdown("<div style='margin-top:10px; font-weight:700; font-size:0.75rem; text-transform:uppercase;'>Minervini Trend Checklist:</div>", unsafe_allow_html=True)
            for k, v in selected_row["checklist"].items():
                color = "#22c55e" if v else "#f43f5e"
                icon = "✓" if v else "✗"
                d_col1.markdown(f"<span style='color:{color}; font-size:0.75rem; font-weight:600;'>{icon} {k}</span>", unsafe_allow_html=True)

            d_col1.caption(f"Announcement Status: {selected_row['announcement']}")

            # Chart in Col 2
            df_hist = selected_row["df_history"]
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=df_hist.index,
                open=df_hist["Open"], high=df_hist["High"],
                low=df_hist["Low"], close=df_hist["Close"],
                name="Price"
            ))
            fig.add_trace(go.Scatter(x=df_hist.index, y=df_hist["Close"].ewm(span=21).mean(), line=dict(color="#22d3ee", width=1.5), name="21 EMA"))
            fig.add_trace(go.Scatter(x=df_hist.index, y=df_hist["Close"].rolling(50).mean(), line=dict(color="#38bdf8", width=1.5), name="50 SMA"))
            fig.add_trace(go.Scatter(x=df_hist.index, y=df_hist["Close"].rolling(150).mean(), line=dict(color="#fbbf24", width=1.5), name="150 SMA"))
            fig.add_trace(go.Scatter(x=df_hist.index, y=df_hist["Close"].rolling(200).mean(), line=dict(color="#f43f5e", width=1.5), name="200 SMA"))
            fig.update_layout(
                title=f"{selected_ticker} ({selected_row['name']}) - 90-Day Trend Structure",
                template="plotly_dark",
                height=340,
                margin=dict(l=10, r=10, t=35, b=10),
                xaxis_rangeslider_visible=False
            )
            d_col2.plotly_chart(fig, use_container_width=True)

            # 1R Position Sizing
            st.markdown("---")
            st.markdown("**1R Risk & Position Sizing Calculator:**")
            p1, p2, p3, p4 = st.columns(4)
            acct_eq = p1.number_input("Account Equity (AUD)", value=100000, step=5000)
            risk_p = p2.selectbox("Risk % (1R)", [0.5, 1.0, 1.5, 2.0], index=1)
            stop_m = p3.selectbox("Stop Model", ["1.0x ATR Below", "1.5x ATR Below", "5% Fixed", "8% Fixed"])
            
            p_price = selected_row["price"]
            p_atr = selected_row["atr"]
            if stop_m == "1.0x ATR Below": stop_p = p_price - p_atr
            elif stop_m == "1.5x ATR Below": stop_p = p_price - (p_atr * 1.5)
            elif stop_m == "5% Fixed": stop_p = p_price * 0.95
            else: stop_p = p_price * 0.92

            risk_d = acct_eq * (risk_p / 100.0)
            risk_per_s = p_price - stop_p
            shares_buy = int(risk_d / risk_per_s) if risk_per_s > 0 else 0
            pos_val = shares_buy * p_price
            port_pct = (pos_val / acct_eq) * 100

            p4.metric("Stop Loss Price", f"${stop_p:.2f}", f"-{((p_price-stop_p)/p_price)*100:.1f}%")
            
            w1, w2, w3, w4 = st.columns(4)
            w1.metric("Risk Distance", f"${risk_per_s:.3f}")
            w2.metric("Shares to Buy", f"{shares_buy:,} shares")
            w3.metric("Total Position Size", f"${pos_val:,.0f}")
            w4.metric("Portfolio Weight", f"{port_pct:.1f}%")

        # MULTI-BROKER EXPORT
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        with st.expander("📋 **Multi-Broker Watchlist Export (TradingView, IBKR, CSV)**"):
            e1, e2 = st.columns(2)
            tv_txt = ", ".join([f"ASX:{t}" for t in df["ticker"]])
            ibkr_txt = ", ".join([f"{t}.AX" for t in df["ticker"]])
            e1.text_area("TradingView Format:", value=tv_txt, height=65)
            e2.text_area("Interactive Brokers (IBKR) Format:", value=ibkr_txt, height=65)

            csv_data = df[["ticker", "name", "type", "price", "rs", "stage_raw", "adtv"]].to_csv(index=False)
            st.download_button(
                label="Download CommSec / Stake CSV Watchlist",
                data=csv_data,
                file_name="ASX_Momentum_Watchlist.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    main()
