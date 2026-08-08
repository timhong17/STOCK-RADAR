import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import time
import random

# 嘗試使用 curl_cffi 模擬瀏覽器指紋，可大幅降低被 Yahoo Finance 限流(429)的機率
# 若環境沒有安裝 curl_cffi，則自動退回使用 yfinance 預設的 requests session
try:
    from curl_cffi import requests as cffi_requests
    CURL_CFFI_AVAILABLE = True
except ImportError:
    CURL_CFFI_AVAILABLE = False

# ==========================================
# 頁面與樣式設定
# ==========================================
st.set_page_config(
    page_title="台美股智慧選股儀表板 Pro",
    page_icon="▲",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Inter:wght@400;500;600&display=swap');

    :root {
        --bg-0: #0A0E16;      /* 最底層背景 */
        --bg-1: #10141F;      /* 側邊欄 / 卡片背景 */
        --bg-2: #171C2B;      /* 次層卡片背景 */
        --line: #262C40;      /* 邊框線 */
        --text-hi: #E7E9F3;   /* 主要文字 */
        --text-lo: #7C8299;   /* 次要文字 */
        --accent: #6C8CFF;    /* 單一主色調（藍） */
        --accent-dim: #3D4E8F;/* 主色調的暗版，用於邊框/底色 */
        --accent-glow: rgba(108, 140, 255, 0.18);
    }

    /* 全域背景與文字 */
    .stApp {
        background: var(--bg-0);
        color: var(--text-hi);
        font-family: 'Inter', sans-serif;
    }

    /* 主標題 */
    .main-header {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.4rem;
        font-weight: 700;
        letter-spacing: -0.01em;
        color: var(--text-hi);
        margin-bottom: 0.4rem;
        padding-bottom: 0.6rem;
        border-bottom: 1px solid var(--line);
        position: relative;
    }
    .main-header::after {
        content: "";
        position: absolute;
        left: 0; bottom: -1px;
        width: 72px; height: 2px;
        background: var(--accent);
        box-shadow: 0 0 12px var(--accent-glow);
    }
    .sub-header {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        letter-spacing: 0.03em;
        color: var(--text-lo);
        margin-bottom: 2rem;
    }

    /* 側邊欄 */
    [data-testid="stSidebar"] {
        background: var(--bg-1);
        border-right: 1px solid var(--line);
    }
    [data-testid="stSidebar"] * {
        color: var(--text-hi);
    }
    [data-testid="stSidebar"] .stRadio label,
    [data-testid="stSidebar"] .stCheckbox label {
        color: var(--text-hi) !important;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        font-family: 'Space Grotesk', sans-serif;
        color: var(--text-hi);
    }
    [data-testid="stSidebar"] hr {
        border-color: var(--line);
    }

    /* 輸入元件（文字框 / 下拉選單） */
    .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
        background: var(--bg-2) !important;
        color: var(--text-hi) !important;
        border: 1px solid var(--line) !important;
    }

    /* 滑桿：改為單一主色調 */
    .stSlider [data-baseweb="slider"] div[role="slider"] {
        background-color: var(--accent) !important;
        border-color: var(--accent) !important;
    }
    .stSlider [data-baseweb="slider"] > div > div {
        background: var(--accent-dim) !important;
    }

    /* 主要按鈕：實心主色調，hover 微微發光 */
    .stButton > button[kind="primary"] {
        background: var(--accent);
        color: #0A0E16;
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 600;
        letter-spacing: 0.02em;
        border: none;
        border-radius: 6px;
        transition: box-shadow 0.2s ease, transform 0.15s ease;
    }
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 0 20px var(--accent-glow);
        transform: translateY(-1px);
    }

    /* Metric 卡片 */
    [data-testid="stMetric"] {
        background: var(--bg-1);
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 1rem 1.2rem;
    }
    [data-testid="stMetricLabel"] {
        color: var(--text-lo) !important;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem !important;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    [data-testid="stMetricValue"] {
        color: var(--text-hi) !important;
        font-family: 'Space Grotesk', sans-serif;
    }

    /* 資料表格 */
    [data-testid="stDataFrame"] {
        border: 1px solid var(--line);
        border-radius: 8px;
        overflow: hidden;
    }

    /* Expander（除錯面板等） */
    [data-testid="stExpander"] {
        background: var(--bg-1);
        border: 1px solid var(--line);
        border-radius: 8px;
    }

    /* 提示框：統一改為單一色調（不用預設的綠/黃/紅） */
    [data-testid="stAlert"] {
        background: var(--bg-2) !important;
        border: 1px solid var(--accent-dim) !important;
        border-left: 3px solid var(--accent) !important;
        border-radius: 6px;
        color: var(--text-hi) !important;
    }
    [data-testid="stAlert"] * {
        color: var(--text-hi) !important;
    }

    /* 一般標題文字 */
    h1, h2, h3, h4 {
        font-family: 'Space Grotesk', sans-serif;
        color: var(--text-hi);
    }

    /* 進度條 */
    .stProgress > div > div > div {
        background-color: var(--accent) !important;
    }

    /* 捲軸 */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: var(--bg-0); }
    ::-webkit-scrollbar-thumb { background: var(--line); border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--accent-dim); }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 側邊欄：篩選條件與參數控制
