import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import time
import random
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import json

# 嘗試使用 curl_cffi 模擬瀏覽器指紋，降低被 Yahoo Finance 限流(429)的機率
try:
    from curl_cffi import requests as cffi_requests
    CURL_CFFI_AVAILABLE = True
except ImportError:
    CURL_CFFI_AVAILABLE = False

# ==========================================
# 常用台股中文名稱對照表
# ==========================================
TW_STOCK_NAMES = {
    "2330.TW": "台積電",
    "2317.TW": "鴻海",
    "2454.TW": "聯發科",
    "2308.TW": "台達電",
    "2382.TW": "廣達",
    "3231.TW": "緯創",
    "2603.TW": "長榮",
    "2881.TW": "富邦金",
    "2882.TW": "國泰金",
    "2303.TW": "聯電",
    "3037.TW": "欣興",
    "2357.TW": "華碩",
    "2376.TW": "技嘉",
    "2377.TW": "微星",
    "6669.TW": "緯穎",
    "3661.TW": "世芯-KY",
    "3443.TW": "創意",
    "3008.TW": "大立光",
    "2327.TW": "國巨",
    "2609.TW": "陽明",
    "2615.TW": "萬海",
    "2002.TW": "中鋼",
    "1301.TW": "台塑",
    "1303.TW": "南亞",
    "2412.TW": "中華電",
    "3034.TW": "聯詠",
    "3711.TW": "日月光投控"
}

def get_chinese_stock_name(symbol, raw_info_name):
    if symbol in TW_STOCK_NAMES:
        return TW_STOCK_NAMES[symbol]
    
    if symbol.endswith(".TW") or symbol.endswith(".TWO"):
        code = symbol.split(".")[0]
        return f"台股 {code}"
    
    return raw_info_name if raw_info_name else symbol

