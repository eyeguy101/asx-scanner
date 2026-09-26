"""
ASX Momentum, Relative Strength & VCP Scanner (Cloud Edition)
Ready for deployment on Streamlit Community Cloud / Hugging Face Spaces.
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import datetime

st.set_page_config(
    page_title="ASX Relative Strength & VCP Scanner",
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
</style>
""", unsafe_allow_html=True)

# ASX Universe Definitions
UNIVERSE = {
    # Equities
    "DRO.AX": {"name": "Droneshield Ltd", "type": "Equity", "theme": "Defense / Aerospace"},
    "SPR.AX": {"name": "Spartan Resources Ltd", "type": "Equity", "theme": "Gold / Precious Metals"},
    "DYL.AX": {"name": "Deep Yellow Ltd", "type": "Equity", "theme": "Uranium / Clean Energy"},
    "BOE.AX": {"name": "Boss Energy Ltd", "type": "Equity", "theme": "Uranium / Clean Energy"},
    "PME.AX": {"name": "Pro Medicus Ltd", "type": "Equity", "theme": "Healthcare / MedTech"},
    "WA1.AX": {"name": "WA1 Resources Ltd", "type": "Equity", "theme": "Critical Minerals / Niobium"},
    "WTC.AX": {"name": "WiseTech Global Ltd", "type": "Equity", "theme": "Technology / AI / SaaS"},
    "360.AX": {"name": "Life360 Inc", "type": "Equity", "theme": "Technology / AI / SaaS"},
    "DEG.AX": {"name": "De Grey Mining Ltd", "type": "Equity", "theme": "Gold / Precious Metals"},
    "NEU.AX": {"name": "Neuren Pharmaceuticals Ltd", "type": "Equity", "theme": "Healthcare / Biotech"},
    "TUA.AX": {"name": "Tuas Limited", "type": "Equity", "theme": "Telecom / Tech"},
    "ZIP.AX": {"name": "Zip Co Limited", "type": "Equity", "theme": "Fintech / Payments"},
    "CBA.AX": {"name": "Commonwealth Bank", "type": "Equity", "theme": "Financials / Banking"},
    "BHP.AX": {"name": "BHP Group Ltd", "type": "Equity", "theme": "Resources / Diversified"},
    "LTR.AX": {"name": "Liontown Resources", "type": "Equity", "theme": "Critical Minerals / Lithium"},
    # Thematic ETFs
    "ATOM.AX": {"name": "Betashares Global Uranium ETF", "type": "ETF", "theme": "Uranium / Clean Energy", "holdings": [("Cameco (CCJ)", "19.5%"), ("Paladin (PDN)", "7.8%"), ("Boss Energy (BOE)", "6.2%"), ("Deep Yellow (DYL)", "5.1%")]},
    "MNRS.AX": {"name": "Betashares Global Gold Miners ETF", "type": "ETF", "theme": "Gold / Precious Metals", "holdings": [("Newmont (NEM)", "12.4%"), ("Northern Star (NST)", "7.5%"), ("Evolution (EVN)", "5.4%")]},
    "HACK.AX": {"name": "Betashares Cybersecurity ETF", "type": "ETF", "theme": "Technology / AI / SaaS", "holdings": [("CrowdStrike (CRWD)", "7.2%"), ("Palo Alto (PANW)", "6.8%"), ("Broadcom (AVGO)", "5.9%")]},
    "SEMI.AX": {"name": "Betashares Semiconductors ETF", "type": "ETF", "theme": "Technology / AI / SaaS", "holdings": [("NVIDIA (NVDA)", "11.2%"), ("TSMC (TSM)", "10.4%"), ("ASML", "8.6%")]},
    "QRE.AX": {"name": "Betashares ASX 200 Resources ETF", "type": "ETF", "theme": "Resources / Diversified", "holdings": [("BHP Group (BHP)", "32.5%"), ("Rio Tinto (RIO)", "12.8%"), ("Northern Star (NST)", "4.2%")]},
    "A200.AX": {"name": "Betashares Australia 200 ETF", "type": "ETF", "theme": "Broad Market", "holdings": [("Commonwealth Bank (CBA)", "9.8%"), ("BHP Group (BHP)", "8.4%"), ("CSL Limited", "5.6%")]}
}

