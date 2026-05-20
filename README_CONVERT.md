# Parquet 轉 CSV 工具使用說明

## 📌 工具簡介

本工具可將 `D:\txf-data\raw_ticks` 目錄下的 Parquet Tick 資料轉換為 CSV 格式，方便用於 Excel 分析或其他系統匯入。

---

## 🚀 快速開始

### 基本用法

```bash
# 互動模式（顯示選單）
python convert_to_csv.py

# 指定商品與日期範圍
python convert_to_csv.py --symbols TXF,MXF --start 2025-01-01 --end 2025-03-31

# 轉換所有商品所有日期
python convert_to_csv.py --all
```

---

## 📋 命令列參數

| 參數 | 簡寫 | 說明 | 範例 |
|------|------|------|------|
| `--symbols` | `-s` | 商品代碼，多個用逗號分隔 | `--symbols TXF,MXF` |
| `--start` | - | 起始日期 (YYYY-MM-DD) | `--start 2025-01-01` |
| `--end` | - | 結束日期 (YYYY-MM-DD) | `--end 2025-03-31` |
| `--all` | - | 轉換所有商品所有日期 | `--all` |
| `--output` | - | 輸出目錄（預設：D:\txf-data\csv） | `--output D:\txf-data\csv` |
| `--force` | - | 強制重新轉換（覆蓋已存在的 CSV） | `--force` |

**注意：**
- `--start` 和 `--end` 必須同時提供，否則會進入互動模式
- 若未提供任何參數，則顯示互動式選單

---

## 🎯 操作模式

### 模式 1：互動式選單（無參數）

```bash
python convert_to_csv.py
```

執行後會顯示：

```
============================================================
   Parquet → CSV 轉檔工具
============================================================

可用商品：
  1. TXF
  2. MXF
  3. TSE
  0. 全部轉換

請選擇商品 (可多選，用逗號分隔，如: 1,2): 1

商品 TXF 的資料範圍：
  最早日期：2025-01-02
  最晚日期：2026-04-27
起始日期 (預設 2025-01-02): 2026-04-01
結束日期 (預設 2026-04-28): 2026-04-01

開始轉換
   商品：TXF
   日期：2026-04-01 ~ 2026-04-01
   輸出：D:\txf-data\csv

🔄 開始轉換 TXF | 共 1 個檔案

TXF 完成：成功 1，失敗 0

============================================================
總計：成功 1，失敗 0
============================================================
```

---

### 模式 2：命令列參數（批量）

```bash
# 轉換 TXF 和 MXF 的 2025 年第一季資料
python convert_to_csv.py --symbols TXF,MXF --start 2025-01-01 --end 2025-03-31

# 轉換所有商品 2026 年 4 月的資料
python convert_to_csv.py --all --start 2026-04-01 --end 2026-04-30

# 轉換 TSE 單日資料
python convert_to_csv.py -s TSE --start 2026-04-28 --end 2026-04-28

# 強制重新轉換（覆蓋已存在的 CSV）
python convert_to_csv.py --symbols TXF --start 2026-04-01 --end 2026-04-01 --force
```

---

## 📂 輸出目錄結構

轉換後的 CSV 檔案會依以下結構儲存：

```
D:\txf-data\
├── csv/
│   ├── TXF/
│   │   ├── 2026/
│   │   │   ├── 04\2026-04-01_TXF_ticks.csv
│   │   │   ├── 04\2026-04-02_TXF_ticks.csv
│   │   │   └── ...
│   ├── MXF/
│   │   └── ...
│   └── TSE/
└── raw_ticks/  (原始 Parquet)
```

**檔名格式：** `{日期}_{商品代碼}_ticks.csv`
**範例：** `2026-04-01_TXF_ticks.csv`

---

## 📊 CSV 欄位說明

### 期貨（TXF, MXF）欄位：

| 欄位 | 型別 | 說明 |
|------|------|------|
| `ts` | 字串 | 時間戳記 (格式：YYYY-MM-DD HH:MM:SS) |
| `symbol` | 字串 | 商品代碼 (TXF/MXF) |
| `close` | 浮點數 | 收盤價 |
| `volume` | 整數 | 成交量 |
| `bid_price` | 浮點數 | 買盤價格 |
| `bid_volume` | 整數 | 買盤量 |
| `ask_price` | 浮點數 | 賣盤價格 |
| `ask_volume` | 整數 | 賣盤量 |
| `tick_type` | 整數 | 內外盤 (1:外盤, 2:內盤, 0:未知) |

### 加權指數（TSE）欄位：

| 欄位 | 型別 | 說明 |
|------|------|------|
| `ts` | 字串 | 時間戳記 |
| `symbol` | 字串 | 商品代碼 (TSE) |
| `close` | 浮點數 | 收盤價 |
| `volume` | 整數 | 成交量 |

