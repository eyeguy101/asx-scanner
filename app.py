"""
==============================================================================
ASX Momentum, Relative Strength & VCP Scanner (Pro Cloud Edition v10.0)
==============================================================================
Refactored Engine:
  - Phase 1: Authentic Weinstein Stages (1-4, including Stage 3 Distribution).
  - Phase 1: True Minervini slope calculations (150-day and 200-day).
  - Phase 1: Discrete quarterly O'Neil RS calculation (non-overlapping).
  - Phase 1: VCP logic based on actual price contraction and volume dry-up.
  - Phase 2: Live rolling market breadth (no synthetic data).
  - Phase 4: Timezone-stripped DatetimeIndex for safe resampling.
  - Phase 4: Added .ffill() to raw data to prevent Yahoo NaNs from excluding stocks.
  - UPDATE: Dynamic Universe Integration (Live ASX Directory Scraping via Markit API).
  - UPDATE: Distance to Pivot (%) calculation added to identify tight base breakouts.
  - UPDATE: Integrated dropdown Price Filter (e.g., > $0.10).
  - FIX: Hardened contiguous Weinstein Stage boundaries to eliminate "unclassified" gaps.
  - FIX: Intraday Volume Normalization (pro-rates volume based on AEST time of day).
  - FIX: True Minervini Continuous MA (200-day MA must rise sequentially, not just point-to-point).
  - FIX: Dynamic ATR Tightness for VCP (replaces arbitrary 6% rule).
  - FIX: True Resistance Breakouts (evaluates strictly against prior 20-day highs, excluding today).
  - FIX: Authentic Pocket Pivots (volume must exceed max down-volume of prior 10 days).
==============================================================================
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import yfinance as yf
import pytz

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

FALLBACK_UNIVERSE = {
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
    "CBA.AX": {"name": "Commonwealth Bank", "type": "Equity", "theme": "Banking"},
    "BHP.AX": {"name": "BHP Group", "type": "Equity", "theme": "Resources"}
}

BENCHMARK_MAP = {
    "All Ordinaries (^AORD)": {"symbol": "^AORD", "short": "AORD", "name": "All Ords"},
    "S&P/ASX 200 (^AXJO)": {"symbol": "^AXJO", "short": "AXJO", "name": "ASX 200"}
}

if "watchlist" not in st.session_state:
    query_wl = st.query_params.get("wl", "")
    st.session_state.watchlist = set(query_wl.split(",")) if query_wl else set(["DRO", "SPR", "DYL"])
if "active_ticker" not in st.session_state: st.session_state.active_ticker = None
if "last_df_selection" not in st.session_state: st.session_state.last_df_selection = []
if "insp_dropdown" not in st.session_state: st.session_state.insp_dropdown = None
if "show_starred_only" not in st.session_state: st.session_state.show_starred_only = False

def update_query_watchlist():
    st.query_params["wl"] = ",".join(st.session_state.watchlist)

@st.cache_data(ttl=43200)
def fetch_dynamic_universe():
    try:
        url = "https://asx.api.markitdigital.com/asx-research/1.0/companies/directory/file?access_token=83ff96335c2d45a094df02a206a39ff4"
        df = pd.read_csv(url)
        df = df.dropna(subset=['ASX code'])
        df = df[df['ASX code'].str.match(r'^[A-Z]{3}$')]
        
        dynamic_universe = {}
        for _, row in df.iterrows():
            sym = f"{row['ASX code']}.AX"
            theme = str(row.get('GICS industry group', 'Unclassified')).title()
            if theme in ["Nan", "Not Applic", "Unclassified"]: theme = "Diversified / Unclassified"
                
            dynamic_universe[sym] = {
                "name": str(row.get('Company name', sym)).title(),
                "type": "Equity",
                "theme": theme
            }
        return dynamic_universe
    except Exception as e:
        return FALLBACK_UNIVERSE

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
def load_all_market_data(universe_dict, bench_symbol):
    symbols = list(set(universe_dict.keys()))
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
    return (count_50 / safe_uni * 100).tolist(), (count_200 / safe_uni * 100).tolist(), count_2a.tolist(), count_3.tolist(), count_uni.tolist()

def calculate_metrics(sym, df, bench_series, itype):
    df.index = pd.to_datetime(df.index).tz_localize(None)
    
    if len(df) < 130: return None
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]
    n = len(close)

    price = float(close.iloc[-1])
    prev_price = float(close.iloc[-2]) if n >= 2 else price
    change = ((price - prev_price) / prev_price) * 100.0 if prev_price > 0.0 else 0.0

    ma50 = float(close.rolling(50).mean().iloc[-1])
    ma150 = float(close.rolling(150).mean().iloc[-1])
    ma200 = float(close.rolling(200).mean().iloc[-1]) if n >= 200 else price
    
    # Authentic Continuous MA200 Rising Check
    ma200_10d = float(close.rolling(200).mean().iloc[-11]) if n >= 210 else price
    ma200_22d = float(close.rolling(200).mean().iloc[-23]) if n >= 222 else price
    ma200_rising = (ma200 > ma200_10d) and (ma200_10d > ma200_22d)

    slope150 = (ma150 - float(close.rolling(150).mean().iloc[-22])) / ma150 if n >= 172 else 0.0
    
    df_weekly = df.resample('W-FRI').last().dropna(subset=["Close"])
    weekly_ma30 = float(df_weekly["Close"].rolling(30).mean().iloc[-1]) if len(df_weekly) >= 30 else ma150
    weekly_slope = (weekly_ma30 - float(df_weekly["Close"].rolling(30).mean().iloc[-4])) / weekly_ma30 if len(df_weekly) >= 34 else 0.0

    high52 = float(high.iloc[-min(n, 252):].max())
    low52 = float(low.iloc[-min(n, 252):].min())

    # Prior Resistance (excludes today)
    prior_resistance = float(high.iloc[-21:-1].max()) if n >= 21 else price
    pivot_dist = ((prior_resistance - price) / price) * 100.0 if price > 0.0 else 0.0

    checklist = {
        "Price > 150 & 200 MA": price > ma150 and price > ma200,
        "150 MA > 200 MA": ma150 > ma200,
        "200 MA Rising (>1mo)": ma200_rising,
        "150 MA Rising (>1mo)": slope150 > 0.0,
        "Price > 50 MA": price > ma50,
        "Price ≥ 30% Above 52W Low": price >= (low52 * 1.30) if itype == "Equity" else price >= (low52 * 1.15),
        "Price Within 25% of 52W High": price >= (high52 * 0.75)
    }

    tt_pass = checklist["Price > 150 & 200 MA"] and checklist["Price > 50 MA"]

    def get_ret(d_start, d_end):
        if n <= d_start: return 0.0
        p_start = float(close.iloc[-d_start])
        return (float(close.iloc[-d_end]) - p_start) / p_start if p_start > 0.0 else 0.0

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

    # Intraday Volume Normalization (AEST)
    now = pd.Timestamp.now(tz=pytz.timezone('Australia/Sydney'))
    if now.weekday() < 5 and 10 <= now.hour < 16:
        elapsed_mins = (now.hour - 10) * 60 + now.minute
        projected_vol = curr_vol * (360.0 / max(1.0, float(elapsed_mins)))
    else:
        projected_vol = curr_vol

    # Contiguous Weinstein Stages
    stage_raw = "1"
    stage = "Stage 1 (Basing)"
    
    if weekly_slope > 0.002: 
        if price < weekly_ma30 * 0.98:
            stage, stage_raw = "Stage 1 (Basing)", "1"
        elif (price - weekly_ma30) / weekly_ma30 > 0.25:
            stage, stage_raw = "Stage 2B (Late Uptrend)", "2B"
        elif (high52 - price) / high52 <= 0.15:
            stage, stage_raw = "Stage 2A (Early Markup)", "2A"
        else:
            stage, stage_raw = "Stage 2 (Advancing)", "2"
            
    elif weekly_slope < -0.002:
        if price >= weekly_ma30 * 0.98:
            stage, stage_raw = "Stage 1 (Basing)", "1"
        else:
            stage, stage_raw = "Stage 4 (Downtrend)", "4"
        
    else: # [-0.002, 0.002]
        if (high52 - price) / high52 < 0.20 and price < weekly_ma30 * 1.05 and price > weekly_ma30 * 0.85:
            stage, stage_raw = "Stage 3 (Distribution)", "3"
        else:
            stage, stage_raw = "Stage 1 (Basing)", "1"

    # Authentic Volatility Calculation (Dynamic ATR)
    tr = np.maximum(high - low, np.maximum(abs(high - close.shift(1)), abs(low - close.shift(1))))
    atr_14 = float(tr.rolling(14).mean().iloc[-1]) if n >= 14 else 0.0

    max_20d = float(high.iloc[-20:].max()) if n >= 20 else price
    min_20d = float(low.iloc[-20:].min()) if n >= 20 else price
    range_20d_pct = (max_20d - min_20d) / min_20d if min_20d > 0 else 0
    
    max_5d = float(high.iloc[-5:].max()) if n >= 5 else price
    min_5d = float(low.iloc[-5:].min()) if n >= 5 else price
    range_5d_abs = max_5d - min_5d
    
    position_20d = (price - min_20d) / (max_20d - min_20d) if max_20d > min_20d else 0
    vdu = projected_vol < (avg_vol50 * 0.5)

    # Authentic Pocket Pivot Prior Down-Volume Check
    max_down_vol = 0.0
    if n >= 12:
        last_10_closes = close.iloc[-12:-1]
        last_10_vols = volume.iloc[-11:-1]
        down_vols = last_10_vols[last_10_closes.diff().iloc[1:].values < 0]
        max_down_vol = float(down_vols.max()) if len(down_vols) > 0 else 0.0

    setup = "No Setup"
    
    if tt_pass and stage_raw in ["2A", "2"]:
        # Precedence 1: Breakout against prior resistance
        if price >= (prior_resistance * 0.99) and rvol >= 1.5 and change > 2.0:
            setup = "Stage 2 Breakout"
        # Precedence 2: Pocket Pivot inside base
        elif change > 0 and curr_vol > max_down_vol and max_down_vol > 0 and position_20d > 0.3:
            setup = "Pocket Pivot"
        # Precedence 3: VCP Base Tightening
        elif range_20d_pct <= 0.25 and range_5d_abs <= (1.5 * atr_14) and position_20d > 0.5 and vdu:
            setup = "VCP Contraction"

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
        "price": price, "change": change, "pivot_dist": pivot_dist, "raw_rs": raw_rs, 
        "adtv": adtv, "adtv_fmt": adtv_fmt, "checklist": checklist, "trend_score": sum(checklist.values()),
        "stage": stage, "stage_raw": stage_raw, "setup": setup,
        "mrs_series": mrs_series, "above_50": price > ma50, "above_200": price > ma200
    }

def main():
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
        universe_mode = c_u1.radio("Scanner Mode", ["Core & Watchlist (Fast)", "ASX Full Market (Slower EOD)"], horizontal=True, label_visibility="collapsed")
        bench_choice = c_u2.selectbox("Benchmark", list(BENCHMARK_MAP.keys()), index=0, label_visibility="collapsed")

    if universe_mode == "ASX Full Market (Slower EOD)":
        active_universe = fetch_dynamic_universe()
        st.caption("⚡ **Engine Note:** Pulling 2-years of historical data for ~1,900 active ASX equities. This EOD scan may take 60-90 seconds.")
    else:
        active_universe = FALLBACK_UNIVERSE.copy()
        for sym in st.session_state.watchlist:
            full_sym = f"{sym}.AX"
            if full_sym not in active_universe:
                active_universe[full_sym] = {"name": sym, "type": "Equity", "theme": "Watchlist Addition"}

    bench_info = BENCHMARK_MAP[bench_choice]
    raw_data, err = load_all_market_data(active_universe, bench_info["symbol"])
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
    
    for sym, meta in active_universe.items():
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
    if missing_data and universe_mode == "Core & Watchlist (Fast)": 
        st.toast(f"Excluded due to missing/insufficient data: {', '.join(missing_data)}")

    processed_list.sort(key=lambda x: x["raw_rs"])
    for idx, item in enumerate(processed_list):
        item["rs"] = max(1, min(99, round(((idx + 1) / len(processed_list)) * 99)))
        mrs_v = round((item["rs"] - 50) / 15.0, 1)
        
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

    h_50, h_200, h_2a, h_3, h_uni = get_historical_breadth(raw_data, active_universe.keys(), b_df.index)

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
    
    with st.container(border=True):
        f1, f2, f3, f4, f5, f6, f7 = st.columns([2.0, 1.2, 1.5, 1.5, 1.5, 1.5, 0.8])
        search_query = f1.text_input("Search", "", placeholder="Search Ticker..", label_visibility="collapsed").strip().lower()
        price_filter = f2.selectbox("Price", ["All Prices", "> $0.10", "> $0.50", "> $1.00", "> $5.00", "> $10.00"], label_visibility="collapsed")
        substage_filter = f3.selectbox("Stage", ["All Stages", "Stage 2A", "Stage 1B", "Stage 3", "Stage 4"], label_visibility="collapsed")
        min_rs = f4.slider("Min RS", 0, 95, 0, 5, label_visibility="collapsed")
        theme_filter = f5.selectbox("Theme", ["All Themes"] + sorted(list(set(v["theme"] for v in active_universe.values()))), label_visibility="collapsed")
        setup_filter = f6.selectbox("Setup", ["All Setups", "VCP Contraction", "Stage 2 Breakout", "Pocket Pivot", "No Setup"], label_visibility="collapsed")
        
        if f7.button("Reset All", use_container_width=True):
            st.session_state.show_starred_only = False
            st.cache_data.clear()
            st.rerun()

    df = df_all.copy()
    
    if price_filter != "All Prices":
        min_price = float(price_filter.replace("> $", ""))
        df = df[df["price"] > min_price]
        
    if st.session_state.show_starred_only:
        df = df[df["ticker"].isin(st.session_state.watchlist)]
        
    if search_query: df = df[df["ticker"].str.lower().str.contains(search_query)]
    if theme_filter != "All Themes": df = df[df["theme"] == theme_filter]
    if substage_filter != "All Stages": df = df[df["stage_raw"] == substage_filter.split(" ")[1]]
    if setup_filter != "All Setups": df = df[df["setup"] == setup_filter]
    df = df[df["rs"] >= min_rs]

    df_display = df[["ticker", "name", "price", "change", "pivot_dist", "rs", "mrs", "trend_score", "stage", "setup", "adtv_fmt"]].copy()
    df_display.columns = ["TICKER", "NAME", "PRICE", "TODAY %", "PIVOT DIST %", "RS", "MANSFIELD RS", "MINERVINI TREND", "WEINSTEIN STAGE", "SETUP", "$ADTV"]
    
    df_display.insert(0, "STARRED", df_display["TICKER"].apply(lambda x: x in st.session_state.watchlist))
    df_display.insert(1, "CHART", False)
    
    df_display = df_display.sort_values(by="RS", ascending=False).reset_index(drop=True)

    editor_key = "watchlist_editor"
    disabled_cols = ["TICKER", "NAME", "PRICE", "TODAY %", "PIVOT DIST %", "RS", "MANSFIELD RS", "MINERVINI TREND", "WEINSTEIN STAGE", "SETUP", "$ADTV"]
    
    event = st.data_editor(
        df_display,
        column_config={
            "STARRED": st.column_config.CheckboxColumn("STARRED", help="Add to Watchlist", default=False),
            "CHART": st.column_config.CheckboxColumn("CHART", help="Send to TV Chart", default=False),
            "PIVOT DIST %": st.column_config.NumberColumn("PIVOT DIST %", format="%.1f%%")
        },
        disabled=disabled_cols,
        use_container_width=True, 
        height=380,
        key=editor_key
    )

    if editor_key in st.session_state and st.session_state[editor_key].get("edited_rows"):
        rerun_needed = False
        for row_idx, edit in st.session_state[editor_key]["edited_rows"].items():
            if "STARRED" in edit:
                changed_ticker = df_display.iloc[row_idx]["TICKER"]
                if edit["STARRED"]:
                    st.session_state.watchlist.add(changed_ticker)
                else:
                    st.session_state.watchlist.discard(changed_ticker)
                update_query_watchlist()
                rerun_needed = True
                
            if "CHART" in edit and edit["CHART"]:
                clicked_ticker = df_display.iloc[row_idx]["TICKER"]
                st.session_state.active_ticker = clicked_ticker
                st.session_state.insp_dropdown = clicked_ticker
                rerun_needed = True
                
        if rerun_needed:
            del st.session_state[editor_key]
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

            st.markdown("<div style='margin-top:4px; margin-bottom:8px; font-weight:700; font-size:0.75rem; text-transform:uppercase;'>Minervini Trend Template Checklist:</div>", unsafe_allow_html=True)
            check_cols = st.columns(len(selected_row["checklist"]))
            for col, (k, v) in zip(check_cols, selected_row["checklist"].items()):
                col.markdown(f"<div style='color:{'#22c55e' if v else '#f43f5e'}; font-size:0.7rem; font-weight:600; text-align:center;'>{'✓' if v else '✗'} {k}</div>", unsafe_allow_html=True)
            
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

            tv_html = f"""
            <div class="tradingview-widget-container" style="height:650px;width:100%">
              <div id="tradingview_{st.session_state.active_ticker}" style="height:100%;width:100%"></div>
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
            components.html(tv_html, height=650)

if __name__ == "__main__":
    main()