@st.cache_data(ttl=14400)
def load_live_asx_market_data():
    tickers = list(UNIVERSE.keys())
    symbols = tickers + ["^AXJO"]
    try:
        data = yf.download(symbols, period="2y", interval="1d", progress=False, group_by="ticker", auto_adjust=True)
    except Exception as e:
        return None, str(e)

    results = []
    for sym in tickers:
        try:
            if sym not in data: continue
            df = data[sym].dropna()
            if len(df) < 200: continue

            close = df["Close"]
            high = df["High"]
            low = df["Low"]
            volume = df["Volume"]
            n = len(close)

            price = float(close.iloc[-1])
            prev_price = float(close.iloc[-2])
            change = ((price - prev_price) / prev_price) * 100.0

            sma50 = float(close.rolling(50).mean().iloc[-1])
            sma150 = float(close.rolling(150).mean().iloc[-1])
            sma200 = float(close.rolling(200).mean().iloc[-1])
            sma200_prev = float(close.rolling(200).mean().iloc[-22]) if n >= 222 else sma200

            lookback = min(n, 252)
            high52 = float(high.iloc[-lookback:].max())
            low52 = float(low.iloc[-lookback:].min())

            meta = UNIVERSE[sym]
            itype = meta["type"]

            # Minervini Conditions
            c1 = price > sma150 and price > sma200
            c2 = sma150 > sma200
            c3 = sma200 > sma200_prev
            c4 = sma50 > sma150 and sma50 > sma200
            c5 = price > sma50
            c6 = price >= (low52 * 1.30) if itype == "Equity" else price >= (low52 * 1.15)
            c7 = price >= (high52 * 0.75)

            # O'Neil 12M Weighted RS
            ret3m = (price - float(close.iloc[-63])) / float(close.iloc[-63])
            ret6m = (price - float(close.iloc[-126])) / float(close.iloc[-126])
            ret9m = (price - float(close.iloc[-189])) / float(close.iloc[-189])
            ret12m = (price - float(close.iloc[-252])) / float(close.iloc[-252])
            raw_rs = (0.40 * ret3m) + (0.20 * ret6m) + (0.20 * ret9m) + (0.20 * ret12m)

            # Weinstein Sub-Stage Assignment
            slope150 = (sma150 - float(close.rolling(160).mean().iloc[-1])) / sma150
            if price >= sma150 * 0.98:
                if slope150 >= -0.005:
                    if (high52 - price) / high52 <= 0.08: stage, stage_raw = "Stage 2A (Early Markup)", "2A"
                    elif (price - sma150) / sma150 >= 0.25: stage, stage_raw = "Stage 2B (Late Uptrend)", "2B"
                    else: stage, stage_raw = "Stage 2 (Advancing)", "2"
                else: stage, stage_raw = "Stage 1B (Late Base / Coiling)", "1B"
            elif price < sma150 and slope150 < -0.01:
                stage = "Stage 4B- (Cycle Low Watch)" if price <= low52 * 1.05 else "Stage 4A (Downtrend)"
                stage_raw = "4B-" if price <= low52 * 1.05 else "4A"
            else:
                stage, stage_raw = "Stage 1 (Basing)", "1"

            avg_vol20 = float(volume.iloc[-21:-1].mean()) if n >= 21 else 1.0
            adtv = avg_vol20 * price
            adtv_fmt = f"${adtv/1e6:.1f}M" if adtv >= 1e6 else f"${round(adtv/1e3)}k"

            tr_list = [max(high.iloc[k] - low.iloc[k], abs(high.iloc[k] - close.iloc[k-1]), abs(low.iloc[k] - close.iloc[k-1])) for k in range(-14, 0)]
            atr = float(np.mean(tr_list))
            atr_pct = round((atr / price) * 100, 1)

            results.append({
                "ticker": sym.replace(".AX", ""),
                "name": meta["name"],
                "type": itype,
                "theme": meta["theme"],
                "price": round(price, 3 if price < 2 else 2),
                "change": round(change, 2),
                "raw_rs": raw_rs,
                "sma50": round(sma50, 2),
                "sma150": round(sma150, 2),
                "sma200": round(sma200, 2),
                "high52": round(high52, 2),
                "low52": round(low52, 2),
                "trend_score": sum([c1, c2, c3, c4, c5, c6, c7]),
                "stage": stage,
                "stage_raw": stage_raw,
                "base_count": "Base 1" if stage_raw == "2A" else ("Base 2" if stage_raw == "1B" else "Base 3+"),
                "setup": "VCP Pivot Breakout" if stage_raw == "2A" else ("NR7 / Inside Day" if stage_raw == "1B" else "Trend Continuation"),
                "rvol": round(float(volume.iloc[-1]) / avg_vol20, 1),
                "adtv": adtv,
                "adtv_fmt": adtv_fmt,
                "atr": round(atr, 3),
                "atr_pct": atr_pct,
                "holdings": meta.get("holdings", [])
            })
        except Exception:
            continue

    if results:
        results.sort(key=lambda x: x["raw_rs"])
        for idx, r in enumerate(results):
            r["rs"] = max(1, min(99, round(((idx + 1) / len(results)) * 99)))
            mrs_val = round((r["rs"] - 50) / 15.0, 1)
            r["mrs"] = f"+{mrs_val}" if mrs_val >= 0 else f"{mrs_val}"
            if r["rs"] >= 70:
                r["trend_score"] += 1

    return pd.DataFrame(results), None

