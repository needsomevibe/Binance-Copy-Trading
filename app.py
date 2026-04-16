import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import time
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.scraper import BinanceScraper

st.set_page_config(
    page_title="Binance Copy Trading Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* ── Global ── */
    [data-testid="stAppViewContainer"] {
        background: #0d1117;
        color: #e6edf3;
    }
    [data-testid="stSidebar"] {
        background: #161b22;
        border-right: 1px solid #30363d;
    }
    [data-testid="stSidebar"] * { color: #e6edf3 !important; }

    /* ── Hide default header ── */
    header[data-testid="stHeader"] { display: none; }

    /* ── App title banner ── */
    .app-header {
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        border: 1px solid #f59e0b33;
        border-radius: 12px;
        padding: 20px 28px;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .app-header h1 {
        margin: 0;
        font-size: 1.7rem;
        font-weight: 700;
        background: linear-gradient(90deg, #f59e0b, #fbbf24);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .app-header p { margin: 4px 0 0; color: #9ca3af; font-size: 0.85rem; }

    /* ── Metric cards ── */
    .kpi-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 14px; margin-bottom: 20px; }
    .kpi-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 18px 20px;
        text-align: center;
        transition: border-color .2s;
    }
    .kpi-card:hover { border-color: #f59e0b88; }
    .kpi-card .label { font-size: 0.75rem; color: #8b949e; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 6px; }
    .kpi-card .value { font-size: 1.6rem; font-weight: 700; }
    .kpi-card .value.green { color: #3fb950; }
    .kpi-card .value.red   { color: #f85149; }
    .kpi-card .value.yellow{ color: #f59e0b; }
    .kpi-card .value.blue  { color: #58a6ff; }

    /* ── Info rows inside deep-dive ── */
    .info-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #21262d; font-size: 0.9rem; }
    .info-row .key  { color: #8b949e; }
    .info-row .val  { color: #e6edf3; font-weight: 500; }

    /* ── Sidebar form ── */
    [data-testid="stForm"] {
        background: #0d1117;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 16px;
    }
    /* Submit button */
    [data-testid="stFormSubmitButton"] > button {
        width: 100%;
        background: linear-gradient(135deg, #f59e0b, #d97706) !important;
        color: #000 !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 0 !important;
        font-size: 1rem !important;
        letter-spacing: .03em;
        transition: opacity .2s !important;
    }
    [data-testid="stFormSubmitButton"] > button:hover { opacity: .85 !important; }

    /* Clear filters button */
    .stButton > button {
        background: #21262d !important;
        color: #e6edf3 !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
        font-size: 0.85rem !important;
        padding: 6px 16px !important;
        transition: border-color .2s !important;
    }
    .stButton > button:hover { border-color: #f85149 !important; color: #f85149 !important; }

    /* ── Tabs ── */
    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        background: #161b22;
        border-radius: 8px;
        padding: 4px;
        gap: 4px;
    }
    [data-testid="stTabs"] [data-baseweb="tab"] {
        background: transparent !important;
        border-radius: 6px !important;
        color: #8b949e !important;
        font-weight: 500 !important;
    }
    [data-testid="stTabs"] [aria-selected="true"] {
        background: #f59e0b22 !important;
        color: #f59e0b !important;
    }

    /* ── Dataframe ── */
    [data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }

    /* ── Expander ── */
    [data-testid="stExpander"] {
        background: #161b22;
        border: 1px solid #30363d !important;
        border-radius: 10px !important;
    }

    /* ── Selectbox / inputs ── */
    [data-testid="stSelectbox"] > div > div,
    [data-testid="stNumberInput"] > div > div > input {
        background: #0d1117 !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
        color: #e6edf3 !important;
    }

    /* ── Progress bar ── */
    [data-testid="stProgressBar"] > div > div { background: #f59e0b !important; }

    /* ── Divider ── */
    hr { border-color: #21262d !important; }

    /* ── Warning / info / success banners ── */
    [data-testid="stAlert"] { border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

# ── Header banner ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <div>
        <h1>📈 Binance Copy Trading Intelligence</h1>
        <p>Real-time trader analytics & deep-dive scanning powered by Binance API</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Initialize Scraper ─────────────────────────────────────────────────────────
if 'scraper' not in st.session_state:
    st.session_state.scraper = BinanceScraper()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Control Panel")
    st.divider()
    with st.form("scrape_config"):
        pages = st.slider("📄 Scrape Depth (Pages)", 1, 10, 2)
        t_range = st.selectbox("🕐 Time Range", ["7D", "30D", "90D", "180D"], index=1)
        sort = st.selectbox("📊 Sort By", ["SHARP_RATIO", "ROI", "PNL", "MDD", "AUM", "COPY_TRADERS"])
        deep = st.toggle("🔬 Deep Scan", value=False, help="Fetches bio, asset allocation, open positions & trade history")
        st.markdown("")
        run = st.form_submit_button("🚀  Fetch Data")

    st.divider()
    st.markdown("<span style='color:#8b949e;font-size:.8rem'>Data sourced from Binance Copy Trading API</span>", unsafe_allow_html=True)

# ── Fetch ──────────────────────────────────────────────────────────────────────
if run:
    all_traders = []
    scraper = st.session_state.scraper
    bar = st.progress(0, text="Starting fetch…")
    status = st.empty()

    try:
        raw_traders = []
        for i in range(1, pages + 1):
            bar.progress((i / pages) * 0.5, text=f"📡 Fetching page {i} of {pages}…")
            batch = scraper.fetch_traders(page=i, time_range=t_range, data_type=sort)
            raw_traders.extend(batch)
            time.sleep(0.2)

        if deep:
            bar.progress(0.6, text=f"🔬 Deep scanning {len(raw_traders)} profiles…")
            all_traders = scraper.fetch_details_concurrently(raw_traders, t_range)
        else:
            bar.progress(0.7, text=f"⚙️ Processing {len(raw_traders)} profiles…")
            for t in raw_traders:
                all_traders.append(scraper.transform_for_llm(t, fetch_details=False, time_range=t_range))

        bar.progress(1.0, text="✅ Complete!")
        time.sleep(0.4)
        bar.empty()
        status.success(f"✅ Loaded **{len(all_traders)}** traders successfully.")
        st.session_state.master_data = all_traders

    except Exception as e:
        bar.empty()
        st.error(f"❌ Error: {e}")

# ── Guard ──────────────────────────────────────────────────────────────────────
if 'master_data' not in st.session_state:
    st.markdown("""
    <div style='text-align:center;padding:60px 20px;color:#8b949e;'>
        <div style='font-size:3rem;margin-bottom:16px'>👈</div>
        <div style='font-size:1.1rem;font-weight:600;color:#e6edf3;margin-bottom:8px'>Ready to explore traders?</div>
        <div>Configure the panel on the left and click <strong style='color:#f59e0b'>Fetch Data</strong> to begin.</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Flatten ────────────────────────────────────────────────────────────────────
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

if df.empty:
    st.warning("⚠️ No trader data returned. Try increasing the page count or changing the sort/time range.")
    st.stop()

# ── Filters ────────────────────────────────────────────────────────────────────
with st.expander("🔍 Filter Traders", expanded=True):
    if "f_roi"    not in st.session_state: st.session_state.f_roi    = 0.0
    if "f_sharpe" not in st.session_state: st.session_state.f_sharpe = 1.0
    if "f_mdd"    not in st.session_state: st.session_state.f_mdd    = 30.0
    if "f_aum"    not in st.session_state: st.session_state.f_aum    = 5000

    def clear_filters():
        st.session_state.f_roi    = -100.0
        st.session_state.f_sharpe = -20.0
        st.session_state.f_mdd    = 100.0
        st.session_state.f_aum    = 0

    fc1, fc2, fc3, fc4, fc5 = st.columns([1, 1, 1, 1, 0.5])
    f_roi    = fc1.number_input("📈 Min ROI %",       -100.0, 5000.0,    key="f_roi")
    f_sharpe = fc2.number_input("⚡ Min Sharpe",       -20.0,   20.0,    key="f_sharpe")
    f_mdd    = fc3.number_input("🛡 Max Drawdown %",    0.0,   100.0,    key="f_mdd")
    f_aum    = fc4.number_input("💰 Min AUM $",         0,  10_000_000,  key="f_aum")
    fc5.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    fc5.button("❌ Reset", on_click=clear_filters, use_container_width=True)

filtered_df = df[
    (df['ROI %']        >= f_roi) &
    (df['Sharpe']       >= f_sharpe) &
    (df['MDD %']        <= f_mdd) &
    (df['AUM $']        >= f_aum)
]

# ── Summary Stats ──────────────────────────────────────────────────────────────
n = len(filtered_df)
avg_roi  = filtered_df['ROI %'].mean()  if n else 0
avg_sharpe = filtered_df['Sharpe'].mean() if n else 0
total_aum  = filtered_df['AUM $'].sum()  if n else 0

s1, s2, s3, s4 = st.columns(4)
s1.metric("🧑‍💼 Traders Found",  f"{n}")
s2.metric("📈 Avg ROI",        f"{avg_roi:.2f}%")
s3.metric("⚡ Avg Sharpe",     f"{avg_sharpe:.2f}")
s4.metric("💰 Total AUM",      f"${total_aum:,.0f}")

st.divider()

# ── Table ──────────────────────────────────────────────────────────────────────
st.markdown(f"### 📊 Market Overview")
st.dataframe(
    filtered_df.drop(columns=['Raw']),
    use_container_width=True,
    hide_index=True,
    column_config={
        "Utilization %": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f%%"),
        "ROI %":  st.column_config.NumberColumn(format="%.2f%%"),
        "PnL $":  st.column_config.NumberColumn(format="$%.0f"),
        "AUM $":  st.column_config.NumberColumn(format="$%.0f"),
        "Sharpe": st.column_config.NumberColumn(format="%.2f"),
        "MDD %":  st.column_config.NumberColumn(format="%.2f%%"),
    }
)

st.divider()

# ── Deep Dive ──────────────────────────────────────────────────────────────────
st.markdown("### 🕵️ Trader Deep Dive")
sel_name = st.selectbox("Select a trader to analyse", filtered_df['Name'].unique(), label_visibility="collapsed")

if sel_name:
    trader_data = filtered_df[filtered_df['Name'] == sel_name].iloc[0]['Raw']
    m = trader_data.metrics

    # KPI Cards
    roi_cls   = "green" if m.roi >= 0 else "red"
    mdd_cls   = "red"   if m.mdd > 20 else "yellow"
    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi-card"><div class="label">ROI</div><div class="value {roi_cls}">{m.roi:.2f}%</div></div>
        <div class="kpi-card"><div class="label">Sharpe Ratio</div><div class="value blue">{m.sharpe:.2f}</div></div>
        <div class="kpi-card"><div class="label">Max Drawdown</div><div class="value {mdd_cls}">{m.mdd:.2f}%</div></div>
        <div class="kpi-card"><div class="label">AUM</div><div class="value yellow">${m.aum:,.0f}</div></div>
    </div>
    """, unsafe_allow_html=True)

    t1, t2, t3, t4 = st.tabs(["📌 Strategy & Risk", "📈 Performance Charts", "💼 Open Positions", "📜 Trade History"])

    with t1:
        if trader_data.deep_dive:
            dd = trader_data.deep_dive
            dc1, dc2 = st.columns(2)
            with dc1:
                st.markdown("#### 📄 About")
                churn_rate = 0.0
                if dd.total_copiers > 0:
                    churn_rate = ((dd.total_copiers - m.copiers) / dd.total_copiers) * 100
                for key, val in [
                    ("Bio", dd.bio),
                    ("Trader's Capital", f"${dd.trader_balance:,.2f}"),
                    ("Profit Share", f"{dd.profit_share}%"),
                    ("Min Investment", f"${dd.min_copy_amount:,.0f}"),
                ]:
                    st.markdown(f'<div class="info-row"><span class="key">{key}</span><span class="val">{val}</span></div>', unsafe_allow_html=True)
            with dc2:
                st.markdown("#### 🤝 Social Trust")
                p_color = "#3fb950" if dd.copier_pnl > 0 else "#f85149"
                for key, val in [
                    ("Follower Total PnL", f'<span style="color:{p_color}">${dd.copier_pnl:,.2f}</span>'),
                    ("Tags", ', '.join(dd.risk_tags) or "—"),
                    ("Lifetime Copiers", f"{dd.total_copiers:,}"),
                    ("Churn Rate", f"{churn_rate:.1f}%"),
                ]:
                    st.markdown(f'<div class="info-row"><span class="key">{key}</span><span class="val">{val}</span></div>', unsafe_allow_html=True)
        else:
            st.warning("🔬 Enable **Deep Scan** in the sidebar to unlock strategy & risk insights.")

    with t2:
        ch1, ch2 = st.columns([2, 1])
        with ch1:
            if trader_data.roi_history:
                hist = pd.DataFrame([h.model_dump() for h in trader_data.roi_history])
                fig = px.area(
                    hist, x='d', y='v',
                    title="📈 Equity Curve (ROI %)",
                    template="plotly_dark",
                    labels={'d': 'Date', 'v': 'ROI %'},
                )
                fig.update_traces(
                    line_color='#f59e0b',
                    fillcolor='rgba(245,158,11,0.12)',
                    hovertemplate='%{x}<br>ROI: %{y:.2f}%<extra></extra>'
                )
                fig.update_layout(
                    plot_bgcolor='#161b22', paper_bgcolor='#161b22',
                    font_color='#e6edf3', title_font_color='#f59e0b',
                    margin=dict(l=10, r=10, t=40, b=10)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No ROI history available.")
        with ch2:
            if trader_data.deep_dive and trader_data.deep_dive.assets:
                assets = pd.DataFrame([a.model_dump() for a in trader_data.deep_dive.assets])
                fig2 = px.pie(
                    assets, values='volume_percent', names='asset',
                    title="🪙 Traded Coins", hole=0.5,
                    template="plotly_dark",
                    color_discrete_sequence=px.colors.sequential.Oranges_r
                )
                fig2.update_layout(
                    plot_bgcolor='#161b22', paper_bgcolor='#161b22',
                    font_color='#e6edf3', title_font_color='#f59e0b',
                    margin=dict(l=10, r=10, t=40, b=10)
                )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No asset data (Deep Scan required).")

    with t3:
        if trader_data.deep_dive and trader_data.deep_dive.positions:
            st.dataframe(pd.DataFrame([p.model_dump() for p in trader_data.deep_dive.positions]), use_container_width=True, hide_index=True)
        else:
            st.info("No active positions found.")

    with t4:
        if trader_data.deep_dive and trader_data.deep_dive.history:
            st.dataframe(pd.DataFrame(trader_data.deep_dive.history), use_container_width=True, hide_index=True)
        else:
            st.info("No trade history available.")

    st.divider()
    with st.expander("🤖 LLM-Ready JSON Export"):
        st.code(trader_data.model_dump_json(indent=2), language='json')