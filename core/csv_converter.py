# core/csv_converter.py
"""
CSV 轉換模組
負責將 Parquet Tick 資料轉換為 CSV 格式
"""
import os
import polars as pl
from datetime import datetime, date
from typing import List, Optional, Tuple
from config.settings import RAW_TICKS_DIR, CSV_OUTPUT_DIR, CSV_OPTIONS, EXCLUDE_FUTURE_DATES


class CSVConverter:
    """CSV 轉換器"""

    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = output_dir or CSV_OUTPUT_DIR
        self.options = CSV_OPTIONS.copy()

    def scan_symbols(self, base_dir: str = RAW_TICKS_DIR) -> List[str]:
        """掃描 raw_ticks 目錄，回傳可用的商品清單"""
        if not os.path.exists(base_dir):
            return []
        symbols = []
        for item in os.listdir(base_dir):
            item_path = os.path.join(base_dir, item)
            if os.path.isdir(item_path):
                symbols.append(item)
        return sorted(symbols)

    def scan_date_range(self, symbol: str) -> Tuple[Optional[date], Optional[date]]:
        """掃描特定商品的最早與最晚日期"""
        symbol_dir = os.path.join(RAW_TICKS_DIR, symbol)
        if not os.path.exists(symbol_dir):
            return None, None

        min_date = None
        max_date = None

        for year_dir in os.listdir(symbol_dir):
            year_path = os.path.join(symbol_dir, year_dir)
            if not os.path.isdir(year_path):
                continue
            for month_dir in os.listdir(year_path):
                month_path = os.path.join(year_path, month_dir)
                if not os.path.isdir(month_path):
                    continue
                for filename in os.listdir(month_path):
                    if filename.endswith(".parquet"):
                        # 檔名格式：YYYY-MM-DD_SYMBOL_ticks.parquet
                        date_str = filename.split("_")[0]
                        try:
                            file_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                            if min_date is None or file_date < min_date:
                                min_date = file_date
                            if max_date is None or file_date > max_date:
                                max_date = file_date
                        except ValueError:
                            continue
        return min_date, max_date

    def list_files(self, symbol: str, start_date: Optional[date] = None,
                   end_date: Optional[date] = None) -> List[Tuple[str, str]]:
        """
        列出要轉換的 Parquet 檔案清單
        回傳：(檔案路徑, 日期字串) 列表
        """
        symbol_dir = os.path.join(RAW_TICKS_DIR, symbol)
        if not os.path.exists(symbol_dir):
            return []

        files = []
        today = date.today()
        exclude_future = getattr(self, 'exclude_future', EXCLUDE_FUTURE_DATES)

        for year_dir in sorted(os.listdir(symbol_dir)):
            year_path = os.path.join(symbol_dir, year_dir)
            if not os.path.isdir(year_path):
                continue
            for month_dir in sorted(os.listdir(year_path)):
                month_path = os.path.join(year_path, month_dir)
                if not os.path.isdir(month_path):
                    continue
                for filename in sorted(os.listdir(month_path)):
                    if not filename.endswith(".parquet"):
                        continue
                    # 解析日期
                    date_str = filename.split("_")[0]
                    try:
                        file_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    except ValueError:
                        continue

                    # 日期篩選
                    if start_date and file_date < start_date:
                        continue
                    if end_date and file_date > end_date:
                        continue
                    if exclude_future and file_date > today:
                        continue

                    file_path = os.path.join(month_path, filename)
                    files.append((file_path, date_str))

        return files

    def convert_file(self, parquet_path: str, date_str: str, symbol: str,
                     skip_existing: bool = True) -> Tuple[bool, str]:
        """
        轉換單一 Parquet 檔案為 CSV
        回傳：(成功與否, 訊息)

        Args:
            skip_existing: 若為 True，當 CSV 已存在時會跳過轉換
        """
        try:
            # 建立輸出目錄
            year, month = date_str.split("-")[0], date_str.split("-")[1]
            output_subdir = os.path.join(self.output_dir, symbol, year, month)
            os.makedirs(output_subdir, exist_ok=True)

            # 輸出檔名：維持原檔名（但副檔名改為 .csv）
            filename = f"{date_str}_{symbol}_ticks.csv"
            output_path = os.path.join(output_subdir, filename)

            # 檢查 CSV 是否已存在
            if skip_existing and os.path.exists(output_path):
                return True, f"跳過（已存在）：{output_path}"

            # 讀取 Parquet
            df = pl.read_parquet(parquet_path)

            if df.is_empty():
                return False, "檔案為空"

            # 時間格式化：將 ts 欄位轉為字串
            if "ts" in df.columns:
                df = df.with_columns(
                    pl.col("ts").dt.strftime(self.options["date_format"]).alias("ts")
                )

            # 轉換為 Pandas 以使用 to_csv（Polars 尚無完整 CSV 選項）
            pdf = df.to_pandas()

            # 寫入 CSV
            pdf.to_csv(
                output_path,
                index=False,
                encoding=self.options["encoding"],
                na_rep=self.options["na_rep"]
            )

            return True, f"已轉換：{output_path}"

        except Exception as e:
            return False, f"錯誤：{str(e)}"

    def batch_convert(self, symbol: str, start_date: Optional[date] = None,
                      end_date: Optional[date] = None,
                      progress_callback=None, skip_existing: bool = True) -> dict:
        """
        批次轉換
        回傳統計資訊 dict

        Args:
            skip_existing: 若為 True，跳過已存在的 CSV 檔案
        """
        files = self.list_files(symbol, start_date, end_date)
        total = len(files)
        success = 0
        failed = 0
        skipped = 0
        errors = []

        print(f"[Convert] 開始轉換 {symbol} | 共 {total} 個檔案")

        for idx, (file_path, date_str) in enumerate(files, 1):
            ok, msg = self.convert_file(file_path, date_str, symbol, skip_existing=skip_existing)
            if ok:
                if "跳過" in msg:
                    skipped += 1
                    # 跳過的不計入 success（或可另計）
                else:
                    success += 1
            else:
                failed += 1
                errors.append(f"{date_str}: {msg}")

            # 進度回調
            if progress_callback:
                progress_callback(idx, total, date_str, ok, msg)

        return {
            "symbol": symbol,
            "total": total,
            "success": success,
            "skipped": skipped,
            "failed": failed,
            "errors": errors
        }

    @staticmethod
    def get_output_path(symbol: str, date_str: str, output_dir: Optional[str] = None) -> str:
        """取得 CSV 輸出路徑（不實際轉換，僅預覽）"""
        year, month = date_str.split("-")[0], date_str.split("-")[1]
        base = output_dir or CSV_OUTPUT_DIR
        return os.path.join(base, symbol, year, month, f"{date_str}_{symbol}_ticks.csv")
