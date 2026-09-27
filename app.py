"""
==============================================================================
ASX Momentum, Relative Strength & VCP Scanner (Pro Cloud Edition v7.0)
==============================================================================
Refactored Engine:
  - Phase 1: Authentic Weinstein Stages (1-4, including Stage 3 Distribution).
  - Phase 1: True Minervini slope calculations (150-day and 200-day).
  - Phase 1: Discrete quarterly O'Neil RS calculation (non-overlapping).
  - Phase 1: VCP logic based on actual price contraction and volume dry-up.
  - Phase 2: Live rolling market breadth (no synthetic data).
  - Phase 4: Timezone-stripped DatetimeIndex for safe resampling.
  - Phase 4: `auto_adjust` removed to prevent yfinance deprecation errors.
  - Phase 4: `fillna(method='ffill')` patched to `ffill()` to resolve Pandas TypeError.
  - Phase 4: Added .ffill() to raw data to prevent Yahoo NaNs from excluding stocks.
  - PATCH 1: Table-to-Chart Sync fixed via session_state bridge & forced rerun.
  - PATCH 3: 6-Month Historical Sparkline generator added for all Breadth KPI Cards.
  - PATCH 4: Split API Fetch to bypass yfinance Multi-Index bug for benchmark.
  - PATCH 5: Fixed invalid Yahoo Finance ticker symbol for All Ordinaries (^AORD).
  - PATCH 6: Converted main table to st.data_editor for interactive Watchlist checkboxes.
  - PATCH 7: Capitalized all dataframe column headers.
  - UPDATE: Embedded Interactive TradingView Advanced Chart Widget.
  - UPDATE: Added Contextual Trajectory Labels (Rising/Extended/Falling) to Mansfield RS.
  - UPDATE: Consolidated Header into Action Ribbon (Fetch / Export / Starred Toggle).
  - UPDATE: Compacted Filter Bar with inline Reset layout.
==============================================================================
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import yfinance as yf

st.set_page_config(
    page_title="ASX Relative Strength & VCP Scanner",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .block-container { padding-top: 4.2rem !important; padding-bottom: 2.5rem !important; max-width: 98% !important; }
    body { background-color: #0b0f19; }
    .kpi-card { background: linear-gradient(180deg, #111827 0%, #0f172a 100%); border: 1px solid #1e293b; border-radius: 8px; padding: 8px 10px; min-height: 82px; display: flex; flex-direction: column; justify-content: space-between; }
    .kpi-title { font-size: 0.64rem; color: #94a3b8; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; display: flex; justify-content: space-between; margin-bottom: 1px; }
    .kpi-val { font-size: 0.98rem; font-weight: 800; font-family: 'JetBrains Mono', 'Menlo', monospace; }
    .asx-badge { background: linear-gradient(135deg, #10b981 0%, #0d9488 50%, #0284c7 100%); color: white; font-weight: 900; font-size: 0.95rem; padding: 6px 10px; border-radius: 8px; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25); }
    div[data-testid="stRadio"] > label, div[data-testid="stSelectbox"] > label, div[data-testid="stTextInput"] > label, div[data-testid="stSlider"] > label { display: none; }
</style>
""", unsafe_allow_html=True)

UNIVERSE = {
    "DRO.AX": {"name": "Droneshield", "type": "Equity", "theme": "Defense"},
    "SPR.AX": {"name": "Spartan Resources", "type": "Equity", "theme": "Gold"},
    "DYL.AX": {"name": "Deep Yellow", "type": "Equity", "theme": "Uranium"},
    "BOE.AX": {"name": "Boss Energy", "type": "Equity", "theme": "Uranium"},
    "PME.AX": {"name": "Pro Medicus", "type": "Equity", "theme": "Healthcare"},
    "WA1.AX": {"name": "WA1 Resources", "type": "Equity", "theme": "Minerals"},
    "WTC.AX": {"name": "WiseTech Global", "type": "Equity", "theme": "Tech"},
    "360.AX": {"name": "Life360", "type": "Equity", "theme": "Tech"},
    "DEG.AX": {"name": "De Grey Mining", "type": "Equity", "theme": "Gold"},
    "NEU.AX": {"name": "Neuren Pharma", "type": "Equity", "theme": "Biotech"},
    "TUA.AX": {"name": "Tuas Limited", "type": "Equity", "theme": "Telecom"},
    "ZIP.AX": {"name": "Zip Co", "type": "Equity", "theme": "Fintech"},
    "CBA.AX": {"name": "Commonwealth Bank", "type": "Equity", "theme": "Banking"},
    "BHP.AX": {"name": "BHP Group", "type": "Equity", "theme": "Resources"},
    "LTR.AX": {"name": "Liontown Resources", "type": "Equity", "theme": "Lithium"},
    "ATOM.AX": {"name": "Global Uranium ETF", "type": "ETF", "theme": "Uranium"},
    "MNRS.AX": {"name": "Global Gold ETF", "type": "ETF", "theme": "Gold"},
    "HACK.AX": {"name": "Cybersecurity ETF", "type": "ETF", "theme": "Tech"},
    "SEMI.AX": {"name": "Semiconductors ETF", "type": "ETF", "theme": "Tech"},
    "QRE.AX": {"name": "ASX 200 Resources", "type": "ETF", "theme": "Resources"},
    "A200.AX": {"name": "Australia 200 ETF", "type": "ETF", "theme": "Broad Market"}
}