**注意：** TSE 沒有 bid/ask 相關欄位，CSV 中會顯示為空值。

---

## ⚙️ 設定檔說明

### `config/settings.py`

```python
# 資料根目錄
DATA_ROOT = r"D:\txf-data"

# 原始 Tick 資料目錄
RAW_TICKS_DIR = os.path.join(DATA_ROOT, "raw_ticks")

# CSV 輸出目錄
CSV_OUTPUT_DIR = os.path.join(DATA_ROOT, "csv")

# CSV 輸出選項
CSV_OPTIONS = {
    "encoding": "utf-8-sig",      # 中文 Excel 相容（含 BOM）
    "date_format": "%Y-%m-%d %H:%M:%S",  # 時間格式
    "na_rep": "",                 # null 轉空字串
    "include_header": True,       # 包含欄位名稱
    "compression": None,          # 壓縮：None, "gzip", "bz2", "zip"
}

# 是否自動排除未來日期（避免轉換不存在的檔案）
EXCLUDE_FUTURE_DATES = True
```

---

## 🔍 功能說明

### 1. 自動掃描商品
工具會自動掃描 `raw_ticks` 目錄，列出所有可用的商品（如 TXF、MXF、TSE）。

### 2. 日期範圍偵測
對每個商品會掃描其最早的日期與最晚的日期，作為互動模式的預設值。

### 3. 未來日期排除
若結束日期晚於今天，會提示確認是否繼續（可防止轉換不存在的未來檔案）。

### 4. 錯誤處理
- 損壞的 Parquet 檔案會跳過，並記錄錯誤訊息
- 轉換失敗的檔案不會中斷整個批次，會繼續處理其他檔案
- 錯誤摘要會顯示前 5 筆，其餘折叠

---

## 📝 使用範例

### 範例 1：轉換最近 7 天的 TXF 資料（互動式）

```bash
python convert_to_csv.py -s TXF
# 輸入起始日期：2026-04-01
# 輸入結束日期：2026-04-07
```

### 範例 2：轉換 MXF 全部歷史資料

```bash
python convert_to_csv.py --symbols MXF --all
```

### 範例 3：轉換 TSE 單日（命令列）

```bash
python convert_to_csv.py -s TSE --start 2026-04-28 --end 2026-04-28
```

### 範例 4：批次轉換多商品多日期

```bash
python convert_to_csv.py -s TXF,MXF,TSE --start 2026-03-01 --end 2026-03-31
```

---

## ⚠️ 注意事項

1. **磁碟空間**：CSV 檔案比 Parquet 大約 3-5 倍，請確保有足夠空間
2. **編碼問題**：CSV 使用 `utf-8-sig` 編碼（含 BOM），可讓 Excel 正確顯示中文
3. **時間格式**：`ts` 欄位已轉為 `YYYY-MM-DD HH:MM:SS` 字串格式
4. **缺失值**：缺失值會轉為空字串（如 TSE 的 bid/ask 欄位）
5. **未來日期**：預設會排除未來日期，避免轉換不存在的檔案

---

## 🐛 常見問題

**Q1：執行時出現 `UnicodeEncodeError`？**
A：腳本已加入 Windows UTF-8 輸出處理，若仍有問題，請確認終端機編碼為 UTF-8。

**Q2：CSV 檔案太大，如何分割？**
A：目前工具依原始 Parquet 檔案轉換（一日一檔）。若需合併，可使用 Excel 或 pandas 後續處理。

**Q3：如何驗證轉換是否正確？**
A：比較 Parquet 與 CSV 的筆數，或隨機抽查幾筆資料：
```bash
# 計算 Parquet 筆數
python -c "import polars as pl; print(pl.read_parquet('D:\\txf-data\\raw_ticks\\TXF\\2026\\04\\2026-04-01_TXF_ticks.parquet').shape[0])"

# 計算 CSV 筆數（排除標題列）
python -c "import pandas as pd; print(len(pd.read_csv('D:\\txf-data\\csv\\TXF\\2026\\04\\2026-04-01_TXF_ticks.csv')) - 1)"
```

**Q4：可以合併多日檔案為單一 CSV 嗎？**
A：目前版本維持一日一檔。若需合併，可自行使用 pandas：
```python
import pandas as pd
import glob

files = glob.glob(r'D:\txf-data\csv\TXF\2026\04\*.csv')
df = pd.concat([pd.read_csv(f) for f in files])
df.to_csv('TXF_2026-04_combined.csv', index=False, encoding='utf-8-sig')
```

---

## 📞 聯絡支援

如有問題，請檢查：
1. `D:\txf-data\raw_ticks\` 目錄是否存在且包含 Parquet 檔案
2. Python 環境是否安裝 `polars` 與 `pandas`：
   ```bash
   pip install polars pandas
   ```
3. 確認有足夠的磁碟空間

---

**版本：** 1.0.0
**最後更新：** 2026-04-28