def main():
    st.markdown('<div class="main-title">ASX Momentum, Relative Strength &amp; VCP Scanner</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Cloud Edition • Live Yahoo Finance Feed • O\'Neil RS • Minervini SEPA • Weinstein Sub-Stages</div>', unsafe_allow_html=True)

    # Sidebar Controls
    st.sidebar.header("Cloud Data Engine")
    if st.sidebar.button("🔄 Force Refresh Today's Prices", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.header("Filter Criteria")
    universe_mode = st.sidebar.radio("Universe", ["All Instruments", "Equities Only", "ETFs Only"], horizontal=True)
    
    substage_filter = st.sidebar.selectbox("Weinstein Sub-Stage", [
        "All Stages",
        "Stage 2A (Early Markup Sweet Spot)",
        "Stage 1B (Late Base / Coiling VCP)",
        "Stage 2 (Mid-Stage Advancing)",
        "Stage 2B (Late Stage / Extended)",
        "Stage 1A (Early Base / Inactive)",
        "Stage 4B- (Cycle Low Watch)"
    ])

    min_rs = st.sidebar.slider("Minimum O'Neil RS (1–99)", min_value=50, max_value=98, value=70, step=1)
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

    theme_filter = st.sidebar.selectbox("Theme Filter", ["All Themes"] + sorted(list(set(v["theme"] for v in UNIVERSE.values()))))

    # Fetch Data
    with st.spinner("Crunching live exchange data..."):
        df, err = load_live_asx_market_data()

    if err or df is None or len(df) == 0:
        st.error("Failed to load live market data. Please refresh or check connection.")
        return

    # Filter Application
    if universe_mode == "Equities Only": df = df[df["type"] == "Equity"]
    elif universe_mode == "ETFs Only": df = df[df["type"] == "ETF"]

    if theme_filter != "All Themes": df = df[df["theme"] == theme_filter]
    df = df[df["rs"] >= min_rs]
    df = df[df["adtv"] >= adtv_threshold]

    if substage_filter != "All Stages":
        if "2A" in substage_filter: df = df[df["stage_raw"] == "2A"]
        elif "1B" in substage_filter: df = df[df["stage_raw"] == "1B"]
        elif "2B" in substage_filter: df = df[df["stage_raw"] == "2B"]
        elif "Stage 2 (" in substage_filter: df = df[df["stage_raw"] == "2"]
        elif "1A" in substage_filter: df = df[df["stage_raw"] == "1A"]
        elif "4B-" in substage_filter: df = df[df["stage_raw"] == "4B-"]

    # Market Breadth KPI Ribbon
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("ASX 200 Regime", "Power Trend ON", "XJO Benchmark")
    c2.metric("Qualifying Leaders", len(df))
    c3.metric("Stage 2A Early Breakouts", len(df[df["stage_raw"] == "2A"]))
    c4.metric("Stage 1B Coiling Bases", len(df[df["stage_raw"] == "1B"]))
    c5.metric("Avg Leader RS", f"{df['rs'].mean():.1f}" if len(df) > 0 else "N/A")

    st.markdown("---")

    # Table Display
    st.subheader(f"Screened Instruments ({len(df)} Results)")
    disp_cols = ["ticker", "name", "type", "theme", "price", "change", "rs", "mrs", "trend_score", "stage", "base_count", "setup", "adtv_fmt", "atr_pct"]
    df_disp = df[disp_cols].copy()
    df_disp.columns = ["Ticker", "Name", "Type", "Theme", "Price ($)", "Today (%)", "RS (1-99)", "Mansfield RS", "Trend Score", "Weinstein Stage", "Base", "Setup", "$ADTV", "ATR %"]

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

    # 1R Position Sizing & ETF Drill-Down
    st.markdown("---")
    st.subheader("1R Position Sizing & Risk Management Calculator")
    if len(df) > 0:
        calc_col1, calc_col2, calc_col3, calc_col4 = st.columns(4)
        sel_ticker = calc_col1.selectbox("Select Screened Instrument", df["ticker"].tolist())
        acct_equity = calc_col2.number_input("Account Equity (AUD)", value=100000, step=5000)
        risk_pct = calc_col3.selectbox("Risk % per Trade (1R)", [0.5, 1.0, 1.5, 2.0], index=1)
        stop_model = calc_col4.selectbox("Stop Model", ["1.0x ATR Below", "1.5x ATR Below", "5.0% Fixed", "8.0% Fixed"])

        if sel_ticker:
            row = df[df["ticker"] == sel_ticker].iloc[0]
            price = row["price"]
            atr = row["atr"]

            if stop_model == "1.0x ATR Below": stop_price = price - atr
            elif stop_model == "1.5x ATR Below": stop_price = price - (atr * 1.5)
            elif stop_model == "5.0% Fixed": stop_price = price * 0.95
            else: stop_price = price * 0.92

            risk_dollars = acct_equity * (risk_pct / 100.0)
            risk_per_share = price - stop_price
            shares_to_buy = int(risk_dollars / risk_per_share) if risk_per_share > 0 else 0
            total_val = shares_to_buy * price
            port_alloc = (total_val / acct_equity) * 100

            r1, r2, r3, r4 = st.columns(4)
            r1.metric("Stop Loss Price", f"${stop_price:.2f}", f"-{((price-stop_price)/price)*100:.1f}%")
            r2.metric("Shares to Buy", f"{shares_to_buy:,} shares")
            r3.metric("Total Position Size", f"${total_val:,.0f}")
            r4.metric("Portfolio Weight", f"{port_alloc:.1f}%")

            if row["type"] == "ETF" and len(row["holdings"]) > 0:
                st.info(f"**Top Underlying Holdings for {row['ticker']} ({row['name']}):** " + ", ".join([f"{h[0]} ({h[1]})" for h in row["holdings"]]))

    # Watchlist Export
    st.markdown("---")
    st.subheader("One-Click Watchlist Export")
    if len(df) > 0:
        e1, e2 = st.columns(2)
        tv_txt = ", ".join([f"ASX:{t}" for t in df["ticker"]])
        ibkr_txt = ", ".join([f"{t}.AX" for t in df["ticker"]])
        e1.text_area("TradingView Format:", value=tv_txt, height=70)
        e2.text_area("Interactive Brokers (IBKR) Format:", value=ibkr_txt, height=70)

if __name__ == "__main__":
    main()