# ==========================================
st.sidebar.markdown("""
<svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-bottom: 0.4rem;">
    <polyline points="4,28 14,18 20,24 36,8" stroke="#6C8CFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
    <circle cx="36" cy="8" r="2.5" fill="#6C8CFF"/>
</svg>
""", unsafe_allow_html=True)
st.sidebar.title("選股策略參數")

# 市場選擇與觀察清單
market = st.sidebar.radio("目標市場", ["台股 (TW)", "美股 (US)"])

if market == "台股 (TW)":
    default_symbols = "2330.TW, 2317.TW, 2454.TW, 2308.TW, 2382.TW, 3231.TW, 2603.TW, 2881.TW, 2303.TW, 3037.TW"
else:
    default_symbols = "NVDA, AAPL, MSFT, GOOGL, AMZN, TSLA, META, AMD, INTC, QCOM, AVGO, SPY"

watchlist_input = st.sidebar.text_area(
    "觀察清單 (用逗號隔開)",
    value=default_symbols,
    height=100,
    help="台股請輸入代號加 .TW (例: 2330.TW)，美股直接輸入代號 (例: AAPL)"
)

st.sidebar.markdown("---")

# 基本面篩選條件（預設放寬）
st.sidebar.subheader("基本面條件")
enable_pe = st.sidebar.checkbox("啟用本益比 (P/E) 篩選", value=True)
min_pe = st.sidebar.slider("最低本益比下限", min_value=0.0, max_value=100.0, value=0.0, step=1.0)
max_pe = st.sidebar.slider("最高本益比上限", min_value=10.0, max_value=150.0, value=60.0, step=5.0)

enable_roe = st.sidebar.checkbox("啟用股東權益報酬率 (ROE) 篩選", value=True)
min_roe = st.sidebar.slider("最低 ROE (%) 下限", min_value=0.0, max_value=50.0, value=8.0, step=1.0)

enable_div = st.sidebar.checkbox("啟用殖利率 (Dividend Yield) 篩選", value=False)
min_div = st.sidebar.slider("最低殖利率 (%) 下限", min_value=0.0, max_value=10.0, value=2.5, step=0.5)

st.sidebar.markdown("---")

# 技術面與籌碼面條件
st.sidebar.subheader("技術面條件")
enable_trend = st.sidebar.checkbox("多頭排列 (股價 > 月線20MA)", value=True)

enable_volume = st.sidebar.checkbox("今日成交量爆量", value=False) # 預設關閉以提升初次搜尋成功率
vol_multiplier = st.sidebar.slider("爆量倍數 (相較 5日均量)", min_value=1.0, max_value=3.0, value=1.1, step=0.1)

