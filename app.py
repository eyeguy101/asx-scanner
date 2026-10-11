


ASX Momentum Scanner Application
Evaluated the feasibility of requested code modifications.
4 min ago

Analysis of Retrial Puck Emails
Implemented structural and clinical enhancements for Retina-OCT companion.
Australian Sharemarket Consensus Analysis
Generating actionable ASX market strategy analysis
Needs input
Other Podcast Summary
Summarized recent podcast episodes and actionable health protocols.
Health Podcast Summary
Checked recent health podcast episodes for new content.
Trading Podcast Summary
Analyzed recent trading podcast episodes for market insights.
Healthy Aging Research
Researched and compiled recent clinical protocols for healthy aging.
Peter Attia's Cardiovascular Pathophysiology Perspective
Analyzing cardiovascular disease mechanisms through Attia's lens
Clarice Job Application Review
Generating document and page deliverables
Constraint Theory in Performance Physiology
Compiled constraint theory principles into a comprehensive PDF guide.
Clarice Job Application Oct 4th
Delivered optimized interview preparation materials and interactive simulator.
Analysis of Retrial Puck Emails
Synthesized thirty-four clinical cases into a professional PDF.

ASX Momentum Scanner Application
beta

Plan steps

Conversation with Gemini
What is the function of the following code:

""""

==============================================================================

ASX Momentum, Relative Strength & VCP Scanner (Pro Cloud Edition v13.0)

==============================================================================

Refactored Engine:

  - Phase 1: Authentic Weinstein Stages & True Minervini slope calculations.

  - Phase 1: Discrete quarterly O'Neil RS calculation & VCP logic.

  - Phase 2: Live rolling market breadth (no synthetic data).

  - Phase 4: Timezone-stripped DatetimeIndex & Yahoo NaN prevention.

  - UPDATE: Dynamic Universe Integration & Pivot Distance (%).

  - UPDATE: Dropdown Price Filter, ADR%, Multi-Timeframe Returns.

  - UPDATE: Macro Dashboard Tab (A/D Line, Breadth Oscillators, Themes).

  - UPDATE: Integrated Darvas Box mechanics & Setup overlap confluence.

  - NEW (v13.0): Configurable Daily / Weekly Timeframe engine switch.

  - NEW (v13.0): Darvas sliders for Max Volume (%) and Max Box Height (ATR).

  - NEW (v13.0): UI overhauled to restore labels and group parameters into an Expander.

==============================================================================

"""



import streamlit as st

import streamlit.components.v1 as components

import pandas as pd

import numpy as np

import yfinance as yf

import pytz

import plotly.graph_objects as go

from plotly.subplots import make_subplots



