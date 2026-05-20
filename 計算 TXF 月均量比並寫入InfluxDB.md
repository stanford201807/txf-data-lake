# 計算 TXF 月均量比並寫入 InfluxDB (實作計畫)

## 目標
根據使用者需求，規劃一個全新的 Python 程式，其職責為：
1. 讀取 `D:\txf-data\raw_ticks\TXF` 中的歷史 Tick 資料。
2. 計算「月均量比」（當日成交量 / 近 N 個月日均成交量，N 預設為 3 個月或 60 個交易日）。
3. 將計算結果（包含月均量比與相關基底數值）寫入 **InfluxDB**。
4. 遵守嚴格的模組化與架構優先 (Architecture-First) 規範。

> [!CAUTION]
> 系統中目前未發現 `influxdb-client` 的連線配置與套件，此計畫將涵蓋依賴安裝與環境變數定義。

---

## 模組結構圖 (Module Architecture Diagram)

為了徹底遵守單一職責原則 (SRP) 與測試邊界 (Test Boundary)，此新功能將不破壞原有 ETL，而是建立於全新的資料夾 `scripts/calc_vol_ratio/` 下。

```mermaid
graph TD
    A[main.py<br/>Orchestrator] -->|1. extract_daily_volume| B(raw_tick_extractor.py<br/>Data Extraction Layer)
    A -->|2. calculate_monthly_ratio| C(vol_ratio_calculator.py<br/>Domain Logic Layer)
    A -->|3. write_to_influx| D(influx_writer.py<br/>Infrastructure Layer)
    
    B -.->|Reads| E[(D:\txf-data\raw_ticks)]
    D -.->|Writes via influxdb-client| F[(InfluxDB)]
    
    subgraph 測試邊界劃分 (Test Boundaries)
    B_test[測試: Mock Parquet 檔案驗證日盤/夜盤時間平移與加總] -.- B
    C_test[測試: 傳入記憶體 DataFrame 驗證 Rolling Average & Ratio 計算正確性] -.- C
    D_test[測試: Mock InfluxDBClient 驗證 Point 建構格式] -.- D
    end
```

### 各模組職責說明與對外 API
1. **`raw_tick_extractor.py`**
   - **職責**：專職讀取 Parquet 檔案。實作「交易日 (Trading Date)」邏輯（例如 00:00~05:00 歸屬於前一個交易日），並加總每日總成交量 (`volume`)。
   - **對外 API**：`extract_daily_volume(source_dir: str) -> pl.DataFrame`
2. **`vol_ratio_calculator.py`**
   - **職責**：純函數 (Pure Function) 領域邏輯。負責進行時間序列排序，並透過 Polars 高效計算 60 日 (`window=60`) 滾動平均及最終月均量比。
   - **對外 API**：`calculate_monthly_ratio(df: pl.DataFrame, window: int = 60) -> pl.DataFrame`
3. **`influx_writer.py`**
   - **職責**：處理與 InfluxDB 2.x 的網路通訊。將 DataFrame 轉換為 Line Protocol 或 SDK `Point` 格式，安全寫入資料儲存點。
   - **對外 API**：`write_to_influx(df: pl.DataFrame, config: dict)`

---

## 預期變更 (Proposed Changes)

### 依賴組件 (Dependencies)
#### [MODIFY] [requirements.txt](file:///f:/GitHub/txf-data-lake/requirements.txt)
- 增加 `influxdb-client` 以支援 InfluxDB 寫入操作。

### 全新功能模組
#### [NEW] [scripts/calc_vol_ratio/main.py](file:///f:/GitHub/txf-data-lake/scripts/calc_vol_ratio/main.py)
#### [NEW] [scripts/calc_vol_ratio/raw_tick_extractor.py](file:///f:/GitHub/txf-data-lake/scripts/calc_vol_ratio/raw_tick_extractor.py)
#### [NEW] [scripts/calc_vol_ratio/vol_ratio_calculator.py](file:///f:/GitHub/txf-data-lake/scripts/calc_vol_ratio/vol_ratio_calculator.py)
#### [NEW] [scripts/calc_vol_ratio/influx_writer.py](file:///f:/GitHub/txf-data-lake/scripts/calc_vol_ratio/influx_writer.py)

#### [MODIFY] [.env.example](file:///f:/GitHub/txf-data-lake/.env.example) (如果存在)
- 新增 InfluxDB 必要的連線變數：`INFLUXDB_URL`, `INFLUXDB_TOKEN`, `INFLUXDB_ORG`, `INFLUXDB_BUCKET`。

---

## 需要確認的項目 (Open Questions)

> [!IMPORTANT]
> 1. **InfluxDB 設定**：您的 InfluxDB 是本機運行還是雲端？請提供預期的 Bucket 名稱（例如：`txf_analytics`），以便寫入時正確指向。
> 2. **執行觸發時機**：這支程式會被獨立手動執行（作為研究腳本），還是需要併入您現有的 `main_etl.py` 每日排程中自動結算上傳？

---

## 驗證計畫 (Verification Plan)

### 自動化測試 (Automated Tests)
- 生成對應的 `test_raw_tick_extractor.py` 與 `test_vol_ratio_calculator.py` 使用 pytest 提供假資料進行斷言測試，確保時間推移（00:00 過後算作前一天夜盤）加總計算正確。

### 實際資料驗證 (Manual Verification)
- 實際執行腳本對 `D:\txf-data\raw_ticks\TXF` 資料庫進行處理。
- 印出並比對最後十天的量比數值，檢查是否有 `< 1` 與 `> 1` 的合理分布。
- 檢查 InfluxDB 介面（或回溯資料），確認 Metrics 格式如預期存入。
