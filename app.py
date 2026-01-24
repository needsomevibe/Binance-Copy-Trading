import streamlit as st
import pandas as pd
import plotly.express as px
import json
import time
# Import from the new package structure
# We need to make sure python can find the src module. 
# For simple running, we might need to adjust sys.path or run as module.
# To keep it simple for the user, we will keep app.py at root and import relatively.
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.scraper import BinanceScraper

st.set_page_config(page_title="Binance Copy Trading Intelligence", page_icon="📈", layout="wide")

# Initialize Scraper
if 'scraper' not in st.session_state:
    st.session_state.scraper = BinanceScraper()

# Sidebar
st.sidebar.title("🛠️ Control Panel")
with st.sidebar.form("scrape_config"):
    pages = st.slider("Scrape Depth (Pages)", 1, 10, 2)
    t_range = st.selectbox("Metrics Time Range", ["7D", "30D", "90D", "180D"], index=1)
    sort = st.selectbox("API Sort", ["SHARP_RATIO", "ROI", "PNL", "MDD", "AUM", "COPY_TRADERS"])
    deep = st.checkbox("Deep Scan (Bio, Assets, History)", value=False)
    run = st.form_submit_button("🚀 Fetch Data")

if run:
    all_traders = []
    scraper = st.session_state.scraper
    bar = st.progress(0)
    status = st.empty()
    
    try:
        raw_traders = []
        # Phase 1: Fetch Lists
        for i in range(1, pages + 1):
            status.text(f"Fetching page {i}/{pages}...")
            batch = scraper.fetch_traders(page=i, time_range=t_range, data_type=sort)
            raw_traders.extend(batch)
            bar.progress((i / pages) * 0.5) # 50% for list fetching
            time.sleep(0.2) # Rate limit politeness

        # Phase 2: Processing / Deep Scan
        status.text(f"Processing {len(raw_traders)} profiles...")
        if deep:
            # Use the concurrent fetcher
            status.text(f"Deep scanning {len(raw_traders)} profiles (Concurrent)...")
            all_traders = scraper.fetch_details_concurrently(raw_traders, t_range)
        else:
            for t in raw_traders:
                all_traders.append(scraper.transform_for_llm(t, fetch_details=False, time_range=t_range))
        
        bar.progress(1.0)
        status.success("Done!")
        st.session_state.master_data = all_traders
        
    except Exception as e:
        st.error(f"An error occurred: {e}")

# Main Logic
if 'master_data' not in st.session_state:
    st.info("👈 Configure and click 'Fetch Data' to begin.")
    st.stop()

# Data Flattening for Table
rows = []
for d in st.session_state.master_data:
    rows.append({
        "Name": d.profile.nickname,
        "ROI %": d.metrics.roi,
        "PnL $": d.metrics.pnl,
        "Sharpe": d.metrics.sharpe,
        "MDD %": d.metrics.mdd,
        "AUM $": d.metrics.aum,
        "Utilization %": d.metrics.utilization,
        "Trend": d.trend,
        "Raw": d
    })
df = pd.DataFrame(rows)

# Advanced Global Filters
with st.expander("🔍 Filter Results", expanded=True):
    # Initialize session state for filters
    if "f_roi" not in st.session_state: st.session_state.f_roi = 0.0
    if "f_sharpe" not in st.session_state: st.session_state.f_sharpe = 1.0
    if "f_mdd" not in st.session_state: st.session_state.f_mdd = 30.0
    if "f_aum" not in st.session_state: st.session_state.f_aum = 5000

    def clear_filters():
        st.session_state.f_roi = -100.0
        st.session_state.f_sharpe = -20.0
        st.session_state.f_mdd = 100.0
        st.session_state.f_aum = 0

    c1, c2, c3, c4 = st.columns(4)
    f_roi = c1.number_input("Min ROI %", -100.0, 5000.0, key="f_roi")
    f_sharpe = c2.number_input("Min Sharpe", -20.0, 20.0, key="f_sharpe")
    f_mdd = c3.number_input("Max Drawdown %", 0.0, 100.0, key="f_mdd")
    f_aum = c4.number_input("Min AUM $", 0, 10000000, key="f_aum")
    
    if st.button("❌ Clear Filters", on_click=clear_filters):
        pass # Rerun to apply state changes