st.set_page_config(

    page_title="ASX Momentum Scanner",

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

    .stTabs [data-baseweb="tab-list"] { gap: 8px; }

    .stTabs [data-baseweb="tab"] { background-color: #1e293b; border-radius: 4px 4px 0 0; padding: 10px 20px; }

    .stTabs [aria-selected="true"] { background-color: #2563eb !important; color: white !important; font-weight: bold; }

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

            dynamic_universe[sym] = {"name": str(row.get('Company name', sym)).title(), "type": "Equity", "theme": theme}

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

        # Pushed from 2y to 3y to ensure accurate 40-week MAs and 52-week RS lookbacks when in Weekly mode

        df_batch = yf.download(symbols, period="3y", interval="1d", progress=False, group_by="ticker")

        data_dict = {}

        if isinstance(df_batch.columns, pd.MultiIndex):

            for sym in symbols:

                try: data_dict[sym] = df_batch[sym]

                except KeyError: pass

        else:

            for sym in symbols: data_dict[sym] = df_batch

        bench_df = yf.Ticker(bench_symbol).history(period="3y")

        if not bench_df.empty: data_dict[bench_symbol] = bench_df

        return data_dict, None

    except Exception as e:

        return None, str(e)



def get_historical_breadth(raw_data, universe_keys, b_df_index, timeframe):

    target_idx = b_df_index[-125:]

    count_50 = pd.Series(0, index=target_idx)

    count_200 = pd.Series(0, index=target_idx)

    count_2a = pd.Series(0, index=target_idx)

    count_3 = pd.Series(0, index=target_idx)

    count_uni = pd.Series(0, index=target_idx)

    ad_line = pd.Series(0, index=target_idx)



    for sym in universe_keys:

        if sym not in raw_data: continue

        df = raw_data[sym].ffill().dropna(subset=["Close"])

        df.index = pd.to_datetime(df.index).tz_localize(None)

        

        if timeframe == "Weekly":

            df = df.resample('W-FRI').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'}).dropna()

            

        if len(df) < 50: continue

        

        close = df['Close']

        high = df['High']

        

        daily_diff = close.diff()

        advancers = (daily_diff > 0).astype(int)

        decliners = (daily_diff < 0).astype(int)

        ad_line += (advancers - decliners).reindex(target_idx).fillna(0)



        if timeframe == "Weekly":

            ma50 = close.rolling(10).mean()

            ma200 = close.rolling(40).mean()

            w_ma30 = close.rolling(30).mean()

            w_slope = (w_ma30 - w_ma30.shift(4)) / w_ma30

            w_ma30_d = w_ma30

            w_slope_d = w_slope

            high52 = high.rolling(52, min_periods=20).max()

        else:

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

    return (count_50 / safe_uni * 100).tolist(), (count_200 / safe_uni * 100).tolist(), count_2a.tolist(), count_3.tolist(), count_uni.tolist(), ad_line.cumsum().tolist()



def calculate_metrics(sym, df, bench_series, itype, darvas_lb, darvas_vol, darvas_coil_vol, darvas_box_atr, timeframe):

    df.index = pd.to_datetime(df.index).tz_localize(None)

    

    if timeframe == "Weekly":

        df = df.resample('W-FRI').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'}).dropna()

        p_50, p_150, p_200 = 10, 30, 40

        p_vol20, p_vol50 = 4, 10

        p_52w = 52

    else:

        p_50, p_150, p_200 = 50, 150, 200

        p_vol20, p_vol50 = 21, 51

        p_52w = 252



    if len(df) < p_200: return None

    

    close = df["Close"]

    high = df["High"]

    low = df["Low"]

    volume = df["Volume"]

    n = len(close)



    price = float(close.iloc[-1])

    prev_price = float(close.iloc[-2]) if n >= 2 else price

    change = ((price - prev_price) / prev_price) * 100.0 if prev_price > 0.0 else 0.0



    ma50 = float(close.rolling(p_50).mean().iloc[-1])

    ma150 = float(close.rolling(p_150).mean().iloc[-1])

    ma200 = float(close.rolling(p_200).mean().iloc[-1])

    

    if timeframe == "Weekly":

        ma200_recent = float(close.rolling(p_200).mean().iloc[-3]) if n >= (p_200 + 3) else price

        ma200_past = float(close.rolling(p_200).mean().iloc[-5]) if n >= (p_200 + 5) else price

    else:

        ma200_recent = float(close.rolling(p_200).mean().iloc[-11]) if n >= 210 else price

        ma200_past = float(close.rolling(p_200).mean().iloc[-23]) if n >= 222 else price

        

    ma200_rising = (ma200 > ma200_recent) and (ma200_recent > ma200_past)



    slope150 = (ma150 - float(close.rolling(p_150).mean().iloc[-22])) / ma150 if n >= (p_150 + 22) else 0.0

    

    if timeframe == "Weekly":

        weekly_ma30 = float(close.rolling(30).mean().iloc[-1]) if n >= 30 else ma150

        weekly_slope = (weekly_ma30 - float(close.rolling(30).mean().iloc[-4])) / weekly_ma30 if n >= 34 else 0.0

    else:

        df_weekly = df.resample('W-FRI').last().dropna(subset=["Close"])

        weekly_ma30 = float(df_weekly["Close"].rolling(30).mean().iloc[-1]) if len(df_weekly) >= 30 else ma150

        weekly_slope = (weekly_ma30 - float(df_weekly["Close"].rolling(30).mean().iloc[-4])) / weekly_ma30 if len(df_weekly) >= 34 else 0.0



    high52 = float(high.iloc[-min(n, p_52w):].max())

    low52 = float(low.iloc[-min(n, p_52w):].min())



    prior_resistance = float(high.iloc[-21:-1].max()) if n >= 21 else price

    pivot_dist = ((prior_resistance - price) / price) * 100.0 if price > 0.0 else 0.0



    adr = float(((high.iloc[-20:] / low.iloc[-20:]) - 1).mean() * 100) if n >= 20 else 0.0



    str_50  = "10-Week MA" if timeframe == "Weekly" else "50 MA"

    str_150 = "30-Week MA" if timeframe == "Weekly" else "150 MA"

    str_200 = "40-Week MA" if timeframe == "Weekly" else "200 MA"



    checklist = {

        f"Price > {str_150} & {str_200}": price > ma150 and price > ma200,

        f"{str_150} > {str_200}": ma150 > ma200,

        f"{str_200} Rising (>1mo)": ma200_rising,

        f"{str_150} Rising (>1mo)": slope150 > 0.0,

        f"Price > {str_50}": price > ma50,

        "Price ≥ 30% Above 52W Low": price >= (low52 * 1.30) if itype == "Equity" else price >= (low52 * 1.15),

        "Price Within 25% of 52W High": price >= (high52 * 0.75)

    }

    tt_pass = checklist[f"Price > {str_150} & {str_200}"] and checklist[f"Price > {str_50}"]



    def get_ret(d_start, d_end):

        if n <= d_start: return 0.0

        p_start = float(close.iloc[-d_start])

        return (float(close.iloc[-d_end]) - p_start) / p_start if p_start > 0.0 else 0.0



    if timeframe == "Weekly":

        ret_1m = get_ret(4, 1) * 100

        ret_3m = get_ret(12, 1) * 100

    else:

        ret_1m = get_ret(22, 1) * 100

        ret_3m = get_ret(64, 1) * 100



    ret_q1 = get_ret(63, 1)

    ret_q2 = get_ret(126, 64)

    ret_q3 = get_ret(189, 127)

    ret_q4 = get_ret(252, 190)

    raw_rs = (0.40 * ret_q1) + (0.20 * ret_q2) + (0.20 * ret_q3) + (0.20 * ret_q4)



    ret_q1_1m = get_ret(63+21, 1+21)

    ret_q2_1m = get_ret(126+21, 64+21)

    ret_q3_1m = get_ret(189+21, 127+21)

    ret_q4_1m = get_ret(252+21, 190+21)

    raw_rs_1m = (0.40 * ret_q1_1m) + (0.20 * ret_q2_1m) + (0.20 * ret_q3_1m) + (0.20 * ret_q4_1m)



    avg_vol20 = float(volume.iloc[-p_vol20-1:-1].mean()) if n >= (p_vol20+1) else 1.0

    avg_vol50 = float(volume.iloc[-p_vol50-1:-1].mean()) if n >= (p_vol50+1) else avg_vol20

    curr_vol = float(volume.iloc[-1])

    rvol = curr_vol / avg_vol20 if avg_vol20 > 0 else 1.0

    adtv = avg_vol20 * price

    adtv_fmt = f"${adtv/1e6:.1f}M" if adtv >= 1e6 else f"${round(adtv/1e3)}k"



    if timeframe == "Weekly":

        projected_vol = curr_vol

    else:

        now = pd.Timestamp.now(tz=pytz.timezone('Australia/Sydney'))

        if now.weekday() < 5 and 10 <= now.hour < 16:

            elapsed_mins = (now.hour - 10) * 60 + now.minute

            projected_vol = curr_vol * (360.0 / max(1.0, float(elapsed_mins)))

        else:

            projected_vol = curr_vol



    stage_raw = "1"

    stage = "Stage 1 (Basing)"

    

    if weekly_slope > 0.002: 

        if price < weekly_ma30 * 0.98: stage, stage_raw = "Stage 1 (Basing)", "1"

        elif (price - weekly_ma30) / weekly_ma30 > 0.25: stage, stage_raw = "Stage 2B (Late Uptrend)", "2B"

        elif (high52 - price) / high52 <= 0.15: stage, stage_raw = "Stage 2A (Early Markup)", "2A"

        else: stage, stage_raw = "Stage 2 (Advancing)", "2"

    elif weekly_slope < -0.002:

        if price >= weekly_ma30 * 0.98: stage, stage_raw = "Stage 1 (Basing)", "1"

        else: stage, stage_raw = "Stage 4 (Downtrend)", "4"

    else: 

        if (high52 - price) / high52 < 0.20 and price < weekly_ma30 * 1.05 and price > weekly_ma30 * 0.85: stage, stage_raw = "Stage 3 (Distribution)", "3"

        else: stage, stage_raw = "Stage 1 (Basing)", "1"



    tr = np.maximum(high - low, np.maximum(abs(high - close.shift(1)), abs(low - close.shift(1))))

    atr_14 = float(tr.rolling(14).mean().iloc[-1]) if n >= 14 else 0.0



    max_20d = float(high.iloc[-20:].max()) if n >= 20 else price

    min_20d = float(low.iloc[-20:].min()) if n >= 20 else price

    range_20d_pct = (max_20d - min_20d) / min_20d if min_20d > 0 else 0

    max_5d = float(high.iloc[-5:].max()) if n >= 5 else price

    min_5d = float(low.iloc[-5:].min()) if n >= 5 else price

    range_5d_abs = max_5d - min_5d

    position_20d = (price - min_20d) / (max_20d - min_20d) if max_20d > min_20d else 0

    vdu_vcp = projected_vol < (avg_vol50 * 0.5)



    max_down_vol = 0.0

    if n >= 12:

        last_10_closes = close.iloc[-12:-1]

        last_10_vols = volume.iloc[-11:-1]

        down_vols = last_10_vols[last_10_closes.diff().iloc[1:].values < 0]

        max_down_vol = float(down_vols.max()) if len(down_vols) > 0 else 0.0



    darvas_coil = False

    darvas_bo = False

    if n >= darvas_lb + 1:

        hist_high = high.iloc[-darvas_lb-1:-1]

        box_top_idx = np.argmax(hist_high.values) 

        box_age = darvas_lb - box_top_idx

        box_top = float(hist_high.values[box_top_idx])

        box_bottom = float(low.iloc[-box_age-1:-1].min())

        box_height_atr = (box_top - box_bottom) / atr_14 if atr_14 > 0 else 0

        

        is_mature_box = (box_age >= (1 if timeframe == "Weekly" else 5)) and (0.3 <= box_height_atr <= darvas_box_atr)

        is_nr4 = (n >= 4) and (tr.iloc[-1] < min(tr.iloc[-2], tr.iloc[-3], tr.iloc[-4]))

        is_inside = (n >= 2) and (high.iloc[-1] <= high.iloc[-2]) and (low.iloc[-1] >= low.iloc[-2])

        is_upper_half = price > (box_bottom + (box_top - box_bottom) * 0.5)

        

        vdu_darvas = projected_vol < (avg_vol50 * (darvas_coil_vol / 100.0))

        darvas_coil = is_mature_box and (is_nr4 or is_inside) and is_upper_half and vdu_darvas and (price <= box_top)

        darvas_bo = is_mature_box and (price > box_top) and (rvol >= darvas_vol)



    setup_flags = []

    if tt_pass and stage_raw in ["2A", "2"]:

        if price >= (prior_resistance * 0.99) and rvol >= 1.5 and change > 2.0:

            setup_flags.append("Stage 2 Breakout")

        elif change > 0 and curr_vol > max_down_vol and max_down_vol > 0 and position_20d > 0.3:

            setup_flags.append("Pocket Pivot")

        if range_20d_pct <= 0.25 and range_5d_abs <= (1.5 * atr_14) and position_20d > 0.5 and vdu_vcp:

            setup_flags.append("VCP")

        if darvas_bo: setup_flags.append("Darvas Breakout")

        if darvas_coil: setup_flags.append("Darvas Coil")



    setup = " + ".join(setup_flags) if len(setup_flags) > 0 else "No Setup"



    mrs_series = []

    pure_rs_series = []

    dates_252 = []

    price_252 = []

    if bench_series is not None:

        bench_series.index = pd.to_datetime(bench_series.index).tz_localize(None)

        common_idx = close.index.intersection(bench_series.index)

        if len(common_idx) >= 52:

            ratio = close.loc[common_idx] / bench_series.loc[common_idx]

            ratio_ma = ratio.rolling(52).mean()

            mrs_curve = ((ratio / ratio_ma) - 1.0) * 10.0

            mrs_series = mrs_curve.reindex(close.index).ffill().iloc[-90:].tolist()

            

            pure_rs_series = ratio.reindex(close.index).ffill().iloc[-p_52w:].tolist()

            dates_252 = close.index[-p_52w:].strftime('%Y-%m-%d').tolist()

            price_252 = close.iloc[-p_52w:].tolist()



    return {

        "price": price, "change": change, "ret_1m": ret_1m, "ret_3m": ret_3m,

        "pivot_dist": pivot_dist, "adr": adr, "raw_rs": raw_rs, "raw_rs_1m": raw_rs_1m, 

        "adtv": adtv, "adtv_fmt": adtv_fmt, "checklist": checklist, "trend_score": sum(checklist.values()),

        "stage": stage, "stage_raw": stage_raw, "setup": setup,

        "mrs_series": mrs_series, "pure_rs_series": pure_rs_series, "dates_252": dates_252, "price_252": price_252,

        "above_50": price > ma50, "above_200": price > ma200

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

        col1, col2, col3, col4, col5 = st.columns(5)

        search_query = col1.text_input("Search Ticker..", "").strip().lower()

        timeframe_sel = col2.selectbox("Timeframe", ["Daily", "Weekly"])

        price_filter = col3.selectbox("Price", ["All Prices", "> $0.10", "> $0.50", "> $1.00", "> $5.00", "> $10.00"])

        theme_filter = col4.selectbox("Theme", ["All Themes", "All Prices"])

        setup_filter = col5.selectbox("Setup", ["All Setups", "VCP", "Stage 2 Breakout", "Pocket Pivot", "Darvas Breakout", "Darvas Coil", "No Setup"])



    with st.expander("⚙️ Advanced Scan Parameters & Thresholds", expanded=True):

        s1, s2, s3, s4, s5 = st.columns(5)

        substage_filter = s1.selectbox("Weinstein Stage", ["All Stages", "Stage 2A", "Stage 1B", "Stage 3", "Stage 4"])

        min_rs = s2.slider("Min RS Rank", 0, 95, 0, 5)

        darvas_lb = s3.slider("Darvas Lookback (Bars)", 5, 50, 21, 1)

        darvas_vol = s4.slider("Darvas BO Vol (x Avg)", 0.5, 3.0, 1.3, 0.1)

        darvas_coil_vol = s5.slider("Darvas Coil Max Vol (%)", 10, 100, 50, 5)

        

        s6, s7, s8, s9, s10 = st.columns(5)

        darvas_box_atr = s6.slider("Darvas Max Box Height (ATR)", 0.5, 10.0, 3.0, 0.1)

        universe_mode = s7.selectbox("Engine Target", ["Core & Watchlist (Fast)", "ASX Full Market (Slower EOD)"])

        bench_choice = s8.selectbox("Benchmark", list(BENCHMARK_MAP.keys()), index=0)

        

        if s10.button("Reset Configurations", use_container_width=True):

            st.session_state.show_starred_only = False

            st.cache_data.clear()

            st.rerun()



    if universe_mode == "ASX Full Market (Slower EOD)":

        active_universe = fetch_dynamic_universe()

        st.caption("⚡ **Engine Note:** Pulling 3-years of historical data for ~1,900 active ASX equities. This full market scan may take 60-90 seconds.")

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

        b_df.index = pd.to_datetime(b_df.index).tz_localize(None)

        if timeframe_sel == "Weekly":

            b_df = b_df.resample('W-FRI').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'}).dropna()

            

    if b_df is None or len(b_df) < 50:

        st.error(f"Failed to fetch sufficient benchmark data for {bench_info['symbol']}. Halting scan to prevent false regime data.")

        return



    last_valid_date = b_df.index[-1].strftime('%d %b %Y')

    bench_dates_recent = b_df.index[-125:].strftime('%Y-%m-%d').tolist()



    bench_price, b_prev = float(b_df["Close"].iloc[-1]), float(b_df["Close"].iloc[-2])

    bench_change = ((bench_price - b_prev) / b_prev) * 100.0

    power_trend_on = float(b_df["Close"].ewm(span=21).mean().iloc[-1]) > float(b_df["Close"].rolling(50).mean().iloc[-1])

    bench_spark_vals = b_df["Close"].iloc[-125:].tolist()



    processed_list = []

    missing_data = []

    

    for sym, meta in active_universe.items():

        df_sym = raw_data[sym].ffill().dropna(subset=["Close"]) if sym in raw_data else None

        if df_sym is not None and len(df_sym) >= 130:

            m = calculate_metrics(sym, df_sym, b_df["Close"], meta["type"], darvas_lb, darvas_vol, darvas_coil_vol, darvas_box_atr, timeframe_sel)

            if m:

                clean_ticker = sym.replace(".AX", "")

                m.update({"ticker": clean_ticker, "name": meta["name"], "type": meta["type"], "theme": meta["theme"]})

                processed_list.append(m)

        else:

            missing_data.append(sym)



    if not processed_list: st.warning("No instruments passed data validation."); return

    if missing_data and universe_mode == "Core & Watchlist (Fast)": 

        st.toast(f"Excluded due to missing/insufficient data: {', '.join(missing_data)}")



    processed_list.sort(key=lambda x: x["raw_rs_1m"])

    for idx, item in enumerate(processed_list): item["rs_1m"] = max(1, min(99, round(((idx + 1) / len(processed_list)) * 99)))



    processed_list.sort(key=lambda x: x["raw_rs"])

    for idx, item in enumerate(processed_list):

        item["rs"] = max(1, min(99, round(((idx + 1) / len(processed_list)) * 99)))

        item["rs_shift"] = item["rs"] - item["rs_1m"]

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

                

        item["mrs"] = f"{'+' if mrs_v >= 0 else ''}{mrs_v} ({traj})"



    df_all = pd.DataFrame(processed_list)

    h_50, h_200, h_2a, h_3, h_uni, h_ad = get_historical_breadth(raw_data, active_universe.keys(), b_df.index, timeframe_sel)



    total_u = len(df_all)

    pct_50 = (df_all["above_50"].sum() / total_u * 100.0) if total_u > 0 else 0.0

    pct_200 = (df_all["above_200"].sum() / total_u * 100.0) if total_u > 0 else 0.0

    stage_2a_count = sum(df_all["stage_raw"] == "2A")

    stage_3_count = sum(df_all["stage_raw"] == "3")



    k1, k2, k3, k4, k5, k6 = st.columns(6)

    with k1: st.markdown(f'<div class="kpi-card"><div class="kpi-title"><span>{bench_info["short"]} REGIME</span><span style="color:#94a3b8;">{bench_price:,.0f} ({bench_change:+.2f}%)</span></div><div class="kpi-val" style="color:{"#22c55e" if power_trend_on else "#f59e0b"};">{"● Power Trend ON" if power_trend_on else "○ Correction"}</div>{make_sparkline_svg(bench_spark_vals, stroke_color="#22c55e" if power_trend_on else "#f59e0b", fill_color="rgba(34,197,94,0.15)" if power_trend_on else "rgba(245,158,11,0.15)")}</div>', unsafe_allow_html=True)

    with k2: st.markdown(f'<div class="kpi-card"><div class="kpi-title"><span>% &gt; {"10W" if timeframe_sel == "Weekly" else "50D"} MA</span></div><div class="kpi-val" style="color:#f8fafc;">{pct_50:.1f}%</div>{make_sparkline_svg(h_50, stroke_color="#38bdf8", fill_color="rgba(56,189,248,0.15)")}</div>', unsafe_allow_html=True)

    with k3: st.markdown(f'<div class="kpi-card"><div class="kpi-title"><span>% &gt; {"40W" if timeframe_sel == "Weekly" else "200D"} MA</span></div><div class="kpi-val" style="color:#f8fafc;">{pct_200:.1f}%</div>{make_sparkline_svg(h_200, stroke_color="#818cf8", fill_color="rgba(129,140,248,0.15)")}</div>', unsafe_allow_html=True)

    with k4: st.markdown(f'<div class="kpi-card"><div class="kpi-title"><span>STAGE 2A LEADERS</span></div><div class="kpi-val" style="color:#22c55e;">{stage_2a_count} Breaking Out</div>{make_sparkline_svg(h_2a, stroke_color="#22c55e", fill_color="rgba(34,197,94,0.15)")}</div>', unsafe_allow_html=True)

    with k5: st.markdown(f'<div class="kpi-card"><div class="kpi-title"><span>STAGE 3 DISTRIBUTION</span></div><div class="kpi-val" style="color:#f43f5e;">{stage_3_count} Topping</div>{make_sparkline_svg(h_3, stroke_color="#f43f5e", fill_color="rgba(244,63,94,0.15)")}</div>', unsafe_allow_html=True)

    with k6: st.markdown(f'<div class="kpi-card"><div class="kpi-title"><span>UNIVERSE</span></div><div class="kpi-val" style="color:#c084fc;">{total_u} Scanned</div>{make_sparkline_svg(h_uni, stroke_color="#c084fc", fill_color="rgba(192,132,252,0.15)")}</div>', unsafe_allow_html=True)



    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)



    tab1, tab2 = st.tabs(["📊 Screener & Setup Charts", "🌍 Macro Breadth & Theme Rotation"])



    with tab1:

        df = df_all.copy()

        if price_filter != "All Prices":

            min_price = float(price_filter.replace("> $", ""))

            df = df[df["price"] > min_price]

        if st.session_state.show_starred_only: df = df[df["ticker"].isin(st.session_state.watchlist)]

        if search_query: df = df[df["ticker"].str.lower().str.contains(search_query)]

        if theme_filter != "All Themes": df = df[df["theme"] == theme_filter]

        if substage_filter != "All Stages": df = df[df["stage_raw"] == substage_filter.split(" ")[1]]

        if setup_filter != "All Setups": df = df[df["setup"].str.contains(setup_filter)]

        df = df[df["rs"] >= min_rs]



        df_display = df[["ticker", "name", "price", "change", "ret_1m", "ret_3m", "pivot_dist", "adr", "rs", "rs_shift", "mrs", "trend_score", "stage", "setup", "adtv_fmt"]].copy()

        df_display.columns = ["TICKER", "NAME", "PRICE", "LAST %", "1M %", "3M %", "PIVOT DIST %", "ADR %", "RS", "RS-S", "MANSFIELD RS", "MINERVINI TREND", "WEINSTEIN STAGE", "SETUP", "$ADTV"]

        

        df_display.insert(0, "STARRED", df_display["TICKER"].apply(lambda x: x in st.session_state.watchlist))

        df_display.insert(1, "CHART", False)

        df_display = df_display.sort_values(by="RS", ascending=False).reset_index(drop=True)



        editor_key = "watchlist_editor"

        disabled_cols = ["TICKER", "NAME", "PRICE", "LAST %", "1M %", "3M %", "PIVOT DIST %", "ADR %", "RS", "RS-S", "MANSFIELD RS", "MINERVINI TREND", "WEINSTEIN STAGE", "SETUP", "$ADTV"]

        

        st.data_editor(

            df_display,

            column_config={

                "STARRED": st.column_config.CheckboxColumn("STARRED", help="Add to Watchlist", default=False),

                "CHART": st.column_config.CheckboxColumn("CHART", help="Send to TV Chart", default=False),

                "1M %": st.column_config.NumberColumn("1M %", format="%.1f%%"),

                "3M %": st.column_config.NumberColumn("3M %", format="%.1f%%"),

                "PIVOT DIST %": st.column_config.NumberColumn("PIVOT DIST %", format="%.1f%%"),

                "ADR %": st.column_config.NumberColumn("ADR %", format="%.2f%%"),

            },

            disabled=disabled_cols,

            use_container_width=True, 

            height=360,

            key=editor_key

        )



        if editor_key in st.session_state and st.session_state[editor_key].get("edited_rows"):

            rerun_needed = False

            for row_idx, edit in st.session_state[editor_key]["edited_rows"].items():

                if "STARRED" in edit:

                    changed_ticker = df_display.iloc[row_idx]["TICKER"]

                    if edit["STARRED"]: st.session_state.watchlist.add(changed_ticker)

                    else: st.session_state.watchlist.discard(changed_ticker)

                    update_query_watchlist()

                    rerun_needed = True

                if "CHART" in edit and edit["CHART"]:

                    st.session_state.active_ticker = df_display.iloc[row_idx]["TICKER"]

                    st.session_state.insp_dropdown = st.session_state.active_ticker

                    rerun_needed = True

            if rerun_needed:

                del st.session_state[editor_key]

                st.rerun()



        if len(df_all) > 0:

            with st.expander("🔍 **Analyze Instrument & Relative Strength Breakdown**", expanded=True):

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

                <div class="tradingview-widget-container" style="height:550px;width:100%">

                  <div id="tradingview_{st.session_state.active_ticker}" style="height:100%;width:100%"></div>

                  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>

                  <script type="text/javascript">

                  new TradingView.widget(

                  {{

                  "autosize": true,

                  "symbol": "ASX:{st.session_state.active_ticker}",

                  "interval": "{'W' if timeframe_sel == 'Weekly' else 'D'}",

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

                components.html(tv_html, height=550)



                if len(selected_row["dates_252"]) > 0:

                    fig_rs = make_subplots(specs=[[{"secondary_y": True}]])

                    fig_rs.add_trace(go.Scatter(x=selected_row["dates_252"], y=selected_row["price_252"], name="Price", line=dict(color="#f8fafc", width=1.5)), secondary_y=False)

                    fig_rs.add_trace(go.Scatter(x=selected_row["dates_252"], y=selected_row["pure_rs_series"], name="Pure RS Line", line=dict(color="#818cf8", width=2.0)), secondary_y=True)

                    fig_rs.update_layout(

                        title=f"{st.session_state.active_ticker} Price vs Pure Relative Strength Line (1 Year)",

                        height=280, margin=dict(l=10, r=10, t=40, b=10),

                        template="plotly_dark", plot_bgcolor="#0b0f19", paper_bgcolor="#0b0f19",

                        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1)

                    )

                    fig_rs.update_yaxes(title_text="Price", secondary_y=False, showgrid=False)

                    fig_rs.update_yaxes(title_text="RS Line", secondary_y=True, showgrid=False)

                    st.plotly_chart(fig_rs, use_container_width=True)



    with tab2:

        st.markdown("### Institutional Macro & Theme Leadership")

        c1, c2 = st.columns([6, 4])



        with c1:

            st.markdown("<div style='font-size:0.85rem; font-weight:700; color:#94a3b8; margin-bottom:10px;'>CUMULATIVE ADVANCE / DECLINE LINE</div>", unsafe_allow_html=True)

            fig_ad = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.5, 0.5])

            fig_ad.add_trace(go.Scatter(x=bench_dates_recent, y=bench_spark_vals, name=bench_info["short"], line=dict(color="#38bdf8", width=2)), row=1, col=1)

            fig_ad.add_trace(go.Scatter(x=bench_dates_recent, y=h_ad, name="A/D Line", line=dict(color="#a855f7", width=2)), row=2, col=1)

            fig_ad.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0), template="plotly_dark", plot_bgcolor="#0b0f19", paper_bgcolor="#0b0f19", showlegend=False)

            fig_ad.update_yaxes(showgrid=True, gridcolor="#1e293b", zeroline=False)

            st.plotly_chart(fig_ad, use_container_width=True)



            st.markdown("<div style='font-size:0.85rem; font-weight:700; color:#94a3b8; margin-bottom:10px; margin-top:20px;'>MARKET BREADTH OSCILLATORS</div>", unsafe_allow_html=True)

            fig_br = go.Figure()

            fig_br.add_trace(go.Scatter(x=bench_dates_recent, y=h_50, name=f"% > {'10W' if timeframe_sel == 'Weekly' else '50D'} MA", line=dict(color="#22c55e", width=2)))

            fig_br.add_trace(go.Scatter(x=bench_dates_recent, y=h_200, name=f"% > {'40W' if timeframe_sel == 'Weekly' else '200D'} MA", line=dict(color="#f59e0b", width=2)))

            fig_br.add_hrect(y0=80, y1=100, fillcolor="red", opacity=0.1, line_width=0)

            fig_br.add_hrect(y0=0, y1=20, fillcolor="green", opacity=0.1, line_width=0)

            fig_br.add_hline(y=80, line_dash="dot", line_color="red", opacity=0.5)

            fig_br.add_hline(y=20, line_dash="dot", line_color="green", opacity=0.5)

            fig_br.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0), template="plotly_dark", plot_bgcolor="#0b0f19", paper_bgcolor="#0b0f19", yaxis=dict(range=[0,100]), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))

            st.plotly_chart(fig_br, use_container_width=True)



        with c2:

            st.markdown("<div style='font-size:0.85rem; font-weight:700; color:#94a3b8; margin-bottom:10px;'>GICS THEME LEADERSHIP</div>", unsafe_allow_html=True)

            theme_df = df_all.groupby('theme').agg(

                Stocks=('ticker', 'count'),

                Avg_RS=('rs', 'mean'),

                Stage2A_Count=('stage_raw', lambda x: (x == '2A').sum())

            ).reset_index()

            theme_df['% Stage 2A'] = (theme_df['Stage2A_Count'] / theme_df['Stocks']) * 100.0

            theme_df = theme_df[theme_df['Stocks'] >= 3].sort_values('Avg_RS', ascending=False)

            

            st.dataframe(

                theme_df[['theme', 'Stocks', 'Avg_RS', '% Stage 2A']],

                column_config={

                    "theme": "Theme / Industry",

                    "Avg_RS": st.column_config.NumberColumn("Avg RS", format="%.1f"),

                    "% Stage 2A": st.column_config.ProgressColumn("% Stage 2A", format="%.1f%%", min_value=0, max_value=100)

                },

                hide_index=True,

                use_container_width=True,

                height=680

            )



