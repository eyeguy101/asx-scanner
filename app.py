"""
==============================================================================
ASX Momentum, Relative Strength & VCP Scanner (Pro Cloud Edition v6.1)
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
  - Phase 4: Fixed Benchmark Volume NaN crash by isolating subset=["Close"].
  - Phase 4: Implemented Clickable Interactive Dataframe -> Chart sync.
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
    "All Ordinaries (^AXAO)": {"symbol": "^AXAO", "short": "AXAO", "name": "All Ords"},
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
    symbols = list(set(list(UNIVERSE.keys()) + [bench_symbol]))
    try:
        data = yf.download(symbols, period="2y", interval="1d", progress=False, group_by="ticker")
        return data, None
    except Exception as e:
        return None, str(e)

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
        "stage": stage, "stage_raw": stage_raw, "setup": setup, "df_history": df.iloc[-90:].copy(),
        "mrs_series": mrs_series, "above_50": price > ma50, "above_200": price > ma200
    }

def main():
    head_col1, head_col2 = st.columns([8, 2])
    with head_col1:
        st.markdown("""<div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;"><div class="asx-badge">ASX</div>
        <div><div style="font-size:1.35rem; font-weight:800; color:#f8fafc; letter-spacing:-0.02em;">ASX Authentic Momentum Scanner <span style="font-size:0.75rem; font-weight:700; background:rgba(16,185,129,0.2); color:#6ee7b7; border:1px solid rgba(16,185,129,0.3); padding:2px 7px; border-radius:4px; margin-left:6px;">PRO SUITE</span></div>
        <div style="font-size:0.78rem; color:#94a3b8; font-weight:500;">Live Market Breadth • True Weinstein Stages • Volume Dry-Up (VDU)</div></div></div>""", unsafe_allow_html=True)
    with head_col2:
        if st.button("🔄 Refresh Data Feed", use_container_width=True): st.cache_data.clear(); st.rerun()

    with st.container(border=True):
        c_u1, c_u2 = st.columns([3, 7])
        universe_mode = c_u1.radio("Universe", ["All", "Equities", "ETFs"], horizontal=True, label_visibility="collapsed")
        bench_choice = c_u2.selectbox("Benchmark", list(BENCHMARK_MAP.keys()), index=0, label_visibility="collapsed")

    bench_info = BENCHMARK_MAP[bench_choice]
    raw_data, err = load_all_market_data(bench_info["symbol"])
    if err or raw_data is None: st.error(f"Market feed error: {err}"); return

    # Fixed Integrity Check: Dropping subsets of "Close" prevents Volume NaNs from wiping the dataframe
    if bench_info["symbol"] not in raw_data or len(raw_data[bench_info["symbol"]].dropna(subset=["Close"])) < 50:
        st.error(f"Failed to fetch sufficient benchmark data for {bench_info['symbol']}. Halting scan to prevent false regime data.")
        return

    b_df = raw_data[bench_info["symbol"]].dropna(subset=["Close"])
    bench_price, b_prev = float(b_df["Close"].iloc[-1]), float(b_df["Close"].iloc[-2])
    bench_change = ((bench_price - b_prev) / b_prev) * 100.0
    power_trend_on = float(b_df["Close"].ewm(span=21).mean().iloc[-1]) > float(b_df["Close"].rolling(50).mean().iloc[-1])
    bench_spark_vals = b_df["Close"].iloc[-60:].tolist()

    processed_list = []
    missing_data = []
    
    for sym, meta in UNIVERSE.items():
        df_sym = raw_data[sym].dropna(subset=["Close"]) if sym in raw_data else None
        if df_sym is not None and len(df_sym) >= 130:
            m = calculate_metrics(sym, df_sym, b_df["Close"], meta["type"])
            if m:
                clean_ticker = sym.replace(".AX", "")
                m.update({"ticker": clean_ticker, "name": meta["name"], "type": meta["type"], "theme": meta["theme"], "starred": "★" if clean_ticker in st.session_state.watchlist else "☆"})
                processed_list.append(m)
        else:
            missing_data.append(sym)

    if not processed_list: st.warning("No instruments passed data validation."); return
    if missing_data: st.toast(f"Excluded due to missing/insufficient data: {', '.join(missing_data)}")

    processed_list.sort(key=lambda x: x["raw_rs"])
    for idx, item in enumerate(processed_list):
        item["rs"] = max(1, min(99, round(((idx + 1) / len(processed_list)) * 99)))
        mrs_v = round((item["rs"] - 50) / 15.0, 1)
        item["mrs"] = f"+{mrs_v}" if mrs_v >= 0 else f"{mrs_v}"

    df_all = pd.DataFrame(processed_list)

    total_u = len(df_all)
    pct_50 = (df_all["above_50"].sum() / total_u * 100.0) if total_u > 0 else 0.0
    pct_200 = (df_all["above_200"].sum() / total_u * 100.0) if total_u > 0 else 0.0
    stage_2a_count = sum(df_all["stage_raw"] == "2A")
    stage_3_count = sum(df_all["stage_raw"] == "3")

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    
    with k1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title"><span>{bench_info["short"]} REGIME</span><span style="color:#94a3b8;">{bench_price:,.0f} ({bench_change:+.2f}%)</span></div><div class="kpi-val" style="color:{"#22c55e" if power_trend_on else "#f59e0b"};">{"● Power Trend ON" if power_trend_on else "○ Correction"}</div>{make_sparkline_svg(bench_spark_vals, stroke_color="#22c55e" if power_trend_on else "#f59e0b")}</div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title"><span>% &gt; 50-DAY MA</span></div><div class="kpi-val" style="color:#f8fafc;">{pct_50:.1f}%</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title"><span>% &gt; 200-DAY MA</span></div><div class="kpi-val" style="color:#f8fafc;">{pct_200:.1f}%</div></div>', unsafe_allow_html=True)
    with k4:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title"><span>STAGE 2A LEADERS</span></div><div class="kpi-val" style="color:#22c55e;">{stage_2a_count} Breaking Out</div></div>', unsafe_allow_html=True)
    with k5:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title"><span>STAGE 3 DISTRIBUTION</span></div><div class="kpi-val" style="color:#f43f5e;">{stage_3_count} Topping</div></div>', unsafe_allow_html=True)
    with k6:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title"><span>UNIVERSE</span></div><div class="kpi-val" style="color:#c084fc;">{total_u} Scanned</div></div>', unsafe_allow_html=True)

    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        f1, f2, f3, f4, f5 = st.columns(5)
        search_query = f1.text_input("Search", "", placeholder="Search Ticker..", label_visibility="collapsed").strip().lower()
        substage_filter = f2.selectbox("Stage", ["All Stages", "Stage 2A", "Stage 1B", "Stage 3", "Stage 4"], label_visibility="collapsed")
        min_rs = f3.slider("Min RS", 0, 95, 0, 5, label_visibility="collapsed")
        theme_filter = f4.selectbox("Theme", ["All Themes"] + sorted(list(set(v["theme"] for v in UNIVERSE.values()))), label_visibility="collapsed")
        setup_filter = f5.selectbox("Setup", ["All Setups", "VCP Contraction", "Stage 2 Breakout", "Pocket Pivot"], label_visibility="collapsed")

    df = df_all.copy()
    if universe_mode == "Equities": df = df[df["type"] == "Equity"]
    elif universe_mode == "ETFs": df = df[df["type"] == "ETF"]
    if search_query: df = df[df["ticker"].str.lower().str.contains(search_query)]
    if theme_filter != "All Themes": df = df[df["theme"] == theme_filter]
    if substage_filter != "All Stages": df = df[df["stage_raw"] == substage_filter.split(" ")[1]]
    if setup_filter != "All Setups": df = df[df["setup"] == setup_filter]
    df = df[df["rs"] >= min_rs]

    # Structure DataFrame for Display & Selection Map
    df_display = df[["starred", "ticker", "name", "price", "change", "rs", "mrs", "trend_score", "stage", "setup", "adtv_fmt"]].sort_values(by="rs", ascending=False).reset_index(drop=True)

    # Interactive Clickable Dataframe
    event = st.dataframe(
        df_display,
        use_container_width=True, hide_index=True, height=380,
        on_select="rerun",
        selection_mode="single_row"
    )

    # Map selected row to session state
    curr_sel = event.selection.rows
    if curr_sel != st.session_state.last_df_selection:
        st.session_state.last_df_selection = curr_sel
        if curr_sel:
            st.session_state.active_ticker = df_display.iloc[curr_sel[0]]["ticker"]

    if len(df_all) > 0:
        with st.expander("🔍 **Analyze Instrument & 3-Panel Technical Chart**", expanded=True):
            d_col1, d_col2 = st.columns([1.1, 2.1])
            
            all_tickers = sorted(df_all["ticker"].tolist())
            if not st.session_state.active_ticker or st.session_state.active_ticker not in all_tickers:
                st.session_state.active_ticker = all_tickers[0]

            def dropdown_callback():
                st.session_state.active_ticker = st.session_state.insp_dropdown

            sel_idx = all_tickers.index(st.session_state.active_ticker)
            d_col1.selectbox("Select Instrument:", all_tickers, index=sel_idx, key="insp_dropdown", on_change=dropdown_callback)
            
            selected_row = df_all[df_all["ticker"] == st.session_state.active_ticker].iloc[0]

            if d_col1.button("Toggle Watchlist", use_container_width=True):
                if st.session_state.active_ticker in st.session_state.watchlist: st.session_state.watchlist.remove(st.session_state.active_ticker)
                else: st.session_state.watchlist.add(st.session_state.active_ticker)
                update_query_watchlist(); st.rerun()

            d_col1.markdown(f'<a href="https://www.tradingview.com/chart/?symbol=ASX:{st.session_state.active_ticker}" target="_blank"><button style="width:100%; padding:7px; border-radius:6px; background:#1e40af; color:white; font-weight:700; border:none; margin-top:4px;">📈 Open in TradingView</button></a>', unsafe_allow_html=True)
            
            d_col1.markdown("<div style='margin-top:10px; font-weight:700; font-size:0.75rem; text-transform:uppercase;'>Minervini Trend Checklist:</div>", unsafe_allow_html=True)
            for k, v in selected_row["checklist"].items():
                d_col1.markdown(f"<span style='color:{'#22c55e' if v else '#f43f5e'}; font-size:0.75rem; font-weight:600;'>{'✓' if v else '✗'} {k}</span>", unsafe_allow_html=True)

            df_hist = selected_row["df_history"]
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.04, row_heights=[0.55, 0.22, 0.23])

            fig.add_trace(go.Candlestick(x=df_hist.index, open=df_hist["Open"], high=df_hist["High"], low=df_hist["Low"], close=df_hist["Close"], name="Price", increasing_line_color="#089981", decreasing_line_color="#F23645"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_hist.index, y=df_hist["Close"].ewm(span=21).mean(), line=dict(color="#22d3ee", width=1.5)), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_hist.index, y=df_hist["Close"].rolling(50).mean(), line=dict(color="#38bdf8", width=1.5)), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_hist.index, y=df_hist["Close"].rolling(150).mean(), line=dict(color="#fbbf24", width=1.5)), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_hist.index, y=df_hist["Close"].rolling(200).mean(), line=dict(color="#f43f5e", width=1.5)), row=1, col=1)

            v_colors = ["#089981" if df_hist["Close"].iloc[k] >= df_hist["Open"].iloc[k] else "#F23645" for k in range(len(df_hist))]
            fig.add_trace(go.Bar(x=df_hist.index, y=df_hist["Volume"], marker_color=v_colors), row=2, col=1)
            fig.add_trace(go.Scatter(x=df_hist.index, y=df_hist["Volume"].rolling(50).mean(), line=dict(color="#94a3b8", width=1.2)), row=2, col=1)

            mrs_data = selected_row["mrs_series"]
            if len(mrs_data) == len(df_hist):
                fig.add_trace(go.Scatter(x=df_hist.index, y=mrs_data, line=dict(color="#10b981", width=1.8)), row=3, col=1)
                fig.add_hline(y=0.0, line_dash="dash", line_color="#94a3b8", line_width=1, row=3, col=1)

            fig.update_layout(template="plotly_dark", height=480, margin=dict(l=10, r=10, t=30, b=10), xaxis_rangeslider_visible=False, showlegend=False, hovermode="x unified")
            d_col2.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
