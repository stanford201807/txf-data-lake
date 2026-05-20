# batch_run.py
import pandas as pd
from adapters.shioaji_source import ShioajiSource
from main_etl import run_pipeline

DEFAULT_TARGET_SYMBOLS = ["TXF", "TSE"]


def run_batch_job(start_date, end_date, target_symbols=None):
    symbols = list(target_symbols or DEFAULT_TARGET_SYMBOLS)
    print(f"[Batch] {start_date} to {end_date} | Symbols: {', '.join(symbols)}")

    if start_date > end_date:
        raise ValueError(f"start_date ({start_date}) cannot be later than end_date ({end_date})")
    
    # 1. 建立一次連線 (Singleton)
    source = ShioajiSource()
    source.connect() # 這裡登入一次
    
    # 2. 產生日期列表 (排除週末)
    # 改用 'D' (Daily)，包含週六週日
    # 雖然會多跑很多天 "No data found"，但能確保抓到 "週六補班日"
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    print(f"[Info] Total {len(dates)} trading days to process.")
    
    try:
        for dt in dates:
            date_str = dt.strftime('%Y-%m-%d')
            
            # 3. 呼叫 ETL，並把 source 傳進去
            # 這樣 main_etl 就不會執行 logout
            print(f"\n> Processing: {date_str}")
            run_pipeline(date_str, shared_source=source, target_symbols=symbols)
            
    except KeyboardInterrupt:
        print("\n[Interrupted] Batch job interrupted by user.")
        
    finally:
        # 4. 全部跑完後，才執行最後一次登出
        print("\n[Complete] Batch Job Completed. Logging out...")
        source.report_usage()
        source.logout()

if __name__ == "__main__":
    # 設定您要補資料的區間
    #START = "2025-06-01"
    #END   = "2025-08-31"
    START = "2026-05-18"
    END   = "2026-05-20"
    run_batch_job(START, END)
