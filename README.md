# 📈 Binance Copy Trading Intelligence (BCTI)

An institutional-grade analytics suite and dashboard designed to audit, filter, and monitor top-performing lead traders on the Binance Copy Trading platform. BCTI provides deep-dive insights that go beyond the standard UI, helping investors identify sustainable alpha while avoiding high-churn "burn-and-turn" strategies.

## 🚀 Core Features

*   **Institutional Metrics:** Track advanced data points including **Lifetime Copier Count**, **User Retention (Churn Rate)**, and **Lead Trader Own Capital (Balance)**.
*   **Multi-Timeframe Analysis:** Native support for 7D, 30D, 90D, and **180D** performance windows to distinguish short-term luck from long-term skill.
*   **Deep-Scan Auditing:** Automatically fetches bio data, risk tags, historical trade distribution, and real-time open positions.
*   **Portfolio Health:** Interactive equity curves (ROI %) and asset allocation charts powered by Plotly.
*   **Advanced Filtering:** Global filtering engine for ROI, Sharpe Ratio, Maximum Drawdown (MDD), and AUM.
*   **LLM-Ready Export:** Generates structured, type-safe JSON snapshots of trader profiles for integration with AI analysis tools.

## 🛠️ Technical Architecture

*   **Data Layer:** Robust `BinanceScraper` utilizing `requests.Session` with **Tenacity-backed retry logic** and exponential backoff for rate-limit resilience.
*   **Type Safety:** Powered by **Pydantic V2** models to ensure strict data validation and integrity across all API responses.
*   **Concurrency:** High-performance `ThreadPoolExecutor` implementation for fast multi-profile "Deep Scans."
*   **Frontend:** Modern **Streamlit** dashboard with a clean, dark-mode responsive UI.

## 📦 Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/binance-copy-trading-intel.git
    cd binance-copy-trading-intel
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Launch the dashboard:**
    ```bash
    streamlit run app.py
    ```

## 🔍 Why BCTI?

While the standard Binance interface highlights top ROI, it often hides the risk of high-churn portfolios and sub-account leading. BCTI exposes these "Red Flags" by calculating churn rates and tracking trader balance stability, allowing you to invest your capital with data-backed confidence.

---

### Disclaimer
*This software is for educational and research purposes only. Trading involves significant risk. Always perform your own due diligence before investing.*
