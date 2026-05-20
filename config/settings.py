# config/settings.py
import os
from datetime import datetime

# 載入 .env 環境變數
from dotenv import load_dotenv
load_dotenv()

# 資料根目錄
DATA_ROOT = r"D:\txf-data"

# Shioaji API 凭证（从环境变量读取）
API_KEY = os.getenv("SHIOAJI_API_KEY")
SECRET_KEY = os.getenv("SHIOAJI_SECRET_KEY")

if not API_KEY or not SECRET_KEY:
    raise ValueError("请设置环境变量 SHIOAJI_API_KEY 和 SHIOAJI_SECRET_KEY")

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

# 支援的商品清單（從 raw_ticks 目錄自動偵測）
DEFAULT_SYMBOLS = ["TXF", "MXF", "TSE"]

# 時間框架（用於目錄結構判斷）
TIMEFRAMES = ["1d", "1h", "1m"]

# 是否自動排除未來日期（避免轉換不存在的檔案）
EXCLUDE_FUTURE_DATES = True