enable_rsi = st.sidebar.checkbox("RSI 強勢區間 (14日)", value=False)
rsi_range = st.sidebar.slider("RSI 允許範圍", min_value=30, max_value=90, value=(45, 80))

# ==========================================
# 資料抓取輔助函數（含重試 / 限流退避 / 除錯訊息）
# ==========================================
@st.cache_resource(show_spinner=False)
def get_yf_session():
    """建立一個模擬瀏覽器指紋的 session，重複使用可減少被 Yahoo 判定為爬蟲的機率"""
    if CURL_CFFI_AVAILABLE:
        try:
            return cffi_requests.Session(impersonate="chrome")
        except Exception:
            return None
    return None


def fetch_ticker_data(symbol, max_retries=3, base_delay=2.0):
    """
    抓取單一股票的歷史資料與基本面資訊。
    - 遇到 429 / 限流錯誤時，會等待後自動重試（指數退避 + 隨機抖動）
    - 任何失敗都會回傳詳細錯誤原因，而不是靜默吞掉
    回傳: (df, info, error_message)  成功時 error_message 為 None
    """
    session = get_yf_session()
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            ticker = yf.Ticker(symbol, session=session) if session else yf.Ticker(symbol)
            # 注意：yfinance 合法的 period 只有 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
            # 原本的 "8m" 並非合法值，容易導致抓取失敗或回傳空資料，這裡改用 "1y" 確保足夠算 60MA
            df = ticker.history(period="1y")

            if df.empty:
                last_error = "history() 回傳空資料（可能代號錯誤，或被限流回傳空結果）"
                raise ValueError(last_error)

            try:
                info = ticker.info
            except Exception as info_err:
                # info 端點特別容易失敗，抓不到就給空 dict，但仍記錄原因供除錯
                info = {}
                last_error = f"info 抓取失敗（不影響股價，僅本益比/ROE等基本面資料缺失）：{info_err}"

            return df, info, None

        except Exception as e:
            err_text = str(e)
            last_error = err_text
            is_rate_limited = (
                "429" in err_text
                or "Too Many Requests" in err_text
                or "Rate limited" in err_text
                or "rate limit" in err_text.lower()
            )

            if attempt < max_retries and is_rate_limited:
                # 指數退避 + 隨機抖動，避免同時大量重試又觸發限流
                wait_time = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 1.5)
                time.sleep(wait_time)
                continue
            elif attempt < max_retries:
                # 非限流錯誤，短暫等待後仍可重試一次（例如暫時性網路問題）
                time.sleep(base_delay)
                continue
            else:
                break

    return None, None, last_error


# ==========================================
# 輔助計算函數
# ==========================================
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def build_candlestick_chart(df, symbol_name):
    """繪製 Plotly 互動式圖表（深色單一色調風格，與頁面主題一致）"""
    # 與頁面 CSS 共用的色票
    BG = "#10141F"
    GRID = "#262C40"
    TEXT = "#E7E9F3"
    TEXT_MUTED = "#7C8299"
    ACCENT = "#6C8CFF"        # 主色調
    ACCENT_SOFT = "#9DB2FF"   # 主色調的亮版，用於次要線條
    UP = "#EF4444"    # 台股慣例：紅漲綠跌（保留漲跌功能性顏色，不併入單一色調）
    DOWN = "#22C55E"

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.6, 0.2, 0.2],
        subplot_titles=(f"{symbol_name} 股價與均線趨勢", "成交量", "RSI (14)")
    )

    # 1. K線圖
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'],
        name='K線',
        increasing_line_color=UP,
        decreasing_line_color=DOWN
    ), row=1, col=1)

    # 均線（同一主色調的深淺兩階，取代原本的橘/藍雙色）
    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name='月線 (20MA)', line=dict(color=ACCENT_SOFT, width=1.5)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA60'], name='季線 (60MA)', line=dict(color=ACCENT, width=1.5)), row=1, col=1)

    # 2. 成交量圖
    colors = [UP if c >= o else DOWN for c, o in zip(df['Close'], df['Open'])]
    fig.add_trace(go.Bar(
        x=df.index, y=df['Volume'],
        name='成交量',
        marker_color=colors,
        showlegend=False
    ), row=2, col=1)

    # 3. RSI 圖（改用主色調）
    fig.add_trace(go.Scatter(
        x=df.index, y=df['RSI'],
        name='RSI(14)',
        line=dict(color=ACCENT, width=1.5)
    ), row=3, col=1)

    fig.add_hline(y=70, line_dash="dash", line_color=TEXT_MUTED, row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color=TEXT_MUTED, row=3, col=1)

    fig.update_layout(
        height=650,
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        font=dict(color=TEXT, family="Inter, sans-serif"),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=20, r=20, t=40, b=20)
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID)
    return fig