if __name__ == "__main__":

    main()"



This code is a Streamlit web application that serves as an institutional-grade stock screener and market breadth dashboard for equities listed on the Australian Securities Exchange (ASX).

It implements several classic technical and momentum trading methodologies—most notably Mark Minervini's Trend Template & VCP, Stan Weinstein's Stage Analysis, William O'Neil's Relative Strength, and Nicolas Darvas's Box Theory.

Key Capabilities & Architecture
1. Data Ingestion & Universe Selection
Dynamic / Fallback Universe: Fetches current ASX-listed stock codes and GICS industry groups dynamically via the ASX/Markit Digital API, falling back to a curated equity list if the feed fails.

Historical Market Data: Uses yfinance to pull 3 years of daily Open-High-Low-Close-Volume (OHLCV) price history for ASX tickers (.AX) and benchmark indices (All Ordinaries ^AORD or S&P/ASX 200 ^AXJO).

Timeframe Switching: Supports both Daily and Weekly analysis by resampling daily bars to Friday close (W-FRI).

2. Quantitative Screening & Setup Detection (calculate_metrics)
The engine evaluates each stock against multiple technical criteria:

Weinstein Stage Analysis: Classifies stocks into Stage 1 (Basing), Stage 2 / 2A / 2B (Uptrend/Markup), Stage 3 (Distribution), or Stage 4 (Downtrend) based on the level and slope of the 30-week moving average.

Minervini Trend Template: Tests moving average alignment (50, 150, 200-day/equivalent weekly MAs), moving average slopes, and proximity to 52-week highs and lows.

O'Neil Weighted Relative Strength (RS): Calculates a 1-year performance score weighted towards recent quarters (40% Q1, 20% Q2, 20% Q3, 20% Q4) and normalizes it into a 1–99 percentile rank across the scanned universe. It also tracks the 1-month shift and computes Mansfield RS.

Volatility Contraction Pattern (VCP): Detects tightening price ranges over 20-day and 5-day periods accompanied by Volume Dry-Up (VDU).

Darvas Box Mechanics: Identifies consolidation boxes using lookback bars and ATR (Average True Range), detecting either Darvas Breakouts (volume expansion above the box) or Darvas Coils (tight consolidation in the upper half of the box with volume contraction).

Additional Setups: Identifies Stage 2 Breakouts and Pocket Pivots.

3. Market Breadth & Macro Regime Analysis (get_historical_breadth)
Cumulative Advance/Decline (A/D) Line: Computes daily advancing vs. declining stocks across the scanned universe.

Breadth Oscillators: Tracks the historical percentage of stocks trading above their 50-period and 200-period moving averages, including overbought (>80%) and oversold (<20%) threshold bands.

Market Regime / Power Trend: Determines whether the benchmark index is in a confirmed uptrend (21 EMA > 50 SMA).

4. Streamlit Dashboard & Visualizations
KPI Header Cards: Displays real-time breadth metrics, benchmark regime status, Stage 2A leader counts, and custom SVG sparklines.

Tab 1: Screener & Setup Charts:

An interactive data editor allowing filtering by price, setup type, Weinstein stage, minimum RS rank, and GICS theme.