filtered_df = df[
    (df['ROI %'] >= f_roi) & 
    (df['Sharpe'] >= f_sharpe) & 
    (df['MDD %'] <= f_mdd) & 
    (df['AUM $'] >= f_aum)
]

# Summary Table
st.subheader(f"📊 Market Overview ({len(filtered_df)} Traders Found)")
st.dataframe(
    filtered_df.drop(columns=['Raw']),
    width="stretch",
    hide_index=True,
    column_config={
        "Utilization %": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f%%"),
        "ROI %": st.column_config.NumberColumn(format="%.2f%%"),
        "PnL $": st.column_config.NumberColumn(format="$%.0f"),
        "AUM $": st.column_config.NumberColumn(format="$%.0f"),
    }
)

# Deep Dive Analysis
st.divider()
st.subheader("🕵️ Selected Trader Deep Dive")
sel_name = st.selectbox("Choose Trader", filtered_df['Name'].unique())

if sel_name:
    trader_data = filtered_df[filtered_df['Name'] == sel_name].iloc[0]['Raw']
    m = trader_data.metrics
    
    # KPI Cards
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("ROI", f"{m.roi:.2f}%")
    k2.metric("Sharpe Ratio", f"{m.sharpe:.2f}")
    k3.metric("Max Drawdown", f"{m.mdd:.2f}%", delta_color="inverse")
    k4.metric("AUM", f"${m.aum:,.0f}")

    # Analysis Tabs
    t1, t2, t3, t4 = st.tabs(["📌 Strategy & Risk", "📈 Performance Charts", "💼 Open Positions", "📜 Trade History"])
    
    with t1:
        if trader_data.deep_dive:
            dd = trader_data.deep_dive
            dc1, dc2 = st.columns(2)
            with dc1:
                st.markdown("#### About")
                st.write(f"**Bio:** {dd.bio}")
                st.write(f"**Trader's Own Capital:** ${dd.trader_balance:,.2f}")
                st.write(f"**Profit Share:** {dd.profit_share}%")
                st.write(f"**Min Investment:** ${dd.min_copy_amount:,.0f}")
            with dc2:
                st.markdown("#### Social Trust")
                p_color = "green" if dd.copier_pnl > 0 else "red"
                st.markdown(f"**Follower Total PnL:** :{p_color}[${dd.copier_pnl:,.2f}]")
                st.write(f"**Tags:** {', '.join(dd.risk_tags)}")
                
                churn_rate = 0.0
                if dd.total_copiers > 0:
                    churn_rate = ((dd.total_copiers - m.copiers) / dd.total_copiers) * 100
                st.write(f"**Lifetime Copiers:** {dd.total_copiers}")
                st.write(f"**Churn Rate:** {churn_rate:.1f}%")
        else:
            st.warning("Enable 'Deep Scan' in sidebar to unlock these insights.")

    with t2:
        c1, c2 = st.columns([2, 1])
        with c1:
            if trader_data.roi_history:
                hist = pd.DataFrame([h.model_dump() for h in trader_data.roi_history])
                st.plotly_chart(px.line(hist, x='d', y='v', title="Equity Curve (ROI %)", template="plotly_dark"), width="stretch")
        with c2:
            if trader_data.deep_dive and trader_data.deep_dive.assets:
                assets = pd.DataFrame([a.model_dump() for a in trader_data.deep_dive.assets])
                st.plotly_chart(px.pie(assets, values='volume_percent', names='asset', title="Traded Coins", hole=0.4))

    with t3:
        if trader_data.deep_dive and trader_data.deep_dive.positions:
            st.dataframe(pd.DataFrame([p.model_dump() for p in trader_data.deep_dive.positions]), width="stretch")
        else:
            st.info("No active positions found.")

    with t4:
        if trader_data.deep_dive and trader_data.deep_dive.history:
            st.dataframe(pd.DataFrame(trader_data.deep_dive.history), width="stretch")
        else:
            st.info("No trade history available.")

    # LLM Export
    with st.expander("🤖 LLM-Ready Data (JSON)"):
        st.code(trader_data.model_dump_json(indent=2), language='json')