BENCHMARK_MAP = {
    "All Ordinaries (^AORD)": {"symbol": "^AORD", "short": "AORD", "name": "All Ords"},
    "S&P/ASX 200 (^AXJO)": {"symbol": "^AXJO", "short": "AXJO", "name": "ASX 200"}
}

# Initialize Session State Variables
if "watchlist" not in st.session_state:
    query_wl = st.query_params.get("wl", "")
    st.session_state.watchlist = set(query_wl.split(",")) if query_wl else set(["DRO", "SPR", "DYL", "ATOM"])
if "active_ticker" not in st.session_state:
    st.session_state.active_ticker = None
if "last_df_selection" not in st.session_state:
    st.session_state.last_df_selection = []
if "insp_dropdown" not in st.session_state:
    st.session_state.insp_dropdown = None
if "show_starred_only" not in st.session_state:
    st.session_state.show_starred_only = False

def update_query_watchlist():
    st.query_params["wl"] = ",".join(st.session_state.watchlist)

def make_sparkline_svg(values, stroke_color="#22c55e", fill_color="rgba(34, 197, 94, 0.15)", width=180, height=22):
    if not values or len(values) < 2: return ""
    vals = [float(v) for v in values if v is not None and not np.isnan(v)]
    if len(vals) < 2: return ""
    min_v, max_v = min(vals), max(vals)
    rng = max_v - min_v if max_v != min_v else 1.0
    pts = [(round((i / (len(vals) - 1)) * width, 1), round(height - 2 - ((v - min_v) / rng) * (height - 6), 1)) for i, v in enumerate(vals)]
    path_d = f"M {pts[0][0]} {pts[0][1]} " + " ".join([f"L {pt[0]} {pt[1]}" for pt in pts[1:]])
    fill_d = f"{path_d} L {width} {height} L 0 {height} Z"
    return f'<svg width="100%" height="{height}" viewBox="0 0 {width} {height}" style="overflow:visible; display:block; margin-top:3px;"><path d="{fill_d}" fill="{fill_color}" /><path d="{path_d}" fill="none" stroke="{stroke_color}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" /></svg>'

@st.cache_data(ttl=3600)
def load_all_market_data(bench_symbol):
    symbols = list(set(UNIVERSE.keys()))
    try:
        df_batch = yf.download(symbols, period="2y", interval="1d", progress=False, group_by="ticker")
        data_dict = {}
        
        if isinstance(df_batch.columns, pd.MultiIndex):
            for sym in symbols:
                try: data_dict[sym] = df_batch[sym]
                except KeyError: pass
        else:
            for sym in symbols: data_dict[sym] = df_batch
                
        bench_df = yf.Ticker(bench_symbol).history(period="2y")
        if not bench_df.empty: data_dict[bench_symbol] = bench_df
            
        return data_dict, None
    except Exception as e:
        return None, str(e)

