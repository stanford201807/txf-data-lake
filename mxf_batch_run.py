from batch_run import run_batch_job


if __name__ == "__main__":
    # 設定您要補 MXF 回測資料的區間
    START = "2026-05-18"
    END   = "2026-05-20"
    #START = "2024-01-01"
    #END   = "2024-12-31"

    run_batch_job(START, END, target_symbols=["MXF"])