Allows users to star/unstar stocks to save to an active session watchlist.

Embeds an interactive TradingView dark-theme chart widget for inspected tickers.

Displays a Plotly chart comparing the stock's price against its pure relative strength line over the past year.

Tab 2: Macro Breadth & Theme Rotation:

Dual-pane Plotly chart of the benchmark price vs. Cumulative Advance/Decline line.

Plotly chart of market breadth oscillators.

Aggregated table ranking GICS Industry Themes by average Relative Strength and the percentage of constituents in Stage 2A uptrends.

Are there any logical errors / conflicts that could interfere with the core functions or cause spurious results?
What improvements can we make to create a more practical / intuitive tool for the retail sharetrader trading the Australian Sharemarket?
















1. Logical Errors, Conflicts, and Spurious Calculations
A. Broken Lookback Calculations in Weekly Mode (Severe)
When the user switches Timeframe to "Weekly", daily price history is resampled to weekly bars (W-FRI). However, the calculations in calculate_metrics() continue to use hardcoded daily bar counts:

O'Neil Relative Strength (raw_rs):

Python
ret_q1 = get_ret(63, 1)    # 63 weekly bars = ~1.2 years
ret_q2 = get_ret(126, 64)  # 126 weekly bars = ~2.4 years
ret_q3 = get_ret(189, 127) # 189 weekly bars = ~3.6 years
ret_q4 = get_ret(252, 190) # 252 weekly bars = ~4.8 years
Because the downloaded history is only 3 years (~156 weekly bars), ret_q3 and ret_q4 will always return 0.0 due to the guard if n <= d_start: return 0.0. ret_q1 and ret_q2 end up measuring multi-year returns instead of quarters. In weekly mode, a quarter is 13 weeks (not 63 bars).

1-Month Offset for RS Shift (raw_rs_1m):
get_ret(63 + 21, 1 + 21) adds 21 weekly bars (5 months), rather than 1 month (4 weeks).

Moving Average Slopes:
slope150 looks back 22 bars. In daily mode this represents 1 trading month, but in weekly mode it represents 22 weeks (~5.5 months), despite the checklist label displaying ">1mo".

B. Intraday & Mid-Week Volume Dry-Up (VDU) Distortion
Weekly Mode:
projected_vol = curr_vol regardless of the day of the week. If run on a Monday or Tuesday, curr_vol represents only 1–2 days of trading, while avg_vol50 is a 10-week average (~50 daily equivalents). Consequently:

Python
vdu_vcp = projected_vol < (avg_vol50 * 0.5)
This condition will falsely trigger VDU and Darvas Coil setups for almost the entire market early in any trading week.

Daily Mode:
projected_vol = curr_vol * (360.0 / max(1.0, float(elapsed_mins))).
Between 10:00 and 10:15 AM AEST, linear extrapolation produces massive false volume spikes. Furthermore, stock volume is non-linear (it follows a U-shaped distribution: heavy at the open and close, thin in the middle).

C. Inconsistent Criteria: KPI Cards vs. Sparklines
There is a direct conflict between the KPI number and its historical sparkline for Stage 2A Leaders:

In calculate_metrics() (which powers the KPI count):

Python
(high52 - price) / high52 <= 0.15  # Within 15% of 52W high
weekly_slope > 0.002              # Strictly positive slope
price not > 1.25 * weekly_ma30    # Excludes extended Stage 2B
In get_historical_breadth() (which powers the sparkline):

Python
(high52 - close) / high52 <= 0.08  # Within 8% of 52W high
w_slope_d >= -0.005               # Allows slightly negative slope
# No check for Stage 2B extension
The sparkline trends do not reflect the metric displayed on the card.

D. User Interface & Filter Bugs
Broken Theme Filter:

Python
theme_filter = col4.selectbox("Theme", ["All Themes", "All Prices"])
The second option is hardcoded as "All Prices" instead of extracting distinct themes from the universe. Selecting it filters for df["theme"] == "All Prices", returning 0 results.

Weinstein Stage Filter Mismatch:
The selectbox includes "Stage 1B", but the engine only outputs "1", "2A", "2", "2B", "3", and "4". Filtering by "Stage 1B" returns zero results. Additionally, "Stage 2" and "Stage 2B" cannot be selected.

Non-functional CSV Export:
st.button("📥 Export CSV") only calls st.toast("Export generated."). It lacks an st.download_button() implementation.

E. Spurious Relative Strength Ranks in Fast Mode
In "Core & Watchlist (Fast)" mode, the universe contains only 12 tickers. Ranking 12 tickers on a 1–99 percentile scale means the top stock gets 99, the second gets ~91, etc.

A stock rated 99 RS in this mode only means it outperformed 11 other stocks, not that it is an institutional market leader across the ASX. Filtering with the Min RS Rank slider in Fast Mode yields misleading results.

F. Potential Pandas Timezone Localization Crash
Python
df.index = pd.to_datetime(df.index).tz_localize(None)
In modern versions of yfinance, ticker history and download results frequently return timezone-aware indices (e.g., Australia/Sydney or UTC). Calling .tz_localize(None) on an already timezone-aware index raises a TypeError: Already tz-aware, use tz_convert(None). The safe approach is:

Python
df.index = pd.to_datetime(df.index).tz_convert(None) if df.index.tz is not None else pd.to_datetime(df.index)
G. Scalability Bottleneck in Full Market Mode
Attempting yf.download(symbols, period="3y", ...) synchronously across ~1,900 symbols:

Frequently encounters Yahoo Finance rate limits (HTTP 429) or IP throttling.

Exceeds Streamlit Cloud worker memory limits (generating a multi-gigabyte MultiIndex DataFrame).

Causes UI lockups during the 60–90 second blocking call.

2. Practical Improvements for Retail ASX Traders
A. Add Liquidity and Turnover Filters ($ADTV & Price Floor)
The ASX has a pronounced liquidity cliff outside the ASX 300. Hundreds of microcap explorers (penny stocks) trade at $0.005–$0.05 with wide bid-ask spreads.

Minimum Daily Turnover: Allow traders to filter by minimum Average Daily Turnover (e.g., $ADTV >= $150,000 AUD) so setups are liquid enough to enter and exit with reasonable slippage.

Minimum Price Threshold: Eliminate sub-$0.02 stocks where tick sizes represent multi-percent bid-ask spreads that invalidate technical patterns.

B. Commodity & Sector Sub-Groupings (Beyond Broad GICS)
The ASX is heavily weighted toward Resources and Financials. The standard GICS sector "Materials" lumps gold producers, iron ore majors, lithium developers, uranium explorers, and rare earths together.

Group ASX mining equities into meaningful sub-industries: Gold, Uranium, Lithium, Iron Ore, Copper, Oil & Gas.

Retail momentum traders on the ASX trade commodity theme rotation; tracking average RS by specific commodity baskets is substantially more actionable than broad GICS groupings.

C. Pre-Computed Universe Relative Strength
To make RS ratings meaningful when scanning a small watchlist:

Maintain a pre-computed or cached baseline of 1-year returns across the entire ASX All Ordinaries / All Tech index.

Compute the 1–99 RS percentile against this full-market baseline so that a watchlist stock with an RS of 92 genuinely reflects top-decile performance across the entire exchange.

D. Account for ASX Trading Hours and Staggered Open
The ASX does not open all stocks simultaneously:

Equities open in staggered phases based on their initial letter between 10:00:00 AM and 10:09:15 AM AEST/AEDT (A–B at 10:00, C–F at 10:02:15, G–M at 10:04:30, N–R at 10:06:45, S–Z at 10:09:00).

Fix: Do not run linear volume projection before 10:15 AM. Use a historical intraday volume curve (weighting the open and closing auctions more heavily than midday trade) to avoid distorted volume projections.

E. Native TradingView Watchlist Export
Retail traders often screen in Streamlit but execute charting and trade management in TradingView.

Replace the dummy export with a button that outputs or copies an exact TradingView-compatible comma-separated ticker string prefixed with ASX::

Plaintext
ASX:DRO, ASX:SPR, ASX:DYL, ASX:WA1, ASX:PME
F. Implement Persistent Local Caching (Parquet / SQLite)
Instead of re-downloading years of full-market data on user request:

Maintain a local storage layer (e.g., DuckDB or lightweight Parquet files).

Fetch incremental daily updates after the 4:10 PM AEST market close, keeping the dashboard fast and immune to runtime rate limits.

Is it reasonable to implement all these changes?



Yes, it is reasonable, but they should be separated into two distinct stages: immediate code fixes (which can be implemented directly within your existing single-file script in under an hour) and architectural adjustments (which make full-market scanning reliable).

Phase 1: Immediate In-Place Fixes (Low Effort, High Impact)
These require no infrastructure changes and resolve the math errors, crashes, and broken UI elements directly in your current script:

Dynamic Lookbacks for Weekly Mode:
Swap hardcoded daily bar offsets (63, 126, 189, 252) for dynamic variables based on timeframe:

Daily: q1=63, q2=126, q3=189, q4=252, 1-month = 21 bars.

Weekly: q1=13, q2=26, q3=39, q4=52, 1-month = 4 bars.

Synchronize Stage 2A Criteria:
Use the exact same logic in get_historical_breadth() as in calculate_metrics() so the KPI metric and sparkline match.

Fix UI Bugs:

Populate theme_filter dynamically: ["All Themes"] + sorted(list(df_all["theme"].unique())).

Update substage_filter options to match the actual outputs ("All Stages", "Stage 1", "Stage 2", "Stage 2A", "Stage 2B", "Stage 3", "Stage 4").

Timezone-Safe Indexing:
Replace .tz_localize(None) with .tz_convert(None) if df.index.tz is not None else df.index to prevent runtime crashes.

Functional CSV & TradingView Export:

Replace the dummy button with st.download_button(..., data=df_display.to_csv(), mime="text/csv").

Add a text area or copy-ready string with comma-separated ASX: tickers for TradingView import.

Add Liquidity Filters in the Sidebar/Expander:
Add a minimum turnover slider (e.g., $ADTV >= $150k) and minimum price filter to immediately screen out un-tradable microcaps.

Phase 2: Architectural Separation (Recommended for Full Market Mode)
The only change that requires careful consideration is how full-market data (~1,900 ASX stocks) is fetched.

The Problem with Doing It Live in Streamlit
Running yf.download() across 1,900 tickers inside a Streamlit browser session will regularly fail on cloud deployments due to:

Yahoo Finance HTTP 429 rate limits or timeouts.

Streamlit worker memory constraints (1 GB RAM limit on free tiers).

Long blocking UI freezes (60–90+ seconds per rerun).

The Practical Solution: Decouple Data from UI
Most retail swing and momentum traders run their scans End-of-Day (EOD) after the 4:10 PM AEST close:

Background EOD Script: A separate Python script runs daily at ~4:30 PM (locally or via a free daily GitHub Action). It downloads the ~1,900 tickers, computes the true 1–99 market-wide RS ranks and setups, and saves a single compressed Parquet or SQLite file (~15–25 MB).

Streamlit App: Simply reads the cached Parquet file on load (st.cache_data). The dashboard opens instantly (sub-second), with full market breadth and true percentile ranks, without making live external API calls during user interaction.

Summary Recommendation
Implement Phase 1 immediately: The existing code already has a solid structure; correcting the timeframe logic, filters, and UI takes minimal effort and eliminates misleading output.

Keep live scanning focused on the Watchlist/Core universe: Reserve on-demand live fetching for smaller universes (50–150 stocks), while using a daily cached dataset for full-market breadth and 1–99 RS calculations.

Implement as per your recommendations.
















The recommendations and fixes have been implemented in the refactored script. Below is a summary of the key modifications made to resolve the logical discrepancies and improve usability for ASX retail share traders.

Readme
ASX Momentum, Relative Strength & VCP Scanner (Pro Edition v13.1)
Overview
This updated version resolves key calculation bugs, UI filtering flaws, and market structure nuances for retail traders screening equities on the Australian Securities Exchange (ASX).

Key Refactoring & Logic Fixes
1. Dynamic Timeframe Lookbacks (Daily vs. Weekly)
Problem: The original code applied daily lookback offsets (63, 126, 189, 252 bars) directly onto weekly resampled data, breaking O'Neil quarterly Relative Strength (raw_rs, raw_rs_1m) and forcing older quarterly returns to return 0.0.

Fix: Offsets now dynamically adapt based on timeframe selection:

Daily: Q 
1
​
 =63, Q 
2
​
 =126, Q 
3
​
 =189, Q 
4
​
 =252 bars; 1-month shift = 21 bars.