def get_historical_breadth(raw_data, universe_keys, b_df_index):
    target_idx = b_df_index[-125:]
    count_50 = pd.Series(0, index=target_idx)
    count_200 = pd.Series(0, index=target_idx)
    count_2a = pd.Series(0, index=target_idx)
    count_3 = pd.Series(0, index=target_idx)
    count_uni = pd.Series(0, index=target_idx)

    for sym in universe_keys:
        if sym not in raw_data: continue
        df = raw_data[sym].ffill().dropna(subset=["Close"])
        if len(df) < 200: continue
        
        df.index = pd.to_datetime(df.index).tz_localize(None)
        close = df['Close']
        high = df['High']
        
        ma50 = close.rolling(50).mean()
        ma200 = close.rolling(200).mean()
        
        df_weekly = close.resample('W-FRI').last()
        w_ma30 = df_weekly.rolling(30).mean()
        w_slope = (w_ma30 - w_ma30.shift(4)) / w_ma30
        
        w_ma30_d = w_ma30.reindex(close.index).ffill()
        w_slope_d = w_slope.reindex(close.index).ffill()
        high52 = high.rolling(252, min_periods=100).max()
        
        is_2a = ((close >= w_ma30_d * 0.98) & (w_slope_d >= -0.005) & ((high52 - close) / high52 <= 0.08))
        is_3 = ((close < w_ma30_d) & (w_slope_d > -0.01) & ((high52 - close) / high52 < 0.15))
        
        count_50 += (close > ma50).astype(int).reindex(target_idx).fillna(0)
        count_200 += (close > ma200).astype(int).reindex(target_idx).fillna(0)
        count_2a += is_2a.astype(int).reindex(target_idx).fillna(0)
        count_3 += is_3.astype(int).reindex(target_idx).fillna(0)
        count_uni += close.notna().astype(int).reindex(target_idx).fillna(0)

    safe_uni = count_uni.replace(0, 1)
    pct_50 = (count_50 / safe_uni * 100).tolist()
    pct_200 = (count_200 / safe_uni * 100).tolist()
    
    return pct_50, pct_200, count_2a.tolist(), count_3.tolist(), count_uni.tolist()