# ==========================================
# 主頁面內容區塊
# ==========================================
st.markdown('<div class="main-header">STOCK RADAR</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">透過靈活的基本面與技術面條件，即時篩選與分析優質標的</div>', unsafe_allow_html=True)

# 執行選股按鈕
if st.button("開始掃描篩選股票", type="primary", use_container_width=True):
    symbols_list = [s.strip().upper() for s in watchlist_input.split(",") if s.strip()]
    
    if not symbols_list:
        st.warning("請在側邊欄輸入有效的股票代號清單！")
    else:
        results = []
        chart_data_store = {}
        debug_logs = []  # 收集每檔股票的處理結果，供下方除錯區塊顯示

        progress_bar = st.progress(0)
        status_text = st.empty()

        for idx, symbol in enumerate(symbols_list):
            status_text.text(f"正在分析 [{symbol}] ({idx + 1}/{len(symbols_list)})...")
            progress_bar.progress((idx + 1) / len(symbols_list))

            # 每檔股票之間加入小延遲，降低短時間內大量請求觸發 Yahoo 限流的機率
            if idx > 0:
                time.sleep(0.8 + random.uniform(0, 0.6))

            try:
                df, info, fetch_error = fetch_ticker_data(symbol)

                if df is None:
                    debug_logs.append(f"[FAIL] [{symbol}] 抓取失敗：{fetch_error}")
                    continue

                if len(df) < 20:
                    debug_logs.append(f"[WARN] [{symbol}] 資料筆數不足 20 筆（僅 {len(df)} 筆），略過")
                    continue

                if fetch_error:
                    # df 有拿到，但 info 抓取有問題，記錄下來但不中斷流程
                    debug_logs.append(f"[WARN] [{symbol}] {fetch_error}")
                else:
                    debug_logs.append(f"[OK] [{symbol}] 資料抓取成功")

                # 指標計算
                df['MA20'] = df['Close'].rolling(window=20).mean()
                df['MA60'] = df['Close'].rolling(window=60).mean()
                df['RSI'] = calculate_rsi(df['Close'])
                
                vol_5d_avg = df['Volume'].tail(5).mean()
                vol_today = df['Volume'].iloc[-1]
                current_price = df['Close'].iloc[-1]
                current_rsi = df['RSI'].iloc[-1] if not pd.isna(df['RSI'].iloc[-1]) else 50.0

                # 基本面數據提取
                pe_ratio = info.get('trailingPE', None)
                roe = info.get('returnOnEquity', None)
                if roe is not None:
                    roe = roe * 100
                
                div_yield = info.get('dividendYield', None)
                if div_yield is not None:
                    div_yield = div_yield * 100

                # 條件判斷邏輯
                passed = True

                # 若數據存在才篩選，若數據缺失不直接淘汰
                if enable_pe and pe_ratio is not None:
                    if pe_ratio > max_pe or pe_ratio < min_pe or pe_ratio <= 0:
                        passed = False

                if enable_roe and roe is not None and passed:
                    if roe < min_roe:
                        passed = False

                if enable_div and div_yield is not None and passed:
                    if div_yield < min_div:
                        passed = False

                if enable_trend and passed:
                    ma20_val = df['MA20'].iloc[-1]
                    if pd.isna(ma20_val) or current_price < ma20_val:
                        passed = False

                if enable_volume and passed:
                    if vol_5d_avg == 0 or vol_today < (vol_5d_avg * vol_multiplier):
                        passed = False

                if enable_rsi and passed:
                    if current_rsi < rsi_range[0] or current_rsi > rsi_range[1]:
                        passed = False

                # 儲存符合結果
                if passed:
                    stock_name = info.get('shortName', symbol)
                    results.append({
                        '股票代號': symbol,
                        '公司名稱': stock_name,
                        '現價': round(current_price, 2),
                        '本益比 (PE)': round(pe_ratio, 2) if pe_ratio else 'N/A',
                        'ROE (%)': round(roe, 2) if roe else 'N/A',
                        '殖利率 (%)': round(div_yield, 2) if div_yield else 'N/A',
                        'RSI (14)': round(current_rsi, 1),
                        '成交量爆量倍數': round(vol_today / vol_5d_avg, 2) if vol_5d_avg and vol_5d_avg > 0 else 1.0
                    })
                    chart_data_store[symbol] = (df, stock_name)

            except Exception as e:
                debug_logs.append(f"[FAIL] [{symbol}] 處理時發生例外：{e}")
                continue

        progress_bar.empty()
        status_text.empty()

        st.session_state['results_df'] = pd.DataFrame(results)
        st.session_state['chart_data'] = chart_data_store
        st.session_state['debug_logs'] = debug_logs

