# StockRadar 台美股選股系統

以 Streamlit 打造的互動式選股與技術分析儀表板，支援台股與美股，可依基本面與技術面條件即時篩選觀察清單中的股票，並提供 K 線圖、均線、成交量、RSI 等技術指標的視覺化分析。

## 功能特色

- **雙市場支援**：可切換台股 (`.TW`) 或美股，並自訂觀察清單
- **基本面篩選**：本益比（上下限）、股東權益報酬率 (ROE)、殖利率
- **技術面篩選**：多頭排列（股價 > 20MA）、成交量爆量倍數、RSI 強勢區間
- **互動式技術分析圖表**：K 線圖 + 20MA/60MA 均線、成交量柱狀圖、RSI 指標圖
- **抓取除錯面板**：篩選完成後可展開查看每檔股票的資料抓取結果，方便排查限流或代號錯誤等問題
- **限流重試機制**：內建指數退避重試邏輯，並可選用 `curl_cffi` 模擬瀏覽器指紋，降低被 Yahoo Finance 限流 (429) 的機率

## 環境需求

- Python 3.9 以上
- 套件見 `requirements.txt`：
  ```
  streamlit
  yfinance
  pandas
  numpy
  plotly
  curl_cffi
  ```

  > `curl_cffi` 為選用套件，用於降低被 Yahoo Finance 限流的機率；未安裝時程式會自動退回預設抓取方式。

## 本機執行

```bash
# 1. 安裝套件
pip install -r requirements.txt

# 2. 啟動應用程式
streamlit run app.py
```

啟動後瀏覽器會自動開啟 `http://localhost:8501`。

## 部署到 Streamlit Community Cloud（手機也能用）

1. 將 `app.py` 與 `requirements.txt` 上傳到 GitHub repository
2. 前往 [share.streamlit.io](https://share.streamlit.io)，用 GitHub 帳號登入
3. 點選「New app」，選擇該 repository、分支，主檔案路徑填 `app.py`
4. 點擊「Deploy」，等待建置完成
5. 部署完成後會取得一個公開網址，手機瀏覽器開啟該網址即可使用，亦可加到手機主畫面當作 App 使用

## 使用方式

1. 於左側側邊欄選擇目標市場（台股 / 美股），並在觀察清單輸入股票代號（以逗號分隔）
2. 依需求開啟／調整基本面與技術面篩選條件
3. 點擊「開始掃描篩選股票」開始分析
4. 篩選完成後，畫面會顯示符合條件的股票清單與統計數據
5. 於下方選單選擇個股，即可檢視該股票的 K 線圖與技術指標

## 注意事項

- 本專案使用 [yfinance](https://github.com/ranaroussi/yfinance) 抓取 Yahoo Finance 公開資料，屬非官方套件，資料可能因 Yahoo 端限流或欄位調整而暫時無法取得，屬正常現象
- 台股部分股票的本益比 (PE)、ROE 等基本面欄位可能因 Yahoo Finance 資料缺失而顯示 `N/A`
- 本工具僅供技術與資料分析參考，不構成任何投資建議