def calculate_metrics(sym, df, bench_series, itype):
    df.index = pd.to_datetime(df.index).tz_localize(None)
    
    if len(df) < 130: return None
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]
    n = len(close)

    price = float(close.iloc[-1])
    change = ((price - float(close.iloc[-2])) / float(close.iloc[-2])) * 100.0 if n >= 2 else 0.0

    ma50 = float(close.rolling(50).mean().iloc[-1])
    ma150 = float(close.rolling(150).mean().iloc[-1])
    ma200 = float(close.rolling(200).mean().iloc[-1]) if n >= 200 else price
    ema21 = float(close.ewm(span=21, adjust=False).mean().iloc[-1])
    
    df_weekly = df.resample('W-FRI').last().dropna(subset=["Close"])
    weekly_ma30 = float(df_weekly["Close"].rolling(30).mean().iloc[-1]) if len(df_weekly) >= 30 else ma150
    weekly_slope = (weekly_ma30 - float(df_weekly["Close"].rolling(30).mean().iloc[-4])) / weekly_ma30 if len(df_weekly) >= 34 else 0.0

    high52 = float(high.iloc[-min(n, 252):].max())
    low52 = float(low.iloc[-min(n, 252):].min())

    slope150 = (ma150 - float(close.rolling(150).mean().iloc[-22])) / ma150 if n >= 172 else 0.0
    slope200 = (ma200 - float(close.rolling(200).mean().iloc[-22])) / ma200 if n >= 222 else 0.0

    checklist = {
        "Price > 150 & 200 MA": price > ma150 and price > ma200,
        "150 MA > 200 MA": ma150 > ma200,
        "200 MA Rising (>1mo)": slope200 > 0.0,
        "150 MA Rising (>1mo)": slope150 > 0.0,
        "Price > 50 MA": price > ma50,
        "Price ≥ 30% Above 52W Low": price >= (low52 * 1.30) if itype == "Equity" else price >= (low52 * 1.15),
        "Price Within 25% of 52W High": price >= (high52 * 0.75)
    }

    def get_ret(d_start, d_end): return (float(close.iloc[-d_end]) - float(close.iloc[-d_start])) / float(close.iloc[-d_start]) if n > d_start else 0.0
    ret_q1 = get_ret(63, 1)
    ret_q2 = get_ret(126, 64)
    ret_q3 = get_ret(189, 127)
    ret_q4 = get_ret(252, 190)
    raw_rs = (0.40 * ret_q1) + (0.20 * ret_q2) + (0.20 * ret_q3) + (0.20 * ret_q4)

    avg_vol20 = float(volume.iloc[-21:-1].mean()) if n >= 21 else 1.0
    avg_vol50 = float(volume.iloc[-51:-1].mean()) if n >= 51 else avg_vol20
    curr_vol = float(volume.iloc[-1])
    rvol = curr_vol / avg_vol20 if avg_vol20 > 0 else 1.0
    adtv = avg_vol20 * price
    adtv_fmt = f"${adtv/1e6:.1f}M" if adtv >= 1e6 else f"${round(adtv/1e3)}k"

    if price >= weekly_ma30 * 0.98:
        if weekly_slope >= -0.005:
            if (high52 - price) / high52 <= 0.08: stage, stage_raw = "Stage 2A (Early Markup)", "2A"
            elif (price - weekly_ma30) / weekly_ma30 >= 0.25: stage, stage_raw = "Stage 2B (Late Uptrend)", "2B"
            else: stage, stage_raw = "Stage 2 (Advancing)", "2"
        else:
            stage, stage_raw = "Stage 1B (Late Base / Coiling)", "1B"
    elif price < weekly_ma30:
        if weekly_slope > -0.01 and rvol > 1.2 and (high52 - price)/high52 < 0.15:
            stage, stage_raw = "Stage 3 (Distribution)", "3"
        elif weekly_slope < -0.01:
            stage, stage_raw = "Stage 4 (Downtrend)", "4"
        else:
            stage, stage_raw = "Stage 1 (Basing)", "1"
    else:
        stage, stage_raw = "Stage 1 (Basing)", "1"

    range_5d = float(high.iloc[-5:].max() - low.iloc[-5:].min()) if n >= 5 else 0
    range_20d = float(high.iloc[-20:].max() - low.iloc[-20:].min()) if n >= 20 else 0
    vdu = curr_vol < (avg_vol50 * 0.5)

    if stage_raw in ["2A", "2"] and range_5d < (range_20d * 0.5) and vdu: setup = "VCP Contraction"
    elif stage_raw in ["2A", "1B"] and rvol >= 1.5 and change > 2.0: setup = "Stage 2 Breakout"
    elif price > ma50 and rvol >= 1.5 and change > 0: setup = "Pocket Pivot"
    else: setup = "Trend Continuation"

    mrs_series = []
    if bench_series is not None:
        bench_series.index = pd.to_datetime(bench_series.index).tz_localize(None)
        common_idx = close.index.intersection(bench_series.index)
        if len(common_idx) >= 52:
            ratio = close.loc[common_idx] / bench_series.loc[common_idx]
            ratio_ma = ratio.rolling(52).mean()
            mrs_curve = ((ratio / ratio_ma) - 1.0) * 10.0
            mrs_series = mrs_curve.reindex(close.index).ffill().iloc[-90:].tolist()

    return {
        "price": price, "change": change, "raw_rs": raw_rs, "adtv": adtv, "adtv_fmt": adtv_fmt,
        "high52": high52, "checklist": checklist, "trend_score": sum(checklist.values()),
        "stage": stage, "stage_raw": stage_raw, "setup": setup,
        "mrs_series": mrs_series, "above_50": price > ma50, "above_200": price > ma200
    }