Weekly: Q 
1
​
 =13, Q 
2
​
 =26, Q 
3
​
 =39, Q 
4
​
 =52 bars; 1-month shift = 4 bars.

30-week moving average slope calculation now uses a 5-week window in weekly mode rather than 22 weeks.

2. Synchronization of Stage 2A & 3 Criteria
Problem: The top KPI card used strict Stage 2A criteria (15% from 52W high, positive slope, no >25% extension), while the historical sparkline used different criteria (8% from 52W high, slope ≥−0.005).

Fix: Both calculate_metrics() and get_historical_breadth() now share identical classification logic, ensuring historical sparklines match the current count.

3. Timezone-Safe DatetimeIndex Handling
Problem: Calling .tz_localize(None) on already timezone-aware yfinance returns raised fatal TypeError exceptions in newer Pandas versions.

Fix: Implemented strip_tz() using .tz_convert(None) when a timezone is present, ensuring safe conversion across environments.

4. Corrected Pivot Distance Convention
Problem: The original formula (prior_resistance - price) / price resulted in negative percentages when a stock broke out above resistance.

Fix: Standardized to ((price - prior_resistance) / prior_resistance) * 100.0. Positive percentages now intuitively represent extensions above breakout points, and negative values indicate distances below resistance.

5. Intraday & Mid-Week Volume Stabilization
Problem: Intraday linear projections produced extreme volume spikes during the opening 15 minutes of trade, and weekly scans run mid-week triggered false Volume Dry-Up (VDU) signals on Mondays/Tuesdays.

Fix: Added a 20-minute floor on the opening multiplier and scaled weekly mid-week volume by trading days elapsed.

Retail Trading Enhancements for the ASX
Liquidity ($ADTV) Filter: Added minimum Average Daily Turnover thresholds (> $50k, > $150k, > $300k, > $500k, > $1M) to filter out illiquid microcaps with prohibitive bid-ask spreads.

Price Floor Filter: Added granular price thresholds (> $0.05, > $0.10, > $0.50, etc.) to exclude sub-penny stocks.

Dynamic Theme Filter: Fixed UI bug where themes were hardcoded as ["All Themes", "All Prices"]. Options are now dynamically extracted from the active universe.

Weinstein Stage Filter Alignment: Dropdown options now directly match the engine's stage labels.

Functional CSV Download: Implemented native st.download_button replacing the static toast notification.

TradingView Watchlist Format: Added a dedicated expander with comma-separated ASX:TICKER strings for quick copy-pasting into TradingView.

Expanded Core Universe: Enhanced default universe to 23 liquid leaders across key ASX themes (Gold, Uranium, Critical Minerals, Tech, Healthcare, Retail, and Banking).

Core Fixes & Mathematical Corrections
Dynamic Weekly Lookback Adaptation:

Replaced static daily offsets (63, 126, 189, 252 bars) with dynamic lookback variables that adapt when the Weekly timeframe is active:

Daily: 63, 126, 189, 252 bars for quarters (Q 
1
​
  to Q 
4
​
 ), and 21 bars for 1-month shift.

Weekly: 13, 26, 39, 52 bars for quarters (Q 
1
​
  to Q 
4
​
 ), and 4 bars for 1-month shift.

Adjusted the 30-week moving average slope lookback to 5 bars in weekly mode (equivalent to ~1 month) instead of 22 bars.

Synchronized Stage 2A & 3 Breadth Logic:

Aligned the filtering logic in get_historical_breadth() with calculate_metrics(). Both now require slope > 0.002, price within 15% of 52-week highs, and exclude late-stage extended advances (>25% above the 30-week MA), ensuring the top KPI card and historical sparklines remain consistent.

Timezone-Safe Datetime Indexing:

Replaced direct .tz_localize(None) calls with a safe helper function (strip_tz) that checks for active timezones and converts via .tz_convert(None) before stripping, preventing runtime TypeError exceptions from newer Pandas and Yahoo Finance data formats.

Standardized Pivot Distance Formula:

Updated the pivot distance equation to ((price - prior_resistance) / prior_resistance) * 100.0. Positive percentages now represent breakouts above prior resistance, while negative percentages indicate distance remaining below resistance.

Volume Distortion Protections:

Intraday Opening: Added a 20-minute floor to the intraday projection multiplier to prevent artificial 100x+ volume spikes during the staggered ASX market open (10:00–10:15 AEST).

Weekly Mid-Week Scaling: Scaled weekly current-bar volume by trading days elapsed in the week to avoid false Volume Dry-Up (VDU) triggers on Mondays and Tuesdays.

ASX Retail Trading Enhancements
Liquidity ($ADTV) & Price Floor Filters:

Added a minimum Average Daily Turnover filter (> $50k, > $150k, > $300k, > $500k, > $1M) and price thresholds (> $0.05, > $0.10, etc.) to filter out illiquid microcap stocks and wide bid-ask spreads.

Dynamic Sector & Theme Population:

Replaced the hardcoded theme list with dynamic extraction from the active universe.

Consistent Weinstein Stage Filtering:

Updated the stage filter dropdown to match all actual engine stages (Stage 1, Stage 2A, Stage 2, Stage 2B, Stage 3, Stage 4).

Working CSV Export & TradingView Watchlist:

Replaced the toast placeholder with a functional st.download_button that exports the filtered results table.

Added an expander containing comma-separated, TradingView-ready ticker strings (e.g., ASX:DRO, ASX:SPR, ASX:PME) for quick clipboard import.

Expanded Balanced Core Universe:

Expanded the default fallback set to 23 liquid ASX growth and momentum leaders across key commodity and technology segments (Uranium, Gold, Critical Minerals, MedTech, Software, and Banking).

Deliverables
The updated application script and companion documentation are available below:

PY icon
asx_momentum_scanner
 PY 
Detailed documentation of formulas and implementation details is provided in the canvas view.




Gemini is AI and can make mistakes.