# ==========================================
# 篩選結果呈現區塊
# ==========================================
if 'results_df' in st.session_state:
    results_df = st.session_state['results_df']
    chart_data = st.session_state['chart_data']
    debug_logs = st.session_state.get('debug_logs', [])

    # 除錯面板：顯示每檔股票的抓取結果，方便判斷是限流、代號錯誤還是條件不符
    if debug_logs:
        fail_count = sum(1 for log in debug_logs if log.startswith("[FAIL]"))
        with st.expander(f"抓取除錯紀錄（共 {len(debug_logs)} 檔，{fail_count} 檔失敗）", expanded=(fail_count > 0)):
            for log in debug_logs:
                st.text(log)
            if fail_count > 0:
                st.caption(
                    "若大量出現 429 / Too Many Requests / Rate limited，代表被 Yahoo Finance 限流，"
                    "建議：減少觀察清單股數、稍後再試，或降低使用頻率。"
                )

    if not results_df.empty:
        st.success(f"篩選完成，共找到 {len(results_df)} 檔符合策略條件的股票。")

        # 頂部數據看板
        col1, col2, col3 = st.columns(3)
        col1.metric("符合條件股票數", f"{len(results_df)} 檔")
        
        roe_numeric = pd.to_numeric(results_df['ROE (%)'], errors='coerce')
        avg_roe = roe_numeric.mean() if not roe_numeric.isna().all() else 0
        col2.metric("平均 ROE", f"{avg_roe:.1f}%")
        
        col3.metric("最高成交量倍數", f"{results_df['成交量爆量倍數'].max():.2f} 倍")

        # 顯示資料表格
        st.subheader("符合條件之股票清單")
        st.dataframe(
            results_df,
            use_container_width=True,
            hide_index=True
        )

        st.markdown("---")

        # 互動式圖表檢視器
        st.subheader("個股技術分析互動圖表")
        selected_symbol = st.selectbox(
            "請選擇要查看詳細 K 線圖與指標的股票：",
            results_df['股票代號'].tolist()
        )

        if selected_symbol in chart_data:
            df_selected, name_selected = chart_data[selected_symbol]
            fig = build_candlestick_chart(df_selected, f"{selected_symbol} ({name_selected})")
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("沒有股票符合目前的篩選條件，請嘗試在側邊欄放寬條件（例如調高本益比上限、調低 ROE 或取消勾選爆量要求）。")