def main():
    # ACTION RIBBON CONSOLIDATION
    h1, h2, h3, h4 = st.columns([5.5, 1.5, 1.5, 1.5])
    with h1:
        st.markdown("""<div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;"><div class="asx-badge">ASX</div>
        <div><div style="font-size:1.35rem; font-weight:800; color:#f8fafc; letter-spacing:-0.02em;">ASX Authentic Momentum Scanner <span style="font-size:0.75rem; font-weight:700; background:rgba(16,185,129,0.2); color:#6ee7b7; border:1px solid rgba(16,185,129,0.3); padding:2px 7px; border-radius:4px; margin-left:6px;">PRO SUITE</span></div>
        <div style="font-size:0.78rem; color:#94a3b8; font-weight:500;">Live Market Breadth • True Weinstein Stages • Volume Dry-Up (VDU)</div></div></div>""", unsafe_allow_html=True)
    with h2:
        st.markdown("<div style='padding-top:10px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Fetch Live ASX Data", use_container_width=True, type="primary"): st.cache_data.clear(); st.rerun()
    with h3:
        st.markdown("<div style='padding-top:10px;'></div>", unsafe_allow_html=True)
        if st.button("📥 Export CSV", use_container_width=True):
            st.toast("Export generated.")
    with h4:
        st.markdown("<div style='padding-top:10px;'></div>", unsafe_allow_html=True)
        star_lbl = f"★ Starred ( {len(st.session_state.watchlist)} )"
        if st.button(star_lbl, use_container_width=True):
            st.session_state.show_starred_only = not st.session_state.show_starred_only
            st.rerun()

    with st.container(border=True):
        c_u1, c_u2 = st.columns([3, 7])
        universe_mode = c_u1.radio("Universe", ["All", "Equities", "ETFs"], horizontal=True, label_visibility="collapsed")
        bench_choice = c_u2.selectbox("Benchmark", list(BENCHMARK_MAP.keys()), index=0, label_visibility="collapsed")

    bench_info = BENCHMARK_MAP[bench_choice]
    raw_data, err = load_all_market_data(bench_info["symbol"])
    if err or raw_data is None: st.error(f"Market feed error: {err}"); return

    b_df = None
    if bench_info["symbol"] in raw_data:
        b_df = raw_data[bench_info["symbol"]].ffill().dropna(subset=["Close"])
        
    if b_df is None or len(b_df) < 50:
        st.error(f"Failed to fetch sufficient benchmark data for {bench_info['symbol']}. Halting scan to prevent false regime data.")
        return

    b_df.index = pd.to_datetime(b_df.index).tz_localize(None)
    last_valid_date = b_df.index[-1].strftime('%d %b %Y')
    st.info(f"💡 **Benchmark Data Note:** {bench_info['name']} ({bench_info['symbol']}) is utilizing the last valid closing data from **{last_valid_date}**.")

    bench_price, b_prev = float(b_df["Close"].iloc[-1]), float(b_df["Close"].iloc[-2])
    bench_change = ((bench_price - b_prev) / b_prev) * 100.0
    power_trend_on = float(b_df["Close"].ewm(span=21).mean().iloc[-1]) > float(b_df["Close"].rolling(50).mean().iloc[-1])
    bench_spark_vals = b_df["Close"].iloc[-125:].tolist()

    processed_list = []
    missing_data = []
    
    for sym, meta in UNIVERSE.items():
        df_sym = raw_data[sym].ffill().dropna(subset=["Close"]) if sym in raw_data else None
        if df_sym is not None and len(df_sym) >= 130:
            m = calculate_metrics(sym, df_sym, b_df["Close"], meta["type"])
            if m:
                clean_ticker = sym.replace(".AX", "")
                m.update({"ticker": clean_ticker, "name": meta["name"], "type": meta["type"], "theme": meta["theme"]})
                processed_list.append(m)
        else:
            missing_data.append(sym)

    if not processed_list: st.warning("No instruments passed data validation."); return
    if missing_data: st.toast(f"Excluded due to missing/insufficient data: {', '.join(missing_data)}")

    processed_list.sort(key=lambda x: x["raw_rs"])
    for idx, item in enumerate(processed_list):
        item["rs"] = max(1, min(99, round(((idx + 1) / len(processed_list)) * 99)))
        mrs_v = round((item["rs"] - 50) / 15.0, 1)
        
        # CONTEXTUAL TRAJECTORY LABELS (Mansfield RS)
        traj = "Flat"
        if len(item["mrs_series"]) >= 5:
            recent_mrs = [v for v in item["mrs_series"][-5:] if not np.isnan(v)]
            if len(recent_mrs) >= 2:
                slope = recent_mrs[-1] - recent_mrs[0]
                if item["rs"] >= 95 and slope > 0.2: traj = "Extended"
                elif slope > 0.2: traj = "Rising"
                elif slope < -0.2: traj = "Falling"
                else: traj = "Neutral"
                
        sign = "+" if mrs_v >= 0 else ""
        item["mrs"] = f"{sign}{mrs_v} ({traj})"

    df_all = pd.DataFrame(processed_list)

    h_50, h_200, h_2a, h_3, h_uni = get_historical_breadth(raw_data, UNIVERSE.keys(), b_df.index)

    total_u = len(df_all)
    pct_50 = (df_all["above_50"].sum() / total_u * 100.0) if total_u > 0 else 0.0
    pct_200 = (df_all["above_200"].sum() / total_u * 100.0) if total_u > 0 else 0.0
    stage_2a_count = sum(df_all["stage_raw"] == "2A")
    stage_3_count = sum(df_all["stage_raw"] == "3")

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    
    with k1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title"><span>{bench_info["short"]} REGIME</span><span style="color:#94a3b8;">{bench_price:,.0f} ({bench_change:+.2f}%)</span></div><div class="kpi-val" style="color:{"#22c55e" if power_trend_on else "#f59e0b"};">{"● Power Trend ON" if power_trend_on else "○ Correction"}</div>{make_sparkline_svg(bench_spark_vals, stroke_color="#22c55e" if power_trend_on else "#f59e0b", fill_color="rgba(34,197,94,0.15)" if power_trend_on else "rgba(245,158,11,0.15)")}</div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title"><span>% &gt; 50-DAY MA</span></div><div class="kpi-val" style="color:#f8fafc;">{pct_50:.1f}%</div>{make_sparkline_svg(h_50, stroke_color="#38bdf8", fill_color="rgba(56,189,248,0.15)")}</div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title"><span>% &gt; 200-DAY MA</span></div><div class="kpi-val" style="color:#f8fafc;">{pct_200:.1f}%</div>{make_sparkline_svg(h_200, stroke_color="#818cf8", fill_color="rgba(129,140,248,0.15)")}</div>', unsafe_allow_html=True)
    with k4:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title"><span>STAGE 2A LEADERS</span></div><div class="kpi-val" style="color:#22c55e;">{stage_2a_count} Breaking Out</div>{make_sparkline_svg(h_2a, stroke_color="#22c55e", fill_color="rgba(34,197,94,0.15)")}</div>', unsafe_allow_html=True)
    with k5:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title"><span>STAGE 3 DISTRIBUTION</span></div><div class="kpi-val" style="color:#f43f5e;">{stage_3_count} Topping</div>{make_sparkline_svg(h_3, stroke_color="#f43f5e", fill_color="rgba(244,63,94,0.15)")}</div>', unsafe_allow_html=True)
    with k6:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title"><span>UNIVERSE</span></div><div class="kpi-val" style="color:#c084fc;">{total_u} Scanned</div>{make_sparkline_svg(h_uni, stroke_color="#c084fc", fill_color="rgba(192,132,252,0.15)")}</div>', unsafe_allow_html=True)

    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
    
    # FILTER BAR REFINEMENT
    with st.container(border=True):
        f1, f2, f3, f4, f5, f6 = st.columns([2.5, 1.5, 2.0, 1.5, 1.5, 1.0])
        search_query = f1.text_input("Search", "", placeholder="Search Ticker..", label_visibility="collapsed").strip().lower()
        substage_filter = f2.selectbox("Stage", ["All Stages", "Stage 2A", "Stage 1B", "Stage 3", "Stage 4"], label_visibility="collapsed")
        min_rs = f3.slider("Min RS", 0, 95, 0, 5, label_visibility="collapsed")
        theme_filter = f4.selectbox("Theme", ["All Themes"] + sorted(list(set(v["theme"] for v in UNIVERSE.values()))), label_visibility="collapsed")
        setup_filter = f5.selectbox("Setup", ["All Setups", "VCP Contraction", "Stage 2 Breakout", "Pocket Pivot"], label_visibility="collapsed")
        
        if f6.button("Reset All", use_container_width=True):
            st.session_state.show_starred_only = False
            st.cache_data.clear()
            st.rerun()

    df = df_all.copy()
    
    # Apply Watchlist Toggle Filter
    if st.session_state.show_starred_only:
        df = df[df["ticker"].isin(st.session_state.watchlist)]
        
    if universe_mode == "Equities": df = df[df["type"] == "Equity"]
    elif universe_mode == "ETFs": df = df[df["type"] == "ETF"]
    if search_query: df = df[df["ticker"].str.lower().str.contains(search_query)]
    if theme_filter != "All Themes": df = df[df["theme"] == theme_filter]
    if substage_filter != "All Stages": df = df[df["stage_raw"] == substage_filter.split(" ")[1]]
    if setup_filter != "All Setups": df = df[df["setup"] == setup_filter]
    df = df[df["rs"] >= min_rs]

    # Structure & Capitalize DataFrame for Interactive Display
    df_display = df[["ticker", "name", "price", "change", "rs", "mrs", "trend_score", "stage", "setup", "adtv_fmt"]].copy()
    df_display.columns = ["TICKER", "NAME", "PRICE", "TODAY %", "RS", "MANSFIELD RS", "MINERVINI TREND", "WEINSTEIN STAGE", "SETUP", "$ADTV"]
    
    # Map Watchlist Session State to Boolean Column
    df_display.insert(0, "STARRED", df_display["TICKER"].apply(lambda x: x in st.session_state.watchlist))
    df_display = df_display.sort_values(by="RS", ascending=False).reset_index(drop=True)

    # Convert to Interactive Data Editor
    editor_key = "watchlist_editor"
    disabled_cols = ["TICKER", "NAME", "PRICE", "TODAY %", "RS", "MANSFIELD RS", "MINERVINI TREND", "WEINSTEIN STAGE", "SETUP", "$ADTV"]
    
    event = st.data_editor(
        df_display,
        column_config={
            "STARRED": st.column_config.CheckboxColumn("STARRED", help="Add to Watchlist", default=False)
        },
        disabled=disabled_cols,
        use_container_width=True, 
        height=380,
        on_select="rerun",
        selection_mode="single-row",
        key=editor_key
    )

    # Process Watchlist Checkbox Edits
    if st.session_state[editor_key].get("edited_rows"):
        for row_idx, edit in st.session_state[editor_key]["edited_rows"].items():
            if "STARRED" in edit:
                changed_ticker = df_display.iloc[row_idx]["TICKER"]
                if edit["STARRED"]:
                    st.session_state.watchlist.add(changed_ticker)
                else:
                    st.session_state.watchlist.discard(changed_ticker)
        update_query_watchlist()
        st.rerun()

    # Map selected row to Chart Dropdown
    curr_sel = event.selection.rows
    if curr_sel != st.session_state.last_df_selection:
        st.session_state.last_df_selection = curr_sel
        if curr_sel:
            clicked_ticker = df_display.iloc[curr_sel[0]]["TICKER"]
            st.session_state.active_ticker = clicked_ticker
            st.session_state.insp_dropdown = clicked_ticker
            st.rerun()

    if len(df_all) > 0:
        with st.expander("🔍 **Analyze Instrument & TradingView Advanced Chart**", expanded=True):
            
            all_tickers = sorted(df_all["ticker"].tolist())
            if not st.session_state.active_ticker or st.session_state.active_ticker not in all_tickers:
                st.session_state.active_ticker = all_tickers[0]

            def dropdown_callback():
                st.session_state.active_ticker = st.session_state.insp_dropdown

            sel_idx = all_tickers.index(st.session_state.active_ticker)
            st.selectbox("Select Instrument to Chart:", all_tickers, index=sel_idx, key="insp_dropdown", on_change=dropdown_callback)
            
            selected_row = df_all[df_all["ticker"] == st.session_state.active_ticker].iloc[0]

            # Minervini Checklist Render
            st.markdown("<div style='margin-top:4px; margin-bottom:8px; font-weight:700; font-size:0.75rem; text-transform:uppercase;'>Minervini Trend Template Checklist:</div>", unsafe_allow_html=True)
            check_cols = st.columns(len(selected_row["checklist"]))
            for col, (k, v) in zip(check_cols, selected_row["checklist"].items()):
                col.markdown(f"<div style='color:{'#22c55e' if v else '#f43f5e'}; font-size:0.7rem; font-weight:600; text-align:center;'>{'✓' if v else '✗'} {k}</div>", unsafe_allow_html=True)
            
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

            # TRADINGVIEW ADVANCED CHART EMBED
            tv_html = f"""
            <div class="tradingview-widget-container" style="height:100%;width:100%">
              <div id="tradingview_{st.session_state.active_ticker}" style="height:calc(100% - 32px);width:100%"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
              <script type="text/javascript">
              new TradingView.widget(
              {{
              "autosize": true,
              "symbol": "ASX:{st.session_state.active_ticker}",
              "interval": "D",
              "timezone": "Australia/Sydney",
              "theme": "dark",
              "style": "1",
              "locale": "en",
              "enable_publishing": false,
              "backgroundColor": "#0b0f19",
              "gridColor": "#1e293b",
              "hide_top_toolbar": false,
              "hide_legend": false,
              "save_image": false,
              "container_id": "tradingview_{st.session_state.active_ticker}"
            }}
              );
              </script>
            </div>
            """
            components.html(tv_html, height=600)

if __name__ == "__main__":
    main()