# ==========================================
# 頁面與高閱讀性典雅字體設定 (Platinum Elegance Design)
# ==========================================
st.set_page_config(
    page_title="台美股智慧選股儀表板 Pro",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* 引入高閱讀性兼具典雅筆畫的字體庫 */
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700&family=Prata&family=Noto+Sans+TC:wght@300;400;500;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    :root {
        --bg-0: #050505;        /* 極致深黑主畫面底色 */
        --bg-1: #0A0D14;        /* 側邊欄深邃星空底色 */
        --bg-2: #121722;        /* 側邊欄控制元件背景 */
        --line: #212836;        /* 星空暗灰邊框 */
        --line-bright: #8A99AD; /* 亮銀星光邊框 */
        --text-hi: #F0F6FC;     /* 白金高亮字 */
        --text-lo: #8A99AD;     /* 沉靜灰字 */
        
        /* 銀灰星空色系 (Platinum Starlight) */
        --starlight-white: #FFFFFF;
        --starlight-silver: #D5E0EA;
        --starlight-dim: #708090;
        --starlight-grad: linear-gradient(135deg, #FFFFFF 0%, #B0C4DE 50%, #708090 100%);
        --starlight-grad-soft: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(176, 196, 222, 0.03) 100%);
        --starlight-glow: rgba(220, 230, 242, 0.35);
    }

    /* -----------------------------------------------------------
       1. 深度解決鍵盤字體破圖 (keyboard_double...)
       ----------------------------------------------------------- */
    [data-testid="stSidebarCollapseButton"] button,
    [data-testid="stSidebarCollapseButton"] button *,
    [data-testid="stSidebarCollapseButton"] span,
    [data-testid="stSidebarCollapseButton"] i,
    [data-testid="stSidebarHeader"] * {
        font-size: 0px !important;
        line-height: 0 !important;
        visibility: hidden !important;
    }
    [data-testid="stSidebarCollapseButton"] button {
        visibility: visible !important;
        position: relative !important;
        width: 32px !important;
        height: 32px !important;
        background: transparent !important;
        border: none !important;
    }
    [data-testid="stSidebarCollapseButton"] button::before {
        content: "◀" !important;
        visibility: visible !important;
        font-size: 14px !important;
        color: #B0C4DE !important;
        position: absolute !important;
        left: 8px !important;
        top: 6px !important;
    }

    /* 全域背景與文字 */
    .stApp {
        background: var(--bg-0);
        color: var(--text-hi);
        font-family: 'Noto Sans TC', -apple-system, sans-serif;
        font-size: 1rem;
        line-height: 1.6;
        letter-spacing: 0.015em;
    }

    /* 頂部主標題 */
    .main-header {
        font-family: 'Cinzel', 'Prata', serif;
        font-size: 2.6rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        background: var(--starlight-grad);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.4rem;
        padding-bottom: 0.6rem;
        border-bottom: 1px solid var(--line);
        position: relative;
    }
    .main-header::after {
        content: "";
        position: absolute;
        left: 0; bottom: -1px;
        width: 120px; height: 2px;
        background: var(--starlight-grad);
        box-shadow: 0 0 15px var(--starlight-glow);
    }
    .sub-header {
        font-family: 'Prata', 'Noto Sans TC', serif;
        font-size: 1.05rem;
        color: var(--starlight-silver);
        opacity: 0.85;
        margin-bottom: 2.2rem;
    }

    /* ==========================================
       側邊欄 (Sidebar) 銀灰星空與控制拉桿修飾
       ========================================== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0A0D14 0%, #06080E 100%) !important;
        border-right: 1px solid var(--line) !important;
    }
    [data-testid="stSidebar"] * {
        color: var(--text-hi) !important;
        font-family: 'Noto Sans TC', sans-serif;
    }
    
    /* 側邊欄標題 */
    section[data-testid="stSidebar"] h1 {
        font-family: 'Prata', serif !important;
        font-size: 1.35rem !important;
        background: var(--starlight-grad);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        letter-spacing: 0.05em;
        margin-bottom: 1rem;
    }
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        font-family: 'Prata', serif !important;
        font-size: 1.05rem !important;
        color: var(--starlight-silver) !important;
        font-weight: 600;
        margin-top: 1rem;
    }
    [data-testid="stSidebar"] hr {
        border-color: var(--line) !important;
    }

    /* 側邊欄輸入框與文字區域 */
    [data-testid="stSidebar"] .stTextArea textarea, 
    [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {
        background: var(--bg-2) !important;
        color: var(--starlight-white) !important;
        border: 1px solid var(--line) !important;
        border-radius: 6px;
        font-family: 'JetBrains Mono', monospace;
        transition: all 0.3s ease;
    }
    [data-testid="stSidebar"] .stTextArea textarea:focus, 
    [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div:focus {
        border-color: var(--line-bright) !important;
        box-shadow: 0 0 12px var(--starlight-glow) !important;
    }

    /* -----------------------------------------------------------
       1.5 覆寫 Streamlit 主題色變數 (--primary-color)
       Streamlit 內建元件（含 Slider）大量使用此變數作為強調色，
       直接覆寫可避免殘留的預設紅色 (#FF4B4B) 在部分節點露出。
       建議同時搭配 .streamlit/config.toml 設定 primaryColor。
       ----------------------------------------------------------- */
    :root, .stApp, [data-testid="stSidebar"] {
        --primary-color: #9AA6B2 !important;
    }

    /* -----------------------------------------------------------
       2. 強效覆寫紅色！Radio / Checkbox 改為銀灰色
       ----------------------------------------------------------- */
    [data-testid="stSidebar"] [data-baseweb="radio"] label,
    [data-testid="stSidebar"] [data-baseweb="checkbox"] label {
        color: var(--starlight-silver) !important;
        font-size: 0.95rem;
    }
    
    [data-testid="stSidebar"] input[type="checkbox"]:checked + div,
    [data-testid="stSidebar"] input[type="radio"]:checked + div,
    [data-testid="stSidebar"] div[data-baseweb="checkbox"] div[aria-checked="true"],
    [data-testid="stSidebar"] div[data-baseweb="radio"] div[aria-checked="true"] {
        background-color: #B0C4DE !important;
        border-color: #FFFFFF !important;
    }

    /* -----------------------------------------------------------
       3. Slider：銀灰金屬漸層拉桿
       ----------------------------------------------------------- */
    /* 整條 slider 元件的背景 */
    [data-testid="stSidebar"] [data-baseweb="slider"] {
        --slider-silver-light: #FFFFFF;
        --slider-silver-mid: #C7D0D9;
        --slider-silver: #9AA6B2;
        --slider-silver-dark: #66727E;
        --slider-track: rgba(180, 192, 204, 0.20);
    }

    /* 已選取區段：亮銀 → 銀灰 */
    [data-testid="stSidebar"] [data-baseweb="slider"] > div > div > div {
        background: linear-gradient(
            90deg,
            #66727E 0%,
            #9AA6B2 48%,
            #E5E9ED 100%
        ) !important;
        background-image: linear-gradient(
            90deg,
            #66727E 0%,
            #9AA6B2 48%,
            #E5E9ED 100%
        ) !important;
        border-radius: 999px !important;
    }

    /* 未選取軌道 */
    [data-testid="stSidebar"] [data-baseweb="slider"] > div > div {
        background: linear-gradient(
            90deg,
            rgba(255,255,255,0.10),
            rgba(154,166,178,0.22)
        ) !important;
        border-radius: 999px !important;
    }

    /* 滑桿圓鈕：銀灰金屬漸層 */
    [data-testid="stSidebar"] [data-baseweb="slider"] div[role="slider"] {
        background: linear-gradient(
            145deg,
            #FFFFFF 0%,
            #D8DEE4 35%,
            #A5AFB9 68%,
            #687580 100%
        ) !important;
        background-image: linear-gradient(
            145deg,
            #FFFFFF 0%,
            #D8DEE4 35%,
            #A5AFB9 68%,
            #687580 100%
        ) !important;
        border: 1px solid #FFFFFF !important;
        box-shadow:
            0 0 0 1px rgba(120,132,144,0.55),
            0 0 12px rgba(213,224,234,0.42),
            inset 1px 1px 2px rgba(255,255,255,0.85) !important;
    }

    /* Slider 數值與刻度文字 */
    [data-testid="stSidebar"] .stSlider [data-testid="stWidgetLabel"],
    [data-testid="stSidebar"] .stSlider [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] .stSlider span {
        color: #D5DCE3 !important;
    }

    /* Slider tooltip */
    [data-testid="stSidebar"] [data-baseweb="slider"] div[data-testid="stSliderValue"] {
        color: #FFFFFF !important;
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* 最終強制覆寫：BaseWeb Slider 實際結構 */
    [data-testid="stSidebar"] .stSlider [data-baseweb="slider"] [role="slider"] {
        background: linear-gradient(145deg, #FFFFFF 0%, #D9DEE3 28%, #A6B0BA 62%, #687580 100%) !important;
        background-image: linear-gradient(145deg, #FFFFFF 0%, #D9DEE3 28%, #A6B0BA 62%, #687580 100%) !important;
        border: 2px solid #F5F7F9 !important;
        border-radius: 50% !important;
        box-shadow: 0 0 0 1px #7B8792, 0 0 14px rgba(220,230,240,.55), inset 1px 1px 2px rgba(255,255,255,.9) !important;
    }

    [data-testid="stSidebar"] .stSlider [data-baseweb="slider"] > div > div {
        background: #3B4651 !important;
        border-radius: 999px !important;
    }

    [data-testid="stSidebar"] .stSlider [data-baseweb="slider"] > div > div > div {
        background: linear-gradient(90deg, #6B7782 0%, #AEB8C1 48%, #F0F2F4 100%) !important;
        background-image: linear-gradient(90deg, #6B7782 0%, #AEB8C1 48%, #F0F2F4 100%) !important;
        border-radius: 999px !important;
    }

    /* 拖曳/聚焦時彈出的數值氣泡（新版 Streamlit 結構）與 focus 光暈 */
    [data-testid="stSidebar"] [data-testid="stThumbValue"],
    [data-testid="stSidebar"] [data-baseweb="slider"] [role="slider"] [data-testid="stTickBar"] {
        color: #F0F2F4 !important;
        background: #3B4651 !important;
    }
    [data-testid="stSidebar"] [data-baseweb="slider"] [role="slider"]:focus,
    [data-testid="stSidebar"] [data-baseweb="slider"] [role="slider"]:focus-visible {
        box-shadow: 0 0 0 6px rgba(213, 224, 234, 0.28) !important;
        outline: none !important;
    }

    /* 主要按鈕 */
    .stButton > button[kind="primary"] {
        background: var(--starlight-grad);
        color: #050505;
        font-family: 'Prata', 'Noto Sans TC', serif;
        font-size: 1.05rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        border: none;
        border-radius: 6px;
        padding: 0.6rem 1.5rem;
        transition: all 0.35s ease;
        box-shadow: 0 4px 15px rgba(255, 255, 255, 0.15);
    }
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 0 25px var(--starlight-glow);
        transform: translateY(-2px);
        color: #000;
    }

    /* 數據看板 Metric */
    [data-testid="stMetric"] {
        background: var(--starlight-grad-soft);
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 1.2rem 1.4rem;
        transition: all 0.3s ease;
    }
    [data-testid="stMetric"]:hover {
        border-color: var(--line-bright);
        box-shadow: 0 0 15px var(--starlight-glow);
    }
    [data-testid="stMetricLabel"] {
        color: var(--text-lo) !important;
        font-family: 'Prata', sans-serif;
        font-size: 0.85rem !important;
        letter-spacing: 0.05em;
    }
    [data-testid="stMetricValue"] {
        background: var(--starlight-grad);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        font-size: 1.9rem !important;
    }

    /* 資料表格 */
    [data-testid="stDataFrame"] {
        border: 1px solid var(--line);
        border-radius: 8px;
        overflow: hidden;
        font-family: 'JetBrains Mono', 'Noto Sans TC', sans-serif;
    }

    /* 新聞卡片標題 */
    .news-card {
        background: var(--bg-1);
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 1rem;
        transition: all 0.35s ease;
    }
    .news-card:hover {
        border-color: var(--line-bright);
        box-shadow: 0 0 15px var(--starlight-glow);
        transform: translateY(-1px);
    }
    .news-title {
        font-family: 'Noto Sans TC', sans-serif;
        font-size: 1.05rem;
        font-weight: 500;
        color: var(--text-hi);
        text-decoration: none;
        margin-bottom: 0.5rem;
        display: block;
        line-height: 1.5;
    }
    .news-title:hover {
        color: var(--starlight-silver);
    }
    .news-meta {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
        color: var(--text-lo);
    }

    /* 資訊卡片 */
    .info-card {
        background: var(--starlight-grad-soft);
        border: 1px solid var(--line);
        border-left: 4px solid var(--starlight-silver);
        padding: 1.4rem;
        border-radius: 6px;
        margin-bottom: 1.2rem;
    }
    .info-title {
        font-family: 'Prata', 'Noto Sans TC', serif;
        font-weight: 700;
        font-size: 1.2rem;
        letter-spacing: 0.04em;
        background: var(--starlight-grad);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.6rem;
    }

    /* Tab 頁籤 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        border-bottom: 1px solid var(--line);
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'Noto Sans TC', sans-serif;
        font-size: 0.95rem;
        color: var(--text-lo);
        padding: 10px 20px;
        border-radius: 6px 6px 0 0;
        transition: all 0.2s ease;
    }
    .stTabs [aria-selected="true"] {
        color: var(--starlight-white) !important;
        border-bottom: 2px solid var(--starlight-white) !important;
        background: rgba(255, 255, 255, 0.05) !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 側邊欄：量化策略與銀灰星空參數配置
# ==========================================
st.sidebar.title("策略模型與量化參數配置")

market = st.sidebar.radio("交易市場選擇 (Target Market)", ["台股 (TW)", "美股 (US)"])

if market == "台股 (TW)":
    default_symbols = "2330.TW, 2317.TW, 2454.TW, 2308.TW, 2382.TW, 3231.TW, 2603.TW"
else:
    default_symbols = "NVDA, PLTR, AAPL, MSFT, GOOGL, AMZN, TSLA, META, AMD, AVGO"

watchlist_input = st.sidebar.text_area(
    "池內標的觀察清單 (Ticker Pool)",
    value=default_symbols,
    height=100,
    help="請輸入代號以逗號分隔",
    key=f"watchlist_{market}"
)

st.sidebar.markdown("---")
st.sidebar.subheader("基本面因子篩選 (Fundamental Factors)")
enable_pe = st.sidebar.checkbox("啟用本益比 (P/E Ratio) 門檻", value=True)
min_pe = st.sidebar.slider("本益比下限 (Lower Bound)", 0.0, 100.0, 0.0, 1.0)
max_pe = st.sidebar.slider("本益比上限 (Upper Bound)", 10.0, 200.0, 80.0, 5.0)

enable_roe = st.sidebar.checkbox("啟用股東權益報酬率 (ROE) 門檻", value=True)
min_roe = st.sidebar.slider("最低 ROE 門檻 (%)", 0.0, 50.0, 8.0, 1.0)

st.sidebar.markdown("---")
st.sidebar.subheader("籌碼流向與資本支出 (Smart Money & CapEx)")
enable_inst_hold = st.sidebar.checkbox("法人/機構持股比例 > 30%", value=False)
enable_capex_growth = st.sidebar.checkbox("CapEx (資本支出) 年增 > 0%", value=False)

st.sidebar.markdown("---")
st.sidebar.subheader("技術動能與量能指標 (Technical & Momentum Filters)")
enable_trend = st.sidebar.checkbox("均線多頭排列 (Close > 20MA)", value=True)
enable_volume = st.sidebar.checkbox("量能突破 (Volume Spikes vs 5MA)", value=False)
vol_multiplier = st.sidebar.slider("爆量倍數 (Volume Multiplier)", 1.0, 3.0, 1.1, 0.1)

# ==========================================
# 中文新聞抓取（Google News RSS 繁體中文）
# ==========================================
@st.cache_data(ttl=600, show_spinner=False)
def fetch_chinese_news(symbol, company_name=""):
    clean_code = symbol.split('.')[0]
    search_query = f"{clean_code} {company_name}".strip() if company_name else clean_code
    encoded_query = urllib.parse.quote(search_query)

    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"

    news_list = []
    try:
        req = urllib.request.Request(
            rss_url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            xml_data = response.read()

        root = ET.fromstring(xml_data)

        for item in root.findall('.//item'):
            title = item.find('title').text if item.find('title') is not None else "無標題"
            link = item.find('link').text if item.find('link') is not None else "#"
            pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""

            source_elem = item.find('source')
            source_name = source_elem.text if source_elem is not None else "中文財經媒體"

            if " - " in title:
                title_parts = title.rsplit(" - ", 1)
                title = title_parts[0]
                if source_name == "中文財經媒體":
                    source_name = title_parts[1]

            time_str = "最新"
            if pub_date:
                try:
                    dt = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %Z')
                    time_str = dt.strftime('%Y-%m-%d %H:%M')
                except Exception:
                    time_str = pub_date[:16]

            news_list.append({
                'title': title,
                'link': link,
                'publisher': source_name,
                'pubDate': time_str
            })

    except Exception:
        pass

    return news_list

# ==========================================
# 繁體中文法說會/公司簡介翻譯輔助函數
# ==========================================
def _translate_via_google(text):
    """透過 Google Translate 免費端點翻譯（無官方 API 金鑰）。"""
    url = (
        "https://translate.googleapis.com/translate_a/single"
        f"?client=gtx&sl=auto&tl=zh-TW&dt=t&q={urllib.parse.quote(text)}"
    )
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=6) as response:
        payload = json.loads(response.read().decode('utf-8'))
        segments = payload[0]
        translated = "".join(seg[0] for seg in segments if seg and seg[0])
        return translated.strip()


def _translate_via_mymemory(text):
    """備援翻譯端點：MyMemory（單次請求長度有限，超長文字會先截斷）。"""
    snippet = text[:490]
    url = (
        "https://api.mymemory.translated.net/get"
        f"?q={urllib.parse.quote(snippet)}&langpair=en|zh-TW"
    )
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=6) as response:
        payload = json.loads(response.read().decode('utf-8'))
        translated = payload.get('responseData', {}).get('translatedText', '')
        return translated.strip()


def translate_summary_to_zh(text):
    if not text or text == '暫無法說會文本說明。':
        return "目前尚無詳細的法說會重點或公司經營摘要資訊。"

    # 依序嘗試多個翻譯來源，確保最終呈現的內容為繁體中文
    for translator in (_translate_via_google, _translate_via_mymemory):
        try:
            translated = translator(text)
            if translated:
                return translated
        except Exception:
            continue

    # 所有翻譯來源皆失敗時，仍以繁體中文提示告知使用者，不再顯示原文英文內容
    return "【翻譯服務暫時無法連線】\n目前無法即時取得繁體中文版法說會重點摘要，請稍後重新整理頁面再試一次。"

# ==========================================
# 資料抓取與解析輔助函數
# ==========================================
@st.cache_resource(show_spinner=False)
def get_yf_session():
    if CURL_CFFI_AVAILABLE:
        try:
            return cffi_requests.Session(impersonate="chrome")
        except Exception:
            return None
    return None

def fetch_ticker_data(symbol, max_retries=3, base_delay=1.5):
    session = get_yf_session()
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            ticker = yf.Ticker(symbol, session=session) if session else yf.Ticker(symbol)
            df = ticker.history(period="1y")

            if df.empty:
                last_error = "history() 回傳空資料"
                raise ValueError(last_error)

            try:
                info = ticker.info
            except Exception as info_err:
                info = {}
                last_error = f"info 抓取失敗: {info_err}"

            holders = {}
            try:
                holders['major'] = ticker.major_holders
                holders['institutional'] = ticker.institutional_holders
            except Exception:
                holders['major'] = None
                holders['institutional'] = None

            cashflow = pd.DataFrame()
            try:
                cashflow = ticker.quarterly_cashflow
                if cashflow.empty:
                    cashflow = ticker.cashflow
            except Exception:
                pass

            calendar = None
            try:
                calendar = ticker.calendar
            except Exception:
                pass

            raw_name = info.get('shortName', symbol)
            chinese_name = get_chinese_stock_name(symbol, raw_name)
            news = fetch_chinese_news(symbol, chinese_name)

            return df, info, holders, cashflow, calendar, news, chinese_name, None

        except Exception as e:
            err_text = str(e)
            last_error = err_text
            if attempt < max_retries:
                time.sleep(base_delay * attempt)
                continue

    return None, None, None, None, None, None, symbol, last_error

def extract_capex_data(cashflow_df):
    if cashflow_df is None or cashflow_df.empty:
        return None, 0.0, []

    capex_row = None
    possible_keys = ['Capital Expenditure', 'Capital Expenditures', 'Net PPE Purchase And Sale']
    
    for key in possible_keys:
        if key in cashflow_df.index:
            capex_row = cashflow_df.loc[key]
            break

    if capex_row is None or capex_row.dropna().empty:
        return None, 0.0, []

    capex_series = capex_row.dropna().abs()
    latest_capex = capex_series.iloc[0]
    
    capex_growth = 0.0
    if len(capex_series) >= 2 and capex_series.iloc[1] > 0:
        capex_growth = ((capex_series.iloc[0] - capex_series.iloc[1]) / capex_series.iloc[1]) * 100

    trend = [{"Date": str(date.date()), "CapEx": val} for date, val in capex_series.head(4).items()]
    return latest_capex, capex_growth, trend

def extract_institutional_flow(info, holders):
    inst_percent = info.get('heldPercentInstitutions', None)
    insider_percent = info.get('heldPercentInsiders', None)

    if inst_percent is not None:
        inst_percent = inst_percent * 100
    if insider_percent is not None:
        insider_percent = insider_percent * 100

    top_holders_df = pd.DataFrame()
    if holders and isinstance(holders.get('institutional'), pd.DataFrame):
        top_holders_df = holders['institutional'].head(5)

    return inst_percent, insider_percent, top_holders_df

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def format_market_cap(val):
    if not val or pd.isna(val):
        return "N/A"
    if val >= 1e12:
        return f"${val/1e12:.2f} T"
    elif val >= 1e9:
        return f"${val/1e9:.2f} B"
    elif val >= 1e6:
        return f"${val/1e6:.2f} M"
    return f"${val:,.0f}"

def render_news_list(news_items, max_items=6):
    if not news_items:
        st.info("暫無相關繁體中文即時新聞。")
        return

    for item in news_items[:max_items]:
        title = item.get('title', '無標題新聞')
        publisher = item.get('publisher', '中文新聞源')
        link = item.get('link', '#')
        time_str = item.get('pubDate', '最新')

        st.markdown(f"""
        <div class="news-card">
            <a class="news-title" href="{link}" target="_blank">{title}</a>
            <div class="news-meta">來源: {publisher} | 發布時間: {time_str}</div>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# 黑白金屬風格繪圖函數
# ==========================================
def build_candlestick_chart(df, symbol_name):
    BG = "#0E1117"
    GRID = "rgba(255, 255, 255, 0.08)"
    TEXT = "#F0F6FC"
    TEXT_MUTED = "#8A99AD"
    SILVER_PRIMARY = "#B0C4DE"
    SILVER_LIGHT = "#FFFFFF"
    UP = "#EF4444"
    DOWN = "#22C55E"

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.6, 0.2, 0.2],
        subplot_titles=(f"{symbol_name} 股價與 K 線走勢", "成交量", "RSI (14)")
    )

    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        name='K線', increasing_line_color=UP, decreasing_line_color=DOWN
    ), row=1, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name='月線 (20MA)', line=dict(color=SILVER_LIGHT, width=1.5)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA60'], name='季線 (60MA)', line=dict(color=SILVER_PRIMARY, width=1.5)), row=1, col=1)

    colors = [UP if c >= o else DOWN for c, o in zip(df['Close'], df['Open'])]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='成交量', marker_color=colors, showlegend=False), row=2, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI(14)', line=dict(color=SILVER_PRIMARY, width=1.5)), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color=TEXT_MUTED, row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color=TEXT_MUTED, row=3, col=1)

    fig.update_layout(
        height=600, xaxis_rangeslider_visible=False, template="plotly_dark",
        paper_bgcolor=BG, plot_bgcolor=BG, font=dict(color=TEXT, family="JetBrains Mono, sans-serif"),
        legend=dict(bgcolor="rgba(0,0,0,0)"), margin=dict(l=20, r=20, t=40, b=20)
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID)
    return fig

def build_capex_chart(capex_trend):
    if not capex_trend:
        return None

    df_capex = pd.DataFrame(capex_trend)
    df_capex['CapEx_M'] = df_capex['CapEx'] / 1e6

    fig = go.Figure(data=[
        go.Bar(
            x=df_capex['Date'],
            y=df_capex['CapEx_M'],
            marker_color='#B0C4DE',
            text=[f"${v:,.1f}M" for v in df_capex['CapEx_M']],
            textposition='auto'
        )
    ])
    fig.update_layout(
        title="近四期 資本支出 (CapEx) 趨勢 (單位: 百萬)",
        height=280,
        template="plotly_dark",
        paper_bgcolor="#0E1117",
        plot_bgcolor="#0E1117",
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig

# ==========================================
# 主頁面內容區塊
# ==========================================
st.markdown('<div class="main-header">STOCK RADAR PRO</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">整合基本/技術面選股、法人籌碼流向、資本支出 (CapEx) 與法說會重點摘要的量化儀表板</div>', unsafe_allow_html=True)

btn_clicked = st.button("開始執行量化篩選模型", type="primary", use_container_width=True)

if btn_clicked:
    symbols_list = [s.strip().upper() for s in watchlist_input.split(",") if s.strip()]

    if not symbols_list:
        st.warning("請在側邊欄輸入有效的股票代號清單！")
    else:
        results = []
        detail_store = {}
        debug_logs = []

        progress_bar = st.progress(0)
        status_text = st.empty()

        for idx, symbol in enumerate(symbols_list):
            status_text.text(f"正在分析 [{symbol}] ({idx + 1}/{len(symbols_list)})...")
            progress_bar.progress((idx + 1) / len(symbols_list))

            if idx > 0:
                time.sleep(0.5 + random.uniform(0, 0.4))

            try:
                df, info, holders, cashflow, calendar, news, stock_name, fetch_error = fetch_ticker_data(symbol)

                if df is None:
                    debug_logs.append(f"[FAIL] [{symbol}] 抓取失敗: {fetch_error}")
                    continue

                df['MA20'] = df['Close'].rolling(window=20).mean()
                df['MA60'] = df['Close'].rolling(window=60).mean()
                df['RSI'] = calculate_rsi(df['Close'])

                vol_5d_avg = df['Volume'].tail(5).mean()
                vol_today = df['Volume'].iloc[-1]
                current_price = df['Close'].iloc[-1]
                current_rsi = df['RSI'].iloc[-1] if not pd.isna(df['RSI'].iloc[-1]) else 50.0

                pe_ratio = info.get('trailingPE', None)
                roe = info.get('returnOnEquity', None)
                if roe is not None:
                    roe = roe * 100

                sector = info.get('sector', 'N/A')
                market_cap = info.get('marketCap', None)
                high_52 = info.get('fiftyTwoWeekHigh', None)
                low_52 = info.get('fiftyTwoWeekLow', None)

                latest_capex, capex_growth, capex_trend = extract_capex_data(cashflow)
                inst_percent, insider_percent, top_holders = extract_institutional_flow(info, holders)

                passed = True

                if enable_pe and pe_ratio is not None:
                    if pe_ratio > max_pe or pe_ratio < min_pe or pe_ratio <= 0:
                        passed = False

                if enable_roe and roe is not None and passed:
                    if roe < min_roe:
                        passed = False

                if enable_inst_hold and passed:
                    if inst_percent is None or inst_percent < 30.0:
                        passed = False

                if enable_capex_growth and passed:
                    if capex_growth <= 0:
                        passed = False

                if enable_trend and passed:
                    ma20_val = df['MA20'].iloc[-1]
                    if pd.isna(ma20_val) or current_price < ma20_val:
                        passed = False

                if enable_volume and passed:
                    if vol_5d_avg == 0 or vol_today < (vol_5d_avg * vol_multiplier):
                        passed = False

                if passed:
                    results.append({
                        '股票代號': symbol,
                        '公司名稱': stock_name,
                        '產業類別': sector,
                        '現價': round(current_price, 2),
                        '市值': format_market_cap(market_cap),
                        '本益比 (PE)': round(pe_ratio, 2) if pe_ratio else 'N/A',
                        'ROE (%)': round(roe, 2) if roe else 'N/A',
                        '機構持股 (%)': round(inst_percent, 1) if inst_percent else 'N/A',
                        'CapEx 年增率 (%)': round(capex_growth, 1) if capex_growth else 'N/A',
                        'RSI (14)': round(current_rsi, 1),
                        '爆量倍數': round(vol_today / vol_5d_avg, 2) if vol_5d_avg > 0 else 1.0
                    })

                    detail_store[symbol] = {
                        'df': df,
                        'info': info,
                        'stock_name': stock_name,
                        'sector': sector,
                        'market_cap': market_cap,
                        'high_52': high_52,
                        'low_52': low_52,
                        'vol_today': vol_today,
                        'capex_trend': capex_trend,
                        'latest_capex': latest_capex,
                        'capex_growth': capex_growth,
                        'inst_percent': inst_percent,
                        'insider_percent': insider_percent,
                        'top_holders': top_holders,
                        'calendar': calendar,
                        'news': news
                    }

                debug_logs.append(f"[OK] [{symbol}] 掃描完成")

            except Exception as e:
                debug_logs.append(f"[FAIL] [{symbol}] 錯誤: {e}")
                continue

        progress_bar.empty()
        status_text.empty()

        st.session_state['results_df'] = pd.DataFrame(results)
        st.session_state['detail_store'] = detail_store
        st.session_state['debug_logs'] = debug_logs

# ==========================================
# 畫面呈現
# ==========================================
if 'results_df' in st.session_state:
    results_df = st.session_state['results_df']
    detail_store = st.session_state['detail_store']

    if not results_df.empty:
        st.success(f"篩選完成！共有 {len(results_df)} 檔標的符合策略。")

        col1, col2, col3 = st.columns(3)
        col1.metric("符合條件股票數", f"{len(results_df)} 檔")
        roe_numeric = pd.to_numeric(results_df['ROE (%)'], errors='coerce')
        col2.metric("平均 ROE", f"{roe_numeric.mean():.1f}%" if not roe_numeric.isna().all() else "N/A")
        col3.metric("最高爆量倍數", f"{results_df['爆量倍數'].max():.2f} 倍")

        st.subheader("符合條件之股票主清單與市場資訊")
        st.dataframe(results_df, use_container_width=True, hide_index=True)

        st.markdown("---")

        st.subheader("個股深度分析（基本面 / 籌碼面 / CapEx / 法說會 / 新聞）")
        selected_symbol = st.selectbox("請選擇個股進行詳細分析：", results_df['股票代號'].tolist())

        if selected_symbol in detail_store:
            data = detail_store[selected_symbol]
            info = data['info']

            st.markdown(f"### {selected_symbol} - {data['stock_name']}")
            i_col1, i_col2, i_col3, i_col4 = st.columns(4)
            i_col1.metric("產業別", str(data['sector']))
            i_col2.metric("總市值", format_market_cap(data['market_cap']))
            i_col3.metric("52週最高價", f"${data['high_52']:.2f}" if data['high_52'] else "N/A")
            i_col4.metric("52週最低價", f"${data['low_52']:.2f}" if data['low_52'] else "N/A")

            st.markdown("---")

            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "技術分析 (K線圖)",
                "中文焦點新聞",
                "籌碼面與法人流向",
                "資本支出 (CapEx) 分析",
                "法說會重點與營運展望"
            ])

            with tab1:
                fig = build_candlestick_chart(data['df'], f"{selected_symbol} ({data['stock_name']})")
                st.plotly_chart(fig, use_container_width=True)

            with tab2:
                st.markdown(f"#### {selected_symbol} ({data['stock_name']}) 最新繁體中文新聞")
                render_news_list(data.get('news', []), max_items=10)

            with tab3:
                st.markdown("#### 法人與內部人持股結構")
                m_col1, m_col2 = st.columns(2)
                m_col1.metric("機構/法人總持股比例", f"{data['inst_percent']:.2f}%" if data['inst_percent'] else "無數據")
                m_col2.metric("公司內部人/董事持股比例", f"{data['insider_percent']:.2f}%" if data['insider_percent'] else "無數據")

                st.markdown("#### 前各大機構法人持有細節")
                if isinstance(data['top_holders'], pd.DataFrame) and not data['top_holders'].empty:
                    st.dataframe(data['top_holders'], use_container_width=True)
                else:
                    st.info("尚無前幾大機構法人的詳細持有數據。")

            with tab4:
                st.markdown("#### 資本支出 (CapEx) 產能擴張力道")
                c_col1, c_col2 = st.columns(2)
                capex_val_display = f"${data['latest_capex']/1e6:,.1f} M" if data['latest_capex'] else "無數據"
                c_col1.metric("最新一期 CapEx 金額", capex_val_display)
                c_col2.metric("CapEx 成長率 (YoY/QoQ)", f"{data['capex_growth']:.1f}%", delta_color="normal")

                if data['capex_trend']:
                    capex_fig = build_capex_chart(data['capex_trend'])
                    if capex_fig:
                        st.plotly_chart(capex_fig, use_container_width=True)
                else:
                    st.warning("無法取得該公司近幾期的歷史 CapEx 現金流數據。")

            with tab5:
                st.markdown("#### 最新法說會與財報發布資訊（繁體中文重點）")

                cal = data['calendar']
                earn_date = "未定/無數據"
                if cal is not None and isinstance(cal, dict) and 'Earnings Date' in cal:
                    earn_date = str(cal['Earnings Date'][0]) if cal['Earnings Date'] else "未定"

                # 將英文公司營運摘要轉換為繁體中文；若沒有實際法說會逐字稿，則以可取得的公司摘要作為重點資訊來源
                raw_summary = info.get('longBusinessSummary', '暫無法說會文本說明。')
                zh_summary = translate_summary_to_zh(raw_summary)

                st.markdown(f"""
                <div class="info-card">
                    <div class="info-title">{selected_symbol} ({data['stock_name']}) 法說會與財報指引｜繁體中文重點摘要</div>
                    <p><b>下一季財報 / 法說會預計開會日期：</b> {earn_date}</p>
                    <p><b>產業分類：</b> {info.get('sector', 'N/A')} - {info.get('industry', 'N/A')}</p>
                    <p><b>繁體中文法說／營運重點：</b></p>
                    <p style="color: #F0F6FC; font-size: 0.95rem; line-height: 1.7; white-space: pre-line;">
                        {zh_summary}
                    </p>
                </div>
                """, unsafe_allow_html=True)

                st.subheader("關鍵法說會追蹤重點檢核表")
                c1, c2 = st.columns(2)
                with c1:
                    st.checkbox("毛利率 (Gross Margin) 指引是否高於市場預期？", value=True)
                    st.checkbox("AI/新產品線產能稼動率 (Capacity Utilization) 是否滿載？", value=True)
                with c2:
                    st.checkbox("資本支出 (CapEx) 是用於研發與擴充高毛利產線？", value=True)
                    st.checkbox("管理層對下一季營收展望 (Guidance) 是否上調？", value=True)

    else:
        st.warning("沒有股票符合篩選條件，請嘗試放寬側邊欄參數。")

else:
    st.markdown("---")
    
    first_symbol = watchlist_input.split(",")[0].strip() if watchlist_input else "2330.TW"
    first_name = get_chinese_stock_name(first_symbol, "")
    
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader(f"觀察清單即時中文焦點新聞 ({first_symbol} {first_name})")
        news_data = fetch_chinese_news(first_symbol, first_name)
        render_news_list(news_data, max_items=5)

    with col_right:
        st.subheader("重點關注指標說明")
        st.markdown("""
        <div class="info-card">
            <div class="info-title">策略快速指南</div>
            <p><b>1. 本益比 (P/E) & ROE：</b> 基本面價值與股東權益報酬率篩選。</p>
            <p><b>2. 法人籌碼流向：</b> 關注外資與大機構資金進駐動向。</p>
            <p><b>3. CapEx 資本支出：</b> 觀察科技與製造業擴產與資本動能。</p>
            <p><b>4. 即時中文新聞：</b> 隨時掌握台美股市場最新消息與財經焦點。</p>
        </div>
        """, unsafe_allow_html=True)