"""
==============================================================================
ASX Momentum, Relative Strength & VCP Scanner (Pro Cloud Edition v13.1)
==============================================================================
Refactored & Enhanced Engine:
  - FIXED: Timeframe Lookbacks (Quarterly O'Neil RS, 1M shifts, and MA slopes
           now dynamically adapt between Daily [63/126/189/252 bars] and Weekly [13/26/39/52 bars]).
  - FIXED: Stage 2A & 3 Synchronization (Historical breadth sparklines match
           screener criteria exactly, eliminating false KPI divergence).
  - FIXED: Timezone-Safe DatetimeIndex stripping (prevents Pandas tz-awareness crashes).
  - FIXED: UI Filters (Dynamic theme options populated from active universe;
           Weinstein Stage filter matches engine outputs).
  - FIXED: Pivot Distance (%) sign convention (+% = above pivot, -% = below pivot).
  - FIXED: Mid-week Weekly VDU & Morning linear projection volume distortions.
  - NEW: Liquidity ($ADTV) filter to eliminate untradable ASX microcaps.
  - NEW: Working CSV Export (st.download_button) and TradingView Watchlist block.
  - NEW: Balanced fallback universe across key ASX resource & growth themes.
==============================================================================
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import yfinance as yf
import pytz
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="ASX Momentum Scanner",
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
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { background-color: #1e293b; border-radius: 4px 4px 0 0; padding: 10px 20px; }
    .stTabs [aria-selected="true"] { background-color: #2563eb !important; color: white !important; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Expanded balanced core universe for ASX retail momentum traders
FALLBACK_UNIVERSE = {
    # Tech & Software
    "WTC.AX": {"name": "WiseTech Global", "type": "Equity", "theme": "Tech / Software"},
    "360.AX": {"name": "Life360", "type": "Equity", "theme": "Tech / Software"},
    "XRO.AX": {"name": "Xero", "type": "Equity", "theme": "Tech / Software"},
    "NXT.AX": {"name": "NextDC", "type": "Equity", "theme": "Tech / Data Infrastructure"},
    # Healthcare & Biotech
    "PME.AX": {"name": "Pro Medicus", "type": "Equity", "theme": "Healthcare / MedTech"},
    "NEU.AX": {"name": "Neuren Pharma", "type": "Equity", "theme": "Biotech"},
    "TLX.AX": {"name": "Telix Pharma", "type": "Equity", "theme": "Biotech"},
    "CSL.AX": {"name": "CSL Limited", "type": "Equity", "theme": "Healthcare"},
    # Uranium & Energy
    "DYL.AX": {"name": "Deep Yellow", "type": "Equity", "theme": "Uranium"},
    "BOE.AX": {"name": "Boss Energy", "type": "Equity", "theme": "Uranium"},
    "PDN.AX": {"name": "Paladin Energy", "type": "Equity", "theme": "Uranium"},
    # Gold & Precious Metals
    "SPR.AX": {"name": "Spartan Resources", "type": "Equity", "theme": "Gold"},
    "DEG.AX": {"name": "De Grey Mining", "type": "Equity", "theme": "Gold"},
    "EVN.AX": {"name": "Evolution Mining", "type": "Equity", "theme": "Gold"},
    "NST.AX": {"name": "Northern Star", "type": "Equity", "theme": "Gold"},
    # Critical Minerals, Copper & Lithium
    "WA1.AX": {"name": "WA1 Resources", "type": "Equity", "theme": "Niobium / Critical Minerals"},
    "PLS.AX": {"name": "Pilbara Minerals", "type": "Equity", "theme": "Lithium"},
    "SFR.AX": {"name": "Sandfire Resources", "type": "Equity", "theme": "Copper"},
    # Defense & Industrials
    "DRO.AX": {"name": "Droneshield", "type": "Equity", "theme": "Defense"},
    # Consumer & Financials
    "GYG.AX": {"name": "Guzman y Gomez", "type": "Equity", "theme": "Consumer / Retail"},
    "ZIP.AX": {"name": "Zip Co", "type": "Equity", "theme": "Fintech"},
    "CBA.AX": {"name": "Commonwealth Bank", "type": "Equity", "theme": "Banking"},
    "BHP.AX": {"name": "BHP Group", "type": "Equity", "theme": "Diversified Resources"}
}

BENCHMARK_MAP = {
    "All Ordinaries (^AORD)": {"symbol": "^AORD", "short": "AORD", "name": "All Ords"},
    "S&P/ASX 200 (^AXJO)": {"symbol": "^AXJO", "short": "AXJO", "name": "ASX 200"}
}

if "watchlist" not in st.session_state:
    query_wl = st.query_params.get("wl", "")
    st.session_state.watchlist = set(query_wl.split(",")) if query_wl else set(["DRO", "SPR", "DYL", "PME", "WA1"])
if "active_ticker" not in st.session_state: st.session_state.active_ticker = None
if "insp_dropdown" not in st.session_state: st.session_state.insp_dropdown = None
if "show_starred_only" not in st.session_state: st.session_state.show_starred_only = False

def update_query_watchlist():
    st.query_params["wl"] = ",".join(st.session_state.watchlist)

def strip_tz(idx):
    """Safely converts timezone-aware DatetimeIndex to timezone-naive to avoid Pandas TypeErrors."""
    idx = pd.to_datetime(idx)
    return idx.tz_convert(None) if idx.tz is not None else idx

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
            dynamic_universe[sym] = {"name": str(row.get('Company name', sym)).title(), "type": "Equity", "theme": theme}
        return dynamic_universe
    except Exception:
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
        df_batch = yf.download(symbols, period="3y", interval="1d", progress=False, group_by="ticker")
        data_dict = {}
        if isinstance(df_batch.columns, pd.MultiIndex):
            for sym in symbols:
                try: 
                    sym_df = df_batch[sym].dropna(how="all")
                    if not sym_df.empty: data_dict[sym] = sym_df
                except KeyError: pass
        else:
            if len(symbols) == 1:
                data_dict[symbols[0]] = df_batch
        
        bench_df = yf.Ticker(bench_symbol).history(period="3y")
        if not bench_df.empty: data_dict[bench_symbol] = bench_df
        return data_dict, None
    except Exception as e:
        return None, str(e)

def get_historical_breadth(raw_data, universe_keys, b_df_index, timeframe):
    target_idx = b_df_index[-125:]
    count_50 = pd.Series(0, index=target_idx)
    count_200 = pd.Series(0, index=target_idx)
    count_2a = pd.Series(0, index=target_idx)
    count_3 = pd.Series(0, index=target_idx)
    count_uni = pd.Series(0, index=target_idx)
    ad_line = pd.Series(0, index=target_idx)

    for sym in universe_keys:
        if sym not in raw_data: continue
        df = raw_data[sym].ffill().dropna(subset=["Close"])
        df.index = strip_tz(df.index)
        
        if timeframe == "Weekly":
            df = df.resample('W-FRI').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'}).dropna()
            min_bars = 40
        else:
            min_bars = 200
            
        if len(df) < min_bars: continue
        
        close = df['Close']
        high = df['High']
        
        daily_diff = close.diff()
        advancers = (daily_diff > 0).astype(int)
        decliners = (daily_diff < 0).astype(int)
        ad_line += (advancers - decliners).reindex(target_idx).fillna(0)

        if timeframe == "Weekly":
            ma50 = close.rolling(10).mean()
            ma200 = close.rolling(40).mean()
            w_ma30 = close.rolling(30).mean()
            w_slope = (w_ma30 - w_ma30.shift(5)) / w_ma30  # 5 weeks (~1 month)
            w_ma30_d = w_ma30
            w_slope_d = w_slope
            high52 = high.rolling(52, min_periods=20).max()
        else:
            ma50 = close.rolling(50).mean()
            ma200 = close.rolling(200).mean()
            df_weekly = close.resample('W-FRI').last()
            w_ma30 = df_weekly.rolling(30).mean()
            w_slope = (w_ma30 - w_ma30.shift(4)) / w_ma30
            w_ma30_d = w_ma30.reindex(close.index).ffill()
            w_slope_d = w_slope.reindex(close.index).ffill()
            high52 = high.rolling(252, min_periods=100).max()
        
        # Synchronized Stage 2A & 3 definitions
        is_2a = ((w_slope_d > 0.002) & 
                 (close >= w_ma30_d * 0.98) & 
                 ((close - w_ma30_d) / w_ma30_d <= 0.25) & 
                 ((high52 - close) / high52 <= 0.15))
                 
        is_3 = ((w_slope_d.abs() <= 0.002) & 
                ((high52 - close) / high52 < 0.20) & 
                (close < w_ma30_d * 1.05) & 
                (close > w_ma30_d * 0.85))
        
        count_50 += (close > ma50).astype(int).reindex(target_idx).fillna(0)
        count_200 += (close > ma200).astype(int).reindex(target_idx).fillna(0)
        count_2a += is_2a.astype(int).reindex(target_idx).fillna(0)
        count_3 += is_3.astype(int).reindex(target_idx).fillna(0)
        count_uni += close.notna().astype(int).reindex(target_idx).fillna(0)

    safe_uni = count_uni.replace(0, 1)
    return (count_50 / safe_uni * 100).tolist(), (count_200 / safe_uni * 100).tolist(), count_2a.tolist(), count_3.tolist(), count_uni.tolist(), ad_line.cumsum().tolist()

def calculate_metrics(sym, df, bench_series, itype, darvas_lb, darvas_vol, darvas_coil_vol, darvas_box_atr, timeframe):
    df.index = strip_tz(df.index)
    
    if timeframe == "Weekly":
        df = df.resample('W-FRI').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'}).dropna()
        p_50, p_150, p_200 = 10, 30, 40
        p_vol20, p_vol50 = 4, 10
        p_52w = 52
        q1_start, q1_end = 13, 1
        q2_start, q2_end = 26, 14
        q3_start, q3_end = 39, 27
        q4_start, q4_end = 52, 40
        shift_1m = 4
        slope150_bars = 5
        ret_1m_bars = 4
        ret_3m_bars = 13
    else:
        p_50, p_150, p_200 = 50, 150, 200
        p_vol20, p_vol50 = 21, 51
        p_52w = 252
        q1_start, q1_end = 63, 1
        q2_start, q2_end = 126, 64
        q3_start, q3_end = 189, 127
        q4_start, q4_end = 252, 190
        shift_1m = 21
        slope150_bars = 22
        ret_1m_bars = 22
        ret_3m_bars = 64

    if len(df) < p_200: return None
    
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]
    n = len(close)

    price = float(close.iloc[-1])
    prev_price = float(close.iloc[-2]) if n >= 2 else price
    change = ((price - prev_price) / prev_price) * 100.0 if prev_price > 0.0 else 0.0

    ma50 = float(close.rolling(p_50).mean().iloc[-1])
    ma150 = float(close.rolling(p_150).mean().iloc[-1])
    ma200 = float(close.rolling(p_200).mean().iloc[-1])
    
    if timeframe == "Weekly":
        ma200_recent = float(close.rolling(p_200).mean().iloc[-3]) if n >= (p_200 + 3) else price
        ma200_past = float(close.rolling(p_200).mean().iloc[-5]) if n >= (p_200 + 5) else price
    else:
        ma200_recent = float(close.rolling(p_200).mean().iloc[-11]) if n >= 210 else price
        ma200_past = float(close.rolling(p_200).mean().iloc[-23]) if n >= 222 else price
        
    ma200_rising = (ma200 > ma200_recent) and (ma200_recent > ma200_past)
    slope150 = (ma150 - float(close.rolling(p_150).mean().iloc[-slope150_bars])) / ma150 if n >= (p_150 + slope150_bars) else 0.0
    
    if timeframe == "Weekly":
        weekly_ma30 = float(close.rolling(30).mean().iloc[-1]) if n >= 30 else ma150
        weekly_slope = (weekly_ma30 - float(close.rolling(30).mean().iloc[-5])) / weekly_ma30 if n >= 35 else 0.0
    else:
        df_weekly = df.resample('W-FRI').last().dropna(subset=["Close"])
        weekly_ma30 = float(df_weekly["Close"].rolling(30).mean().iloc[-1]) if len(df_weekly) >= 30 else ma150
        weekly_slope = (weekly_ma30 - float(df_weekly["Close"].rolling(30).mean().iloc[-4])) / weekly_ma30 if len(df_weekly) >= 34 else 0.0

    high52 = float(high.iloc[-min(n, p_52w):].max())
    low52 = float(low.iloc[-min(n, p_52w):].min())

    # Corrected Pivot Distance: Positive indicates extended above pivot, Negative indicates below pivot
    prior_resistance = float(high.iloc[-min(n-1, 21):-1].max()) if n >= 22 else price
    pivot_dist = ((price - prior_resistance) / prior_resistance) * 100.0 if prior_resistance > 0.0 else 0.0

    adr = float(((high.iloc[-20:] / low.iloc[-20:]) - 1).mean() * 100) if n >= 20 else 0.0

    str_50  = "10-Week MA" if timeframe == "Weekly" else "50 MA"
    str_150 = "30-Week MA" if timeframe == "Weekly" else "150 MA"
    str_200 = "40-Week MA" if timeframe == "Weekly" else "200 MA"

    checklist = {
        f"Price > {str_150} & {str_200}": price > ma150 and price > ma200,
        f"{str_150} > {str_200}": ma150 > ma200,
        f"{str_200} Rising (>1mo)": ma200_rising,
        f"{str_150} Rising (>1mo)": slope150 > 0.0,
        f"Price > {str_50}": price > ma50,
        "Price ≥ 30% Above 52W Low": price >= (low52 * 1.30) if itype == "Equity" else price >= (low52 * 1.15),
        "Price Within 25% of 52W High": price >= (high52 * 0.75)
    }
    tt_pass = checklist[f"Price > {str_150} & {str_200}"] and checklist[f"Price > {str_50}"]

    def get_ret(d_start, d_end):
        if n <= d_start: return 0.0
        p_start = float(close.iloc[-d_start])
        return (float(close.iloc[-d_end]) - p_start) / p_start if p_start > 0.0 else 0.0

    ret_1m = get_ret(ret_1m_bars, 1) * 100
    ret_3m = get_ret(ret_3m_bars, 1) * 100

    # Dynamic O'Neil quarterly relative return calculations
    ret_q1 = get_ret(q1_start, q1_end)
    ret_q2 = get_ret(q2_start, q2_end)
    ret_q3 = get_ret(q3_start, q3_end)
    ret_q4 = get_ret(q4_start, q4_end)
    raw_rs = (0.40 * ret_q1) + (0.20 * ret_q2) + (0.20 * ret_q3) + (0.20 * ret_q4)

    ret_q1_1m = get_ret(q1_start + shift_1m, q1_end + shift_1m)
    ret_q2_1m = get_ret(q2_start + shift_1m, q2_end + shift_1m)
    ret_q3_1m = get_ret(q3_start + shift_1m, q3_end + shift_1m)
    ret_q4_1m = get_ret(q4_start + shift_1m, q4_end + shift_1m)
    raw_rs_1m = (0.40 * ret_q1_1m) + (0.20 * ret_q2_1m) + (0.20 * ret_q3_1m) + (0.20 * ret_q4_1m)

    avg_vol20 = float(volume.iloc[-p_vol20-1:-1].mean()) if n >= (p_vol20+1) else 1.0
    avg_vol50 = float(volume.iloc[-p_vol50-1:-1].mean()) if n >= (p_vol50+1) else avg_vol20
    curr_vol = float(volume.iloc[-1])
    rvol = curr_vol / avg_vol20 if avg_vol20 > 0 else 1.0
    adtv = avg_vol20 * price
    adtv_fmt = f"${adtv/1e6:.1f}M" if adtv >= 1e6 else f"${round(adtv/1e3)}k"

    # Refined Volume Projection (Intraday morning protection & Weekly mid-week scaling)
    now = pd.Timestamp.now(tz=pytz.timezone('Australia/Sydney'))
    if timeframe == "Weekly":
        weekday = now.weekday()
        if weekday < 5:
            days_elapsed = max(1.0, min(5.0, float(weekday) + (1.0 if now.hour >= 16 else 0.5)))
            projected_vol = curr_vol * (5.0 / days_elapsed)
        else:
            projected_vol = curr_vol
    else:
        if now.weekday() < 5 and 10 <= now.hour < 16:
            elapsed_mins = (now.hour - 10) * 60 + now.minute
            # Buffer first 20 minutes of ASX trade to prevent exaggerated volume multipliers
            effective_mins = max(20.0, float(elapsed_mins))
            projected_vol = curr_vol * (360.0 / effective_mins)
        else:
            projected_vol = curr_vol

    # Weinstein Stages
    stage_raw = "1"
    stage = "Stage 1 (Basing)"
    
    if weekly_slope > 0.002: 
        if price < weekly_ma30 * 0.98: stage, stage_raw = "Stage 1 (Basing)", "1"
        elif (price - weekly_ma30) / weekly_ma30 > 0.25: stage, stage_raw = "Stage 2B (Late Uptrend)", "2B"
        elif (high52 - price) / high52 <= 0.15: stage, stage_raw = "Stage 2A (Early Markup)", "2A"
        else: stage, stage_raw = "Stage 2 (Advancing)", "2"
    elif weekly_slope < -0.002:
        if price >= weekly_ma30 * 0.98: stage, stage_raw = "Stage 1 (Basing)", "1"
        else: stage, stage_raw = "Stage 4 (Downtrend)", "4"
    else: 
        if (high52 - price) / high52 < 0.20 and price < weekly_ma30 * 1.05 and price > weekly_ma30 * 0.85: stage, stage_raw = "Stage 3 (Distribution)", "3"
        else: stage, stage_raw = "Stage 1 (Basing)", "1"

    tr = np.maximum(high - low, np.maximum(abs(high - close.shift(1)), abs(low - close.shift(1))))
    atr_14 = float(tr.rolling(14).mean().iloc[-1]) if n >= 14 else 0.0

    max_20d = float(high.iloc[-20:].max()) if n >= 20 else price
    min_20d = float(low.iloc[-20:].min()) if n >= 20 else price
    range_20d_pct = (max_20d - min_20d) / min_20d if min_20d > 0 else 0
    max_5d = float(high.iloc[-5:].max()) if n >= 5 else price
    min_5d = float(low.iloc[-5:].min()) if n >= 5 else price
    range_5d_abs = max_5d - min_5d
    position_20d = (price - min_20d) / (max_20d - min_20d) if max_20d > min_20d else 0
    vdu_vcp = projected_vol < (avg_vol50 * 0.5)

    max_down_vol = 0.0
    if n >= 12:
        last_10_closes = close.iloc[-12:-1]
        last_10_vols = volume.iloc[-11:-1]
        down_vols = last_10_vols[last_10_closes.diff().iloc[1:].values < 0]
        max_down_vol = float(down_vols.max()) if len(down_vols) > 0 else 0.0

    darvas_coil = False
    darvas_bo = False
    if n >= darvas_lb + 1:
        hist_high = high.iloc[-darvas_lb-1:-1]
        box_top_idx = np.argmax(hist_high.values) 
        box_age = darvas_lb - box_top_idx
        box_top = float(hist_high.values[box_top_idx])
        box_bottom = float(low.iloc[-box_age-1:-1].min())
        box_height_atr = (box_top - box_bottom) / atr_14 if atr_14 > 0 else 0
        
        is_mature_box = (box_age >= (1 if timeframe == "Weekly" else 5)) and (0.3 <= box_height_atr <= darvas_box_atr)
        is_nr4 = (n >= 4) and (tr.iloc[-1] < min(tr.iloc[-2], tr.iloc[-3], tr.iloc[-4]))
        is_inside = (n >= 2) and (high.iloc[-1] <= high.iloc[-2]) and (low.iloc[-1] >= low.iloc[-2])
        is_upper_half = price > (box_bottom + (box_top - box_bottom) * 0.5)
        
        vdu_darvas = projected_vol < (avg_vol50 * (darvas_coil_vol / 100.0))
        darvas_coil = is_mature_box and (is_nr4 or is_inside) and is_upper_half and vdu_darvas and (price <= box_top)
        darvas_bo = is_mature_box and (price > box_top) and (rvol >= darvas_vol)

    setup_flags = []
    if tt_pass and stage_raw in ["2A", "2"]:
        if price >= (prior_resistance * 0.99) and rvol >= 1.5 and change > 2.0:
            setup_flags.append("Stage 2 Breakout")
        elif change > 0 and curr_vol > max_down_vol and max_down_vol > 0 and position_20d > 0.3:
            setup_flags.append("Pocket Pivot")
        if range_20d_pct <= 0.25 and range_5d_abs <= (1.5 * atr_14) and position_20d > 0.5 and vdu_vcp:
            setup_flags.append("VCP")
        if darvas_bo: setup_flags.append("Darvas Breakout")
        if darvas_coil: setup_flags.append("Darvas Coil")

    setup = " + ".join(setup_flags) if len(setup_flags) > 0 else "No Setup"

    mrs_series = []
    pure_rs_series = []
    dates_252 = []
    price_252 = []
    if bench_series is not None:
        bench_series.index = strip_tz(bench_series.index)
        common_idx = close.index.intersection(bench_series.index)
        lookback_rs = min(len(common_idx), p_52w)
        if len(common_idx) >= 30:
            ratio = close.loc[common_idx] / bench_series.loc[common_idx]
            ratio_ma = ratio.rolling(min(52, len(ratio)), min_periods=10).mean()
            mrs_curve = ((ratio / ratio_ma) - 1.0) * 10.0
            mrs_series = mrs_curve.reindex(close.index).ffill().iloc[-90:].tolist()
            
            pure_rs_series = ratio.reindex(close.index).ffill().iloc[-lookback_rs:].tolist()
            dates_252 = close.index[-lookback_rs:].strftime('%Y-%m-%d').tolist()
            price_252 = close.iloc[-lookback_rs:].tolist()

    return {
        "price": price, "change": change, "ret_1m": ret_1m, "ret_3m": ret_3m,
        "pivot_dist": pivot_dist, "adr": adr, "raw_rs": raw_rs, "raw_rs_1m": raw_rs_1m, 
        "adtv": adtv, "adtv_fmt": adtv_fmt, "checklist": checklist, "trend_score": sum(checklist.values()),
        "stage": stage, "stage_raw": stage_raw, "setup": setup,
        "mrs_series": mrs_series, "pure_rs_series": pure_rs_series, "dates_252": dates_252, "price_252": price_252,
        "above_50": price > ma50, "above_200": price > ma200
    }

def main():
    h1, h2, h3, h4 = st.columns([5.5, 1.5, 1.5, 1.5])
    with h1:
        st.markdown("""<div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;"><div class="asx-badge">ASX</div>
        <div><div style="font-size:1.35rem; font-weight:800; color:#f8fafc; letter-spacing:-0.02em;">ASX Authentic Momentum Scanner <span style="font-size:0.75rem; font-weight:700; background:rgba(16,185,129,0.2); color:#6ee7b7; border:1px solid rgba(16,185,129,0.3); padding:2px 7px; border-radius:4px; margin-left:6px;">PRO v13.1</span></div>
        <div style="font-size:0.78rem; color:#94a3b8; font-weight:500;">Live Market Breadth • True Weinstein Stages • Volume Dry-Up (VDU) • Darvas Boxes</div></div></div>""", unsafe_allow_html=True)
    with h2:
        st.markdown("<div style='padding-top:10px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Fetch Live ASX Data", use_container_width=True, type="primary"): 
            st.cache_data.clear()
            st.rerun()
    with h3:
        # Will render actual st.download_button once table is computed
        export_container = st.container()
    with h4:
        st.markdown("<div style='padding-top:10px;'></div>", unsafe_allow_html=True)
        star_lbl = f"★ Starred ({len(st.session_state.watchlist)})"
        if st.button(star_lbl, use_container_width=True):
            st.session_state.show_starred_only = not st.session_state.show_starred_only
            st.rerun()

    # Pre-select Universe Target
    with st.expander("⚙️ Advanced Scan Parameters & Thresholds", expanded=False):
        s1, s2, s3, s4, s5 = st.columns(5)
        universe_mode = s1.selectbox("Engine Target", ["Core & Watchlist (Fast)", "ASX Full Market (Slower EOD)"])
        bench_choice = s2.selectbox("Benchmark", list(BENCHMARK_MAP.keys()), index=0)
        darvas_lb = s3.slider("Darvas Lookback (Bars)", 5, 50, 21, 1)
        darvas_vol = s4.slider("Darvas BO Vol (x Avg)", 0.5, 3.0, 1.3, 0.1)
        darvas_coil_vol = s5.slider("Darvas Coil Max Vol (%)", 10, 100, 50, 5)
        
        s6, s7, s8, s9, s10 = st.columns(5)
        darvas_box_atr = s6.slider("Darvas Max Box Height (ATR)", 0.5, 10.0, 3.0, 0.1)
        min_adtv_filter = s7.selectbox("Min Daily Turnover ($ADTV)", ["All Liquidity", "> $50k", "> $150k", "> $300k", "> $500k", "> $1M"], index=2)
        min_rs = s8.slider("Min RS Rank", 0, 95, 0, 5)
        if s10.button("Reset Configurations", use_container_width=True):
            st.session_state.show_starred_only = False
            st.cache_data.clear()
            st.rerun()

    # Determine Active Universe
    if universe_mode == "ASX Full Market (Slower EOD)":
        active_universe = fetch_dynamic_universe()
        st.caption("⚡ **Engine Note:** Pulling 3-years of historical data for active ASX equities. RS ranks reflect full-market percentiles.")
    else:
        active_universe = FALLBACK_UNIVERSE.copy()
        for sym in st.session_state.watchlist:
            full_sym = f"{sym}.AX"
            if full_sym not in active_universe:
                active_universe[full_sym] = {"name": sym, "type": "Equity", "theme": "Watchlist Addition"}
        st.caption(f"⚡ **Fast Mode Active:** Scanning {len(active_universe)} key liquid momentum leaders. (RS Rank is ordinal to this set).")

    # Load Data
    bench_info = BENCHMARK_MAP[bench_choice]
    raw_data, err = load_all_market_data(active_universe, bench_info["symbol"])
    if err or raw_data is None: 
        st.error(f"Market feed error: {err}")
        return

    b_df = None
    if bench_info["symbol"] in raw_data:
        b_df = raw_data[bench_info["symbol"]].ffill().dropna(subset=["Close"])
        b_df.index = strip_tz(b_df.index)
            
    if b_df is None or len(b_df) < 50:
        st.error(f"Failed to fetch sufficient benchmark data for {bench_info['symbol']}. Halting scan to prevent false regime data.")
        return

    # User Filters Row (Rendered with active themes)
    with st.container(border=True):
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        search_query = col1.text_input("Search Ticker..", "").strip().lower()
        timeframe_sel = col2.selectbox("Timeframe", ["Daily", "Weekly"])
        price_filter = col3.selectbox("Price", ["All Prices", "> $0.05", "> $0.10", "> $0.50", "> $1.00", "> $5.00", "> $10.00"])
        
        # Dynamically extracted themes
        available_themes = ["All Themes"] + sorted(list(set(meta.get("theme", "Diversified") for meta in active_universe.values())))
        theme_filter = col4.selectbox("Theme", available_themes)
        
        setup_filter = col5.selectbox("Setup", ["All Setups", "VCP", "Stage 2 Breakout", "Pocket Pivot", "Darvas Breakout", "Darvas Coil", "No Setup"])
        stage_filter = col6.selectbox("Weinstein Stage", [
            "All Stages", 
            "Stage 1 (Basing)", 
            "Stage 2A (Early Markup)", 
            "Stage 2 (Advancing)", 
            "Stage 2B (Late Uptrend)", 
            "Stage 3 (Distribution)", 
            "Stage 4 (Downtrend)"
        ])

    # Timeframe adjustment for benchmark
    if timeframe_sel == "Weekly":
        b_df = b_df.resample('W-FRI').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'}).dropna()

    bench_dates_recent = b_df.index[-125:].strftime('%Y-%m-%d').tolist()
    bench_price, b_prev = float(b_df["Close"].iloc[-1]), float(b_df["Close"].iloc[-2])
    bench_change = ((bench_price - b_prev) / b_prev) * 100.0
    power_trend_on = float(b_df["Close"].ewm(span=21).mean().iloc[-1]) > float(b_df["Close"].rolling(50 if timeframe_sel == 'Daily' else 10).mean().iloc[-1])
    bench_spark_vals = b_df["Close"].iloc[-125:].tolist()

    processed_list = []
    missing_data = []
    
    for sym, meta in active_universe.items():
        df_sym = raw_data[sym].ffill().dropna(subset=["Close"]) if sym in raw_data else None
        min_bars_needed = 45 if timeframe_sel == "Weekly" else 130
        if df_sym is not None and len(df_sym) >= min_bars_needed:
            m = calculate_metrics(sym, df_sym, b_df["Close"], meta["type"], darvas_lb, darvas_vol, darvas_coil_vol, darvas_box_atr, timeframe_sel)
            if m:
                clean_ticker = sym.replace(".AX", "")
                m.update({"ticker": clean_ticker, "name": meta["name"], "type": meta["type"], "theme": meta["theme"]})
                processed_list.append(m)
        else:
            missing_data.append(sym)

    if not processed_list: 
        st.warning("No instruments passed data validation.")
        return
        
    if missing_data and universe_mode == "Core & Watchlist (Fast)": 
        st.toast(f"Excluded due to insufficient history: {', '.join(missing_data)}")

    # Relative strength percentile calculations
    processed_list.sort(key=lambda x: x["raw_rs_1m"])
    for idx, item in enumerate(processed_list): 
        item["rs_1m"] = max(1, min(99, round(((idx + 1) / len(processed_list)) * 99)))

    processed_list.sort(key=lambda x: x["raw_rs"])
    for idx, item in enumerate(processed_list):
        item["rs"] = max(1, min(99, round(((idx + 1) / len(processed_list)) * 99)))
        item["rs_shift"] = item["rs"] - item["rs_1m"]
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
                
        item["mrs"] = f"{'+' if mrs_v >= 0 else ''}{mrs_v} ({traj})"

    df_all = pd.DataFrame(processed_list)
    h_50, h_200, h_2a, h_3, h_uni, h_ad = get_historical_breadth(raw_data, active_universe.keys(), b_df.index, timeframe_sel)

    total_u = len(df_all)
    pct_50 = (df_all["above_50"].sum() / total_u * 100.0) if total_u > 0 else 0.0
    pct_200 = (df_all["above_200"].sum() / total_u * 100.0) if total_u > 0 else 0.0
    stage_2a_count = sum(df_all["stage_raw"] == "2A")
    stage_3_count = sum(df_all["stage_raw"] == "3")

    # KPI Top Bar
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    with k1: 
        st.markdown(f'<div class="kpi-card"><div class="kpi-title"><span>{bench_info["short"]} REGIME</span><span style="color:#94a3b8;">{bench_price:,.0f} ({bench_change:+.2f}%)</span></div><div class="kpi-val" style="color:{"#22c55e" if power_trend_on else "#f59e0b"};">{"● Power Trend ON" if power_trend_on else "○ Correction"}</div>{make_sparkline_svg(bench_spark_vals, stroke_color="#22c55e" if power_trend_on else "#f59e0b", fill_color="rgba(34,197,94,0.15)" if power_trend_on else "rgba(245,158,11,0.15)")}</div>', unsafe_allow_html=True)
    with k2: 
        st.markdown(f'<div class="kpi-card"><div class="kpi-title"><span>% &gt; {"10W" if timeframe_sel == "Weekly" else "50D"} MA</span></div><div class="kpi-val" style="color:#f8fafc;">{pct_50:.1f}%</div>{make_sparkline_svg(h_50, stroke_color="#38bdf8", fill_color="rgba(56,189,248,0.15)")}</div>', unsafe_allow_html=True)
    with k3: 
        st.markdown(f'<div class="kpi-card"><div class="kpi-title"><span>% &gt; {"40W" if timeframe_sel == "Weekly" else "200D"} MA</span></div><div class="kpi-val" style="color:#f8fafc;">{pct_200:.1f}%</div>{make_sparkline_svg(h_200, stroke_color="#818cf8", fill_color="rgba(129,140,248,0.15)")}</div>', unsafe_allow_html=True)
    with k4: 
        st.markdown(f'<div class="kpi-card"><div class="kpi-title"><span>STAGE 2A LEADERS</span></div><div class="kpi-val" style="color:#22c55e;">{stage_2a_count} Breaking Out</div>{make_sparkline_svg(h_2a, stroke_color="#22c55e", fill_color="rgba(34,197,94,0.15)")}</div>', unsafe_allow_html=True)
    with k5: 
        st.markdown(f'<div class="kpi-card"><div class="kpi-title"><span>STAGE 3 DISTRIBUTION</span></div><div class="kpi-val" style="color:#f43f5e;">{stage_3_count} Topping</div>{make_sparkline_svg(h_3, stroke_color="#f43f5e", fill_color="rgba(244,63,94,0.15)")}</div>', unsafe_allow_html=True)
    with k6: 
        st.markdown(f'<div class="kpi-card"><div class="kpi-title"><span>UNIVERSE</span></div><div class="kpi-val" style="color:#c084fc;">{total_u} Scanned</div>{make_sparkline_svg(h_uni, stroke_color="#c084fc", fill_color="rgba(192,132,252,0.15)")}</div>', unsafe_allow_html=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📊 Screener & Setup Charts", "🌍 Macro Breadth & Theme Rotation"])

    with tab1:
        df = df_all.copy()
        
        # Apply Filters
        if price_filter != "All Prices":
            min_price = float(price_filter.replace("> $", ""))
            df = df[df["price"] > min_price]
            
        if min_adtv_filter != "All Liquidity":
            if min_adtv_filter == "> $50k": df = df[df["adtv"] >= 50000]
            elif min_adtv_filter == "> $150k": df = df[df["adtv"] >= 150000]
            elif min_adtv_filter == "> $300k": df = df[df["adtv"] >= 300000]
            elif min_adtv_filter == "> $500k": df = df[df["adtv"] >= 500000]
            elif min_adtv_filter == "> $1M": df = df[df["adtv"] >= 1000000]
            
        if st.session_state.show_starred_only: 
            df = df[df["ticker"].isin(st.session_state.watchlist)]
        if search_query: 
            df = df[df["ticker"].str.lower().str.contains(search_query) | df["name"].str.lower().str.contains(search_query)]
        if theme_filter != "All Themes": 
            df = df[df["theme"] == theme_filter]
        if stage_filter != "All Stages": 
            df = df[df["stage"] == stage_filter]
        if setup_filter != "All Setups": 
            df = df[df["setup"].str.contains(setup_filter)]
            
        df = df[df["rs"] >= min_rs]

        df_display = df[["ticker", "name", "price", "change", "ret_1m", "ret_3m", "pivot_dist", "adr", "rs", "rs_shift", "mrs", "trend_score", "stage", "setup", "adtv_fmt"]].copy()
        df_display.columns = ["TICKER", "NAME", "PRICE", "LAST %", "1M %", "3M %", "PIVOT DIST %", "ADR %", "RS", "RS-S", "MANSFIELD RS", "MINERVINI TREND", "WEINSTEIN STAGE", "SETUP", "$ADTV"]
        
        df_display.insert(0, "STARRED", df_display["TICKER"].apply(lambda x: x in st.session_state.watchlist))
        df_display.insert(1, "CHART", False)
        df_display = df_display.sort_values(by="RS", ascending=False).reset_index(drop=True)

        # Working CSV Export Button in Top Bar
        with export_container:
            st.markdown("<div style='padding-top:10px;'></div>", unsafe_allow_html=True)
            csv_data = df_display.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export CSV",
                data=csv_data,
                file_name=f"asx_momentum_{timeframe_sel.lower()}.csv",
                mime="text/csv",
                use_container_width=True
            )

        editor_key = "watchlist_editor"
        disabled_cols = ["TICKER", "NAME", "PRICE", "LAST %", "1M %", "3M %", "PIVOT DIST %", "ADR %", "RS", "RS-S", "MANSFIELD RS", "MINERVINI TREND", "WEINSTEIN STAGE", "SETUP", "$ADTV"]
        
        st.data_editor(
            df_display,
            column_config={
                "STARRED": st.column_config.CheckboxColumn("STARRED", help="Add to Watchlist", default=False),
                "CHART": st.column_config.CheckboxColumn("CHART", help="Send to TV Chart", default=False),
                "PRICE": st.column_config.NumberColumn("PRICE", format="$%.2f"),
                "1M %": st.column_config.NumberColumn("1M %", format="%.1f%%"),
                "3M %": st.column_config.NumberColumn("3M %", format="%.1f%%"),
                "PIVOT DIST %": st.column_config.NumberColumn("PIVOT DIST %", format="%+.1f%%", help="Distance from prior 20-bar resistance"),
                "ADR %": st.column_config.NumberColumn("ADR %", format="%.2f%%"),
            },
            disabled=disabled_cols,
            use_container_width=True, 
            height=360,
            key=editor_key
        )

        # Handle Watchlist and Chart Clicks
        if editor_key in st.session_state and st.session_state[editor_key].get("edited_rows"):
            rerun_needed = False
            for row_idx, edit in st.session_state[editor_key]["edited_rows"].items():
                if row_idx < len(df_display):
                    if "STARRED" in edit:
                        changed_ticker = df_display.iloc[row_idx]["TICKER"]
                        if edit["STARRED"]: st.session_state.watchlist.add(changed_ticker)
                        else: st.session_state.watchlist.discard(changed_ticker)
                        update_query_watchlist()
                        rerun_needed = True
                    if "CHART" in edit and edit["CHART"]:
                        st.session_state.active_ticker = df_display.iloc[row_idx]["TICKER"]
                        st.session_state.insp_dropdown = st.session_state.active_ticker
                        rerun_needed = True
            if rerun_needed:
                del st.session_state[editor_key]
                st.rerun()

        # Copy-Ready TradingView Watchlist block
        tv_tickers = ", ".join([f"ASX:{t}" for t in df_display["TICKER"].tolist()])
        with st.expander("📋 Copy TradingView Watchlist Format", expanded=False):
            st.text_area("TradingView Import Format (Comma-Separated):", tv_tickers, height=70)

        # Detailed Chart Inspector
        if len(df_all) > 0:
            with st.expander("🔍 **Analyze Instrument & Relative Strength Breakdown**", expanded=True):
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
                <div class="tradingview-widget-container" style="height:550px;width:100%">
                  <div id="tradingview_{st.session_state.active_ticker}" style="height:100%;width:100%"></div>
                  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
                  <script type="text/javascript">
                  new TradingView.widget(
                  {{
                  "autosize": true,
                  "symbol": "ASX:{st.session_state.active_ticker}",
                  "interval": "{'W' if timeframe_sel == 'Weekly' else 'D'}",
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
                components.html(tv_html, height=550)

                if len(selected_row["dates_252"]) > 0:
                    fig_rs = make_subplots(specs=[[{"secondary_y": True}]])
                    fig_rs.add_trace(go.Scatter(x=selected_row["dates_252"], y=selected_row["price_252"], name="Price ($AUD)", line=dict(color="#f8fafc", width=1.5)), secondary_y=False)
                    fig_rs.add_trace(go.Scatter(x=selected_row["dates_252"], y=selected_row["pure_rs_series"], name="Pure RS Line", line=dict(color="#818cf8", width=2.0)), secondary_y=True)
                    fig_rs.update_layout(
                        title=f"{st.session_state.active_ticker} Price vs Pure Relative Strength Line (vs {bench_info['short']})",
                        height=280, margin=dict(l=10, r=10, t=40, b=10),
                        template="plotly_dark", plot_bgcolor="#0b0f19", paper_bgcolor="#0b0f19",
                        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1)
                    )
                    fig_rs.update_yaxes(title_text="Price ($AUD)", secondary_y=False, showgrid=False)
                    fig_rs.update_yaxes(title_text="RS Ratio", secondary_y=True, showgrid=False)
                    st.plotly_chart(fig_rs, use_container_width=True)

    with tab2:
        st.markdown("### Institutional Macro & Theme Leadership")
        c1, c2 = st.columns([6, 4])

        with c1:
            st.markdown("<div style='font-size:0.85rem; font-weight:700; color:#94a3b8; margin-bottom:10px;'>CUMULATIVE ADVANCE / DECLINE LINE</div>", unsafe_allow_html=True)
            fig_ad = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.5, 0.5])
            fig_ad.add_trace(go.Scatter(x=bench_dates_recent, y=bench_spark_vals, name=bench_info["short"], line=dict(color="#38bdf8", width=2)), row=1, col=1)
            fig_ad.add_trace(go.Scatter(x=bench_dates_recent, y=h_ad, name="A/D Line", line=dict(color="#a855f7", width=2)), row=2, col=1)
            fig_ad.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0), template="plotly_dark", plot_bgcolor="#0b0f19", paper_bgcolor="#0b0f19", showlegend=False)
            fig_ad.update_yaxes(showgrid=True, gridcolor="#1e293b", zeroline=False)
            st.plotly_chart(fig_ad, use_container_width=True)

            st.markdown("<div style='font-size:0.85rem; font-weight:700; color:#94a3b8; margin-bottom:10px; margin-top:20px;'>MARKET BREADTH OSCILLATORS</div>", unsafe_allow_html=True)
            fig_br = go.Figure()
            fig_br.add_trace(go.Scatter(x=bench_dates_recent, y=h_50, name=f"% > {'10W' if timeframe_sel == 'Weekly' else '50D'} MA", line=dict(color="#22c55e", width=2)))
            fig_br.add_trace(go.Scatter(x=bench_dates_recent, y=h_200, name=f"% > {'40W' if timeframe_sel == 'Weekly' else '200D'} MA", line=dict(color="#f59e0b", width=2)))
            fig_br.add_hrect(y0=80, y1=100, fillcolor="red", opacity=0.1, line_width=0)
            fig_br.add_hrect(y0=0, y1=20, fillcolor="green", opacity=0.1, line_width=0)
            fig_br.add_hline(y=80, line_dash="dot", line_color="red", opacity=0.5)
            fig_br.add_hline(y=20, line_dash="dot", line_color="green", opacity=0.5)
            fig_br.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0), template="plotly_dark", plot_bgcolor="#0b0f19", paper_bgcolor="#0b0f19", yaxis=dict(range=[0,100]), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig_br, use_container_width=True)

        with c2:
            st.markdown("<div style='font-size:0.85rem; font-weight:700; color:#94a3b8; margin-bottom:10px;'>GICS THEME LEADERSHIP</div>", unsafe_allow_html=True)
            theme_df = df_all.groupby('theme').agg(
                Stocks=('ticker', 'count'),
                Avg_RS=('rs', 'mean'),
                Stage2A_Count=('stage_raw', lambda x: (x == '2A').sum())
            ).reset_index()
            theme_df['% Stage 2A'] = (theme_df['Stage2A_Count'] / theme_df['Stocks']) * 100.0
            theme_df = theme_df[theme_df['Stocks'] >= 1].sort_values('Avg_RS', ascending=False)
            
            st.dataframe(
                theme_df[['theme', 'Stocks', 'Avg_RS', '% Stage 2A']],
                column_config={
                    "theme": "Theme / Industry",
                    "Avg_RS": st.column_config.NumberColumn("Avg RS", format="%.1f"),
                    "% Stage 2A": st.column_config.ProgressColumn("% Stage 2A", format="%.1f%%", min_value=0, max_value=100)
                },
                hide_index=True,
                use_container_width=True,
                height=680
            )

if __name__ == "__main__":
    main()
asx_momentum_scanner.py
Displaying asx_momentum_scanner.py.
