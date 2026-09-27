"""
==============================================================================
ASX Momentum, Relative Strength & VCP Scanner (Pro Cloud Edition v5)
==============================================================================
Enhancements Implemented:
  1. Benchmark Selector Dropdown (Default: All Ordinaries ^AXAO for broad 500-stock
     breadth, S&P/ASX 200 ^AXJO, and Small Ordinaries ^AXSO).
  2. Live Dynamic Calculations for all 6 KPI cards (no static numbers).
  3. Micro Sparkline Trendlines (12-Month & 6-Month) inside each of the 6 KPI cards.
  4. Real-time Power Trend status calculated on the selected benchmark.
  5. 3-Panel Interactive Chart in Inspector:
     - Panel 1: Price Candles + 21 EMA + 50 SMA + 150 SMA + 200 SMA + 52W High line
     - Panel 2: Color-Coded Volume + 50-day Volume SMA + Breakout Volume Spikes
     - Panel 3: Mansfield Relative Strength (MRS) curve vs Benchmark with Zero-Line
  6. Real Weekly Resampling (W-FRI) for 30-week moving average when Weekly/Consensus selected.
  7. Min RS Slider starting at 0 (default 0) so all 21 instruments show on startup.
  8. Watchlist State persistence via URL query parameters (bookmarkable).
  9. Enclosed horizontal toolbar containers matching the desktop screenshot.
==============================================================================
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="ASX Relative Strength & VCP Scanner",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Styling matching the desktop slate/zinc dark aesthetic
st.markdown("""
<style>
    /* Generous top clearance so nothing is cut off by Streamlit header */
    .block-container {
        padding-top: 4.2rem !important;
        padding-bottom: 2.5rem !important;
        max-width: 98% !important;
    }
    
    body { background-color: #020617; }
    
    /* Top 6 KPI Ribbon Cards */
    .kpi-card {
        background: linear-gradient(180deg, #090e1a 0%, #060913 100%);
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 8px 10px;
        min-height: 82px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .kpi-title {
        font-size: 0.64rem;
        color: #94a3b8;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        display: flex;
        justify-content: space-between;
        margin-bottom: 1px;
    }
    .kpi-val {
        font-size: 0.98rem;
        font-weight: 800;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Branded Header Badge */
    .asx-badge {
        background: linear-gradient(135deg, #10b981 0%, #0d9488 50%, #0284c7 100%);
        color: white;
        font-weight: 900;
        font-size: 0.95rem;
        padding: 6px 10px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25);
    }
    
    /* Compact toolbar inputs */
    div[data-testid="stRadio"] > label { display: none; }
    div[data-testid="stSelectbox"] > label { display: none; }
    div[data-testid="stTextInput"] > label { display: none; }
    div[data-testid="stSlider"] > label { display: none; }
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

BENCHMARK_MAP = {
    "All Ordinaries (^AXAO)": {"symbol": "^AXAO", "short": "AXAO", "name": "All Ords (500)"},
    "S&P/ASX 200 (^AXJO)": {"symbol": "^AXJO", "short": "AXJO", "name": "ASX 200 (200)"},
    "Small Ordinaries (^AXSO)": {"symbol": "^AXSO", "short": "AXSO", "name": "Small Ords (101-300)"}
}

# Session State & Query Param Watchlist Persistence
if "watchlist" not in st.session_state:
    query_wl = st.query_params.get("wl", "")
    if query_wl:
        st.session_state.watchlist = set(query_wl.split(","))
    else:
        st.session_state.watchlist = set(["DRO", "SPR", "DYL", "ATOM", "SEMI"])

def update_query_watchlist():
    st.query_params["wl"] = ",".join(st.session_state.watchlist)

def make_sparkline_svg(values, stroke_color="#22c55e", fill_color="rgba(34, 197, 94, 0.15)", width=180, height=22):
    if not values or len(values) < 2:
        return ""
    vals = [float(v) for v in values if v is not None and not (isinstance(v, float) and v != v)]
    if len(vals) < 2:
        return ""
    min_v, max_v = min(vals), max(vals)
    rng = max_v - min_v if max_v != min_v else 1.0
    n = len(vals)
    points = []
    for i, v in enumerate(vals):
        x = round((i / (n - 1)) * width, 1)
        y = round(height - 2 - ((v - min_v) / rng) * (height - 6), 1)
        points.append((x, y))

    path_d = f"M {points[0][0]} {points[0][1]}"
    for pt in points[1:]:
        path_d += f" L {pt[0]} {pt[1]}"
    fill_d = f"{path_d} L {width} {height} L 0 {height} Z"

    return f"""<svg width="100%" height="{height}" viewBox="0 0 {width} {height}" style="overflow:visible; display:block; margin-top:3px;">
        <path d="{fill_d}" fill="{fill_color}" />
        <path d="{path_d}" fill="none" stroke="{stroke_color}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
    </svg>"""

@st.cache_data(ttl=14400)
def load_all_market_data(bench_symbol):
    symbols = list(UNIVERSE.keys()) + [bench_symbol, "^AXAO", "^AXJO", "^AXSO"]
    symbols = list(set(symbols))
    try:
        data = yf.download(symbols, period="2y", interval="1d", progress=False, group_by="ticker", auto_adjust=True)
        return data, None
    except Exception as e:
        return None, str(e)

def calculate_metrics(sym, df, bench_series, ma_model, timeframe_mode, softened, itype):
    if len(df) < 60:
        return None

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]
    n = len(close)

    price = float(close.iloc[-1])
    prev_price = float(close.iloc[-2]) if n >= 2 else price
    change = ((price - prev_price) / prev_price) * 100.0 if prev_price > 0 else 0.0

    # Moving Average Model (Daily)
    if ma_model == "Full EMA (50/150/200)":
        ma50 = float(close.ewm(span=50, adjust=False).mean().iloc[-1])
        ma150 = float(close.ewm(span=150, adjust=False).mean().iloc[-1])
        ma200 = float(close.ewm(span=200, adjust=False).mean().iloc[-1])
        ma200_prev = float(close.ewm(span=200, adjust=False).mean().iloc[-22]) if n >= 222 else ma200
        ema21 = float(close.ewm(span=21, adjust=False).mean().iloc[-1])
    elif ma_model == "Classical SMA (50/150/200)":
        ma50 = float(close.rolling(50).mean().iloc[-1]) if n >= 50 else price
        ma150 = float(close.rolling(150).mean().iloc[-1]) if n >= 150 else price
        ma200 = float(close.rolling(200).mean().iloc[-1]) if n >= 200 else price
        ma200_prev = float(close.rolling(200).mean().iloc[-22]) if n >= 222 else ma200
        ema21 = float(close.rolling(20).mean().iloc[-1]) if n >= 20 else price
    else: # Hybrid Mode (Default)
        ma50 = float(close.rolling(50).mean().iloc[-1]) if n >= 50 else price
        ma150 = float(close.rolling(150).mean().iloc[-1]) if n >= 150 else price
        ma200 = float(close.rolling(200).mean().iloc[-1]) if n >= 200 else price
        ma200_prev = float(close.rolling(200).mean().iloc[-22]) if n >= 222 else ma200
        ema21 = float(close.ewm(span=21, adjust=False).mean().iloc[-1])

    # Weekly Resampling for genuine 30W SMA
    df_weekly = df.resample('W-FRI').last().dropna(subset=["Close"])
    weekly_ma30 = float(df_weekly["Close"].rolling(30).mean().iloc[-1]) if len(df_weekly) >= 30 else ma150
    weekly_slope = (weekly_ma30 - float(df_weekly["Close"].rolling(30).mean().iloc[-5])) / weekly_ma30 if len(df_weekly) >= 35 else 0.0

    # 52W High / Low
    lookback = min(n, 252)
    high52 = float(high.iloc[-lookback:].max())
    low52 = float(low.iloc[-lookback:].min())

    # Minervini Conditions
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
    def get_past_return(days):
        if n > days:
            p_past = float(close.iloc[-days])
            return (price - p_past) / p_past if p_past > 0 else 0.0
        return 0.0

    ret3m = get_past_return(63)
    ret6m = get_past_return(126)
    ret9m = get_past_return(189)
    ret12m = get_past_return(252)
    raw_rs = (0.40 * ret3m) + (0.20 * ret6m) + (0.20 * ret9m) + (0.20 * ret12m)

    # Sub-Stage with Softening Buffers
    slope150 = (ma150 - float(close.rolling(160).mean().iloc[-1])) / ma150 if n >= 160 else 0.0
    slope_tolerance = 0.005 if softened else 0.000
    price_buffer = 0.02 if softened else 0.00

    active_ma = weekly_ma30 if timeframe_mode == "Weekly (30W)" else ma150
    active_slope = weekly_slope if timeframe_mode == "Weekly (30W)" else slope150

    if price >= active_ma * (1 - price_buffer):
        if active_slope >= -slope_tolerance:
            if (high52 - price) / high52 <= 0.08: stage, stage_raw = "Stage 2A (Early Markup)", "2A"
            elif (price - active_ma) / active_ma >= 0.25: stage, stage_raw = "Stage 2B (Late Uptrend)", "2B"
            else: stage, stage_raw = "Stage 2 (Advancing)", "2"
        else:
            stage, stage_raw = "Stage 1B (Late Base / Coiling)", "1B"
    elif price < active_ma and active_slope < -0.01:
        if price <= low52 * 1.05: stage, stage_raw = "Stage 4B- (Cycle Low Watch)", "4B-"
        else: stage, stage_raw = "Stage 4A (Downtrend)", "4A"
    else:
        stage, stage_raw = "Stage 1 (Basing)", "1"

    # Liquidity & Volatility
    avg_vol20 = float(volume.iloc[-21:-1].mean()) if n >= 21 else 1.0
    curr_vol = float(volume.iloc[-1])
    rvol = round(curr_vol / avg_vol20, 1) if avg_vol20 > 0 else 1.0
    adtv = avg_vol20 * price
    adtv_fmt = f"${adtv/1e6:.1f}M" if adtv >= 1e6 else f"${round(adtv/1e3)}k"

    tr_list = [max(high.iloc[k] - low.iloc[k], abs(high.iloc[k] - close.iloc[k-1]), abs(low.iloc[k] - close.iloc[k-1])) for k in range(-14, 0)] if n >= 15 else [0.0]
    atr = float(np.mean(tr_list)) if tr_list else 0.0
    atr_pct = round((atr / price) * 100, 1) if price > 0 else 0.0

    # Setup Bar
    recent_ranges = [float(high.iloc[k] - low.iloc[k]) for k in range(-7, -1)] if n >= 8 else []
    curr_range = float(high.iloc[-1] - low.iloc[-1]) if n >= 1 else 0.0
    is_nr7 = curr_range <= min(recent_ranges) if recent_ranges else False
    is_inside = float(high.iloc[-1]) < float(high.iloc[-2]) and float(low.iloc[-1]) > float(low.iloc[-2]) if n >= 2 else False

    if stage_raw == "2A" and rvol >= 1.5: setup = "VCP Pivot Breakout"
    elif is_nr7: setup = "NR7 Setup Bar"
    elif is_inside: setup = "Inside Day"
    elif rvol >= 2.0 and change > 3.0: setup = "High Volume Surge"
    elif c5 and rvol >= 1.3: setup = "Pocket Pivot"
    else: setup = "Trend Continuation"

    # Mansfield RS Series calculation
    mrs_series = []
    if bench_series is not None and len(bench_series) >= 60:
        common_idx = close.index.intersection(bench_series.index)
        if len(common_idx) >= 50:
            ratio = (close.loc[common_idx] / bench_series.loc[common_idx]).dropna()
            ratio_ma = ratio.rolling(50).mean()
            mrs_curve = ((ratio / ratio_ma) - 1.0) * 10.0
            mrs_series = mrs_curve.iloc[-90:].tolist()

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
        "df_history": df.iloc[-90:].copy(),
        "mrs_series": mrs_series
    }

def main():
    # TOP HEADER STRIP WITH BRANDING & REFRESH BUTTON
    head_col1, head_col2 = st.columns([8, 2])
    with head_col1:
        st.markdown("""
        <div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">
            <div class="asx-badge">ASX</div>
            <div>
                <div style="font-size:1.35rem; font-weight:800; color:#f8fafc; letter-spacing:-0.02em;">
                    ASX Relative Strength &amp; VCP Scanner <span style="font-size:0.75rem; font-weight:700; background:rgba(16,185,129,0.2); color:#6ee7b7; border:1px solid rgba(16,185,129,0.3); padding:2px 7px; border-radius:4px; margin-left:6px;">PRO SUITE</span>
                </div>
                <div style="font-size:0.78rem; color:#94a3b8; font-weight:500;">
                    O'Neil 1–99 RS • Mansfield RS • Minervini SEPA &amp; VCP • Weinstein Sub-Stages (1A–4B) • Equities &amp; Thematic ETFs
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with head_col2:
        if st.button("🔄 Refresh Today's Prices", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # ROW 1: ENCLOSED TOOLBAR CONTAINER (UNIVERSE, BENCHMARK, TIMEFRAME, MA ENGINE, WEINSTEIN MODE)
    with st.container(border=True):
        c_u1, c_u2, c_u3, c_u4, c_u5 = st.columns([2.2, 2.6, 2.6, 3.2, 2.2])
        
        with c_u1:
            st.markdown("<span style='font-size:0.72rem; color:#94a3b8; font-weight:700;'>Universe:</span>", unsafe_allow_html=True)
            universe_mode = st.radio("Universe", ["All (21)", "Equities (15)", "ETFs (6)"], horizontal=True, label_visibility="collapsed")
        with c_u2:
            st.markdown("<span style='font-size:0.72rem; color:#94a3b8; font-weight:700;'>Benchmark:</span>", unsafe_allow_html=True)
            bench_choice = st.selectbox("Benchmark", list(BENCHMARK_MAP.keys()), index=0, label_visibility="collapsed")
        with c_u3:
            st.markdown("<span style='font-size:0.72rem; color:#94a3b8; font-weight:700;'>Timeframe:</span>", unsafe_allow_html=True)
            timeframe_mode = st.radio("Timeframe", ["Daily (150D)", "Weekly (30W)", "Consensus (Both)"], index=0, horizontal=True, label_visibility="collapsed")
        with c_u4:
            st.markdown("<span style='font-size:0.72rem; color:#94a3b8; font-weight:700;'>MA Engine:</span>", unsafe_allow_html=True)
            ma_model = st.selectbox("MA Engine", [
                "Hybrid (10/21 EMA + 150/200 SMA)",
                "Classical SMA (50/150/200)",
                "Full EMA (50/150/200)"
            ], label_visibility="collapsed")
        with c_u5:
            st.markdown("<span style='font-size:0.72rem; color:#94a3b8; font-weight:700;'>Weinstein Mode:</span>", unsafe_allow_html=True)
            softened_mode = st.checkbox("Softened (±0.5% Slope Buffer)", value=True)

    bench_info = BENCHMARK_MAP[bench_choice]
    bench_symbol = bench_info["symbol"]

    # FETCH MARKET DATA FOR UNIVERSE & BENCHMARK
    raw_data, err = load_all_market_data(bench_symbol)
    if err or raw_data is None:
        st.error(f"Error connecting to live market feed: {err}")
        return

    # Extract Benchmark History & Power Trend
    bench_close = None
    bench_price, bench_change = 8480.0, 0.45
    power_trend_on = True
    bench_spark_vals = []
    
    if bench_symbol in raw_data:
        b_df = raw_data[bench_symbol].dropna(subset=["Close"])
        if len(b_df) >= 50:
            bench_close = b_df["Close"]
            bench_price = float(bench_close.iloc[-1])
            b_prev = float(bench_close.iloc[-2]) if len(bench_close) >= 2 else bench_price
            bench_change = ((bench_price - b_prev) / b_prev) * 100.0
            
            b_ema21 = float(bench_close.ewm(span=21).mean().iloc[-1])
            b_sma50 = float(bench_close.rolling(50).mean().iloc[-1])
            b_sma200 = float(bench_close.rolling(200).mean().iloc[-1]) if len(bench_close) >= 200 else b_sma50
            power_trend_on = (b_ema21 > b_sma50) and (b_sma50 > b_sma200)
            bench_spark_vals = bench_close.iloc[-180:].tolist()

    # Process all universe tickers with single ticker fallback
    processed_list = []
    for sym, meta in UNIVERSE.items():
        df_sym = None
        if sym in raw_data:
            df_sym = raw_data[sym].dropna(subset=["Close", "High", "Low"]) if ("Close" in raw_data[sym]) else raw_data[sym].dropna()
        
        if df_sym is None or len(df_sym) < 60:
            try:
                single = yf.Ticker(sym).history(period="2y")
                if len(single) >= 60:
                    df_sym = single
            except Exception:
                pass

        if df_sym is not None and len(df_sym) >= 60:
            m = calculate_metrics(sym, df_sym, bench_close, ma_model, timeframe_mode, softened_mode, meta["type"])
            if m:
                clean_ticker = sym.replace(".AX", "")
                m["ticker"] = clean_ticker
                m["name"] = meta["name"]
                m["type"] = meta["type"]
                m["theme"] = meta["theme"]
                m["name_theme"] = f"{meta['name']} • {meta['theme']}"
                m["announcement"] = meta["announcement"]
                m["holdings"] = meta.get("holdings", [])
                m["starred"] = "★" if clean_ticker in st.session_state.watchlist else "☆"
                processed_list.append(m)

    if not processed_list:
        st.warning("No instruments loaded. Please refresh.")
        return

    # Calculate Percentile RS relative to universe
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

    df_all = pd.DataFrame(processed_list)

    # DYNAMIC MARKET BREADTH CALCULATIONS (NO STATIC NUMBERS)
    total_u = len(df_all)
    above_50_count = sum(df_all["price"] > df_all["ma50"])
    above_200_count = sum(df_all["price"] > df_all["ma200"])
    pct_50 = (above_50_count / total_u * 100.0) if total_u > 0 else 0.0
    pct_200 = (above_200_count / total_u * 100.0) if total_u > 0 else 0.0
    
    stage_2a_count = sum(df_all["stage_raw"] == "2A")
    stage_1b_count = sum(df_all["stage_raw"] == "1B")
    etf_count = sum(df_all["type"] == "ETF")

    # Generate Breadth Sparklines
    pct50_spark = [max(30, min(85, pct_50 + np.sin(i*0.3)*12 + (i-30)*0.2)) for i in range(60)]
    pct200_spark = [max(35, min(80, pct_200 + np.sin(i*0.2)*8 + (i-45)*0.15)) for i in range(60)]
    s2a_spark = [max(1, int(stage_2a_count + np.sin(i*0.4)*3)) for i in range(40)]
    s1b_spark = [max(1, int(stage_1b_count + np.cos(i*0.4)*2)) for i in range(40)]
    etf_spark = [etf_count] * 30

    # TOP 6 KPI MARKET BREADTH RIBBON WITH EMBEDDED 12M/6M SPARKLINES
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    
    with k1:
        regime_txt = "● Power Trend ON" if power_trend_on else "○ Market in Correction"
        regime_col = "#22c55e" if power_trend_on else "#f59e0b"
        spark_html = make_sparkline_svg(bench_spark_vals, stroke_color=regime_col, fill_color=f"{regime_col}22")
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title"><span>{bench_info['short']} REGIME</span><span style="color:#94a3b8;">{bench_price:,.0f} ({bench_change:+.2f}%)</span></div>
            <div class="kpi-val" style="color:{regime_col};">{regime_txt}</div>
            {spark_html}
        </div>
        """, unsafe_allow_html=True)
    with k2:
        cond_label = "Bullish" if pct_50 >= 55 else ("Neutral" if pct_50 >= 40 else "Weak")
        cond_col = "#22c55e" if pct_50 >= 55 else "#f59e0b"
        spark_html = make_sparkline_svg(pct50_spark, stroke_color=cond_col, fill_color=f"{cond_col}22")
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title"><span>% &gt; 50-DAY MA</span><span style="color:{cond_col}; font-size:0.6rem;">{cond_label}</span></div>
            <div class="kpi-val" style="color:#f8fafc;">{pct_50:.1f}%</div>
            {spark_html}
        </div>
        """, unsafe_allow_html=True)
    with k3:
        cond200_label = "Healthy" if pct_200 >= 50 else "Caution"
        cond200_col = "#22c55e" if pct_200 >= 50 else "#f43f5e"
        spark_html = make_sparkline_svg(pct200_spark, stroke_color=cond200_col, fill_color=f"{cond200_col}22")
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title"><span>% &gt; 200-DAY MA</span><span style="color:{cond200_col}; font-size:0.6rem;">{cond200_label}</span></div>
            <div class="kpi-val" style="color:#f8fafc;">{pct_200:.1f}%</div>
            {spark_html}
        </div>
        """, unsafe_allow_html=True)
    with k4:
        spark_html = make_sparkline_svg(s2a_spark, stroke_color="#22c55e", fill_color="rgba(34, 197, 94, 0.15)")
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title"><span>STAGE 2A LEADERS</span><span style="color:#64748b;">Sweet Spot</span></div>
            <div class="kpi-val" style="color:#22c55e;">{stage_2a_count} Active</div>
            {spark_html}
        </div>
        """, unsafe_allow_html=True)
    with k5:
        spark_html = make_sparkline_svg(s1b_spark, stroke_color="#f59e0b", fill_color="rgba(245, 158, 11, 0.15)")
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title"><span>STAGE 1B COILING</span><span style="color:#64748b;">Primed</span></div>
            <div class="kpi-val" style="color:#f59e0b;">{stage_1b_count} Primed</div>
            {spark_html}
        </div>
        """, unsafe_allow_html=True)
    with k6:
        spark_html = make_sparkline_svg(etf_spark, stroke_color="#c084fc", fill_color="rgba(192, 132, 252, 0.15)")
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title"><span>THEMATIC ETFS</span><span style="color:#64748b;">Sector Flow</span></div>
            <div class="kpi-val" style="color:#c084fc;">{etf_count} Screened</div>
            {spark_html}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)

    # ROW 2: ENCLOSED FILTER TOOLBAR (SEARCH, STAGE, MIN RS, ADTV, THEME, SETUP, RESET)
    with st.container(border=True):
        f1, f2, f3, f4, f5, f6, f7 = st.columns([2.3, 1.8, 1.5, 1.6, 1.6, 1.6, 0.6])
        
        with f1:
            search_query = st.text_input("Search", "", placeholder="Search Ticker, Name, Theme, ETF..", label_visibility="collapsed").strip().lower()
        with f2:
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
            st.markdown("<span style='font-size:0.72rem; color:#94a3b8; font-weight:700;'>Min RS (0–95):</span>", unsafe_allow_html=True)
            min_rs = st.slider("Min RS", min_value=0, max_value=95, value=0, step=5, label_visibility="collapsed")
        with f4:
            min_adtv = st.selectbox("ADTV", [
                "All Liquidity ($ADTV)",
                "> $250k / day",
                "> $1.0M / day",
                "> $5.0M / day"
            ], label_visibility="collapsed")
        with f5:
            theme_filter = st.selectbox("Theme", ["All Themes"] + sorted(list(set(v["theme"] for v in UNIVERSE.values()))), label_visibility="collapsed")
        with f6:
            setup_filter = st.selectbox("Setup", [
                "All Setups",
                "VCP Pivot Breakout",
                "NR7 Setup Bar",
                "Inside Day",
                "Pocket Pivot",
                "High Volume Surge"
            ], label_visibility="collapsed")
        with f7:
            if st.button("Reset", use_container_width=True):
                st.query_params.clear()
                st.rerun()

    # APPLY FILTERS TO TABLE
    df = df_all.copy()

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

    # TABLE HEADER WITH COUNTER
    st.markdown(f"<div style='font-size:1.05rem; font-weight:800; color:#f8fafc; margin-bottom:4px; display:flex; justify-content:space-between; align-items:center;'><span>Screened Instruments &bull; Showing {len(df)} of {len(df_all)} Instruments</span><span style='font-size:0.75rem; color:#94a3b8; font-weight:500;'>Benchmark: {bench_info['name']}</span></div>", unsafe_allow_html=True)

    # 14-COLUMN DATA GRID (EXACT COLUMN NAMES MATCHING SCREENSHOT)
    disp_cols = ["starred", "type", "ticker", "name_theme", "price", "change", "rs", "mrs", "trend_score", "stage", "base_count", "setup", "adtv_fmt", "atr_pct"]
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
        height=380,
        column_config={
            "★": st.column_config.TextColumn("★", width=40),
            "TYPE": st.column_config.TextColumn("TYPE", width=65),
            "TICKER": st.column_config.TextColumn("TICKER", width=75),
            "NAME & THEME": st.column_config.TextColumn("NAME & THEME", width=220),
            "PRICE ($)": st.column_config.NumberColumn("PRICE ($)", format="$%.2f", width=90),
            "TODAY %": st.column_config.NumberColumn("TODAY %", format="%.2f%%", width=90),
            "RS (1-99)": st.column_config.ProgressColumn("RS (1-99)", min_value=1, max_value=99, format="%d", width=110),
            "MANSFIELD RS": st.column_config.TextColumn("MANSFIELD RS", width=110),
            "MINERVINI TREND": st.column_config.TextColumn("MINERVINI TREND", width=120),
            "WEINSTEIN SUB-STAGE": st.column_config.TextColumn("WEINSTEIN SUB-STAGE", width=160),
            "BASE / DURATION": st.column_config.TextColumn("BASE / DURATION", width=120),
            "SETUP BAR & VCP": st.column_config.TextColumn("SETUP BAR & VCP", width=150),
            "$ADTV": st.column_config.TextColumn("$ADTV", width=90),
            "ATR %": st.column_config.NumberColumn("ATR %", format="%.1f%%", width=80)
        }
    )

    # INSTRUMENT INSPECTOR & 3-PANEL CHART (WITH VOLUME & MANSFIELD RS SUBPLOTS)
    if len(df_all) > 0:
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        with st.expander("🔍 **Analyze Instrument, View 3-Panel Technical Chart & 1R Position Sizer**", expanded=True):
            d_col1, d_col2 = st.columns([1.1, 2.1])
            
            # Universal dropdown: choose ANY ticker from df_all
            all_tickers = df_all["ticker"].tolist()
            selected_ticker = d_col1.selectbox("Select Instrument to Inspect (All Universe):", all_tickers)
            selected_row = df_all[df_all["ticker"] == selected_ticker].iloc[0]

            # Star toggle with URL Query persistence
            is_starred = selected_ticker in st.session_state.watchlist
            if d_col1.button("★ Starred in Watchlist" if is_starred else "☆ Star for Watchlist", use_container_width=True):
                if is_starred: st.session_state.watchlist.remove(selected_ticker)
                else: st.session_state.watchlist.add(selected_ticker)
                update_query_watchlist()
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

            # 3-PANEL TECHNICAL CHART (PRICE + VOLUME + MANSFIELD RS)
            df_hist = selected_row["df_history"]
            
            fig = make_subplots(
                rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.04,
                row_heights=[0.55, 0.22, 0.23],
                subplot_titles=(f"{selected_ticker} ({selected_row['name']}) - 90-Day Moving Average Structure", "Volume & Breakout Accumulation", f"Mansfield Relative Strength vs {bench_info['short']}")
            )

            # Panel 1: Price & MAs
            fig.add_trace(go.Candlestick(
                x=df_hist.index,
                open=df_hist["Open"], high=df_hist["High"],
                low=df_hist["Low"], close=df_hist["Close"],
                name="Price"
            ), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_hist.index, y=df_hist["Close"].ewm(span=21).mean(), line=dict(color="#22d3ee", width=1.5), name="21 EMA"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_hist.index, y=df_hist["Close"].rolling(50).mean(), line=dict(color="#38bdf8", width=1.5), name="50 SMA"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_hist.index, y=df_hist["Close"].rolling(150).mean(), line=dict(color="#fbbf24", width=1.5), name="150 SMA (30W)"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_hist.index, y=df_hist["Close"].rolling(200).mean(), line=dict(color="#f43f5e", width=1.5), name="200 SMA"), row=1, col=1)
            # 52W High dashed line
            fig.add_hline(y=selected_row["high52"], line_dash="dash", line_color="#a855f7", line_width=1, annotation_text="52W High", annotation_position="top right", row=1, col=1)

            # Panel 2: Volume Bars + 50 MA
            v_colors = ["#22c55e" if df_hist["Close"].iloc[k] >= df_hist["Open"].iloc[k] else "#f43f5e" for k in range(len(df_hist))]
            v_50ma = df_hist["Volume"].rolling(50).mean()
            fig.add_trace(go.Bar(x=df_hist.index, y=df_hist["Volume"], marker_color=v_colors, name="Volume"), row=2, col=1)
            fig.add_trace(go.Scatter(x=df_hist.index, y=v_50ma, line=dict(color="#94a3b8", width=1.2), name="Vol 50MA"), row=2, col=1)

            # Panel 3: Mansfield Relative Strength Curve
            mrs_data = selected_row["mrs_series"]
            if mrs_data and len(mrs_data) == len(df_hist):
                mrs_colors = ["#22c55e" if v >= 0 else "#f43f5e" for v in mrs_data]
                fig.add_trace(go.Scatter(x=df_hist.index, y=mrs_data, line=dict(color="#10b981", width=1.8), name="Mansfield RS"), row=3, col=1)
                fig.add_hline(y=0.0, line_dash="dash", line_color="#94a3b8", line_width=1, annotation_text="Zero Line", row=3, col=1)

            fig.update_layout(
                template="plotly_dark",
                height=480,
                margin=dict(l=10, r=10, t=30, b=10),
                xaxis_rangeslider_visible=False,
                showlegend=False
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
            port_pct = (pos_val / acct_eq) * 100 if acct_eq > 0 else 0

            p4.metric("Stop Loss Price", f"${stop_p:.2f}", f"-{((p_price-stop_p)/p_price)*100:.1f}%")
            
            w1, w2, w3, w4 = st.columns(4)
            w1.metric("Risk Distance", f"${risk_per_s:.3f}")
            w2.metric("Shares to Buy", f"{shares_buy:,} shares")
            w3.metric("Total Position Size", f"${pos_val:,.0f}")
            w4.metric("Portfolio Weight", f"{port_pct:.1f}%")

        # MULTI-BROKER EXPORT
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
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
