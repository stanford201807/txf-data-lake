#!/usr/bin/env python3
"""
Parquet 轉 CSV 工具
將 D:\txf-data\raw_ticks 下的 Parquet Tick 資料轉換為 CSV
"""
import os
import sys
import argparse
from datetime import datetime, date
from typing import Tuple

# 解決 Windows cmd 編碼問題，確保 UTF-8 輸出
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 確保 import 路徑正確
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import RAW_TICKS_DIR, CSV_OUTPUT_DIR, DEFAULT_SYMBOLS
from core.csv_converter import CSVConverter


def print_banner():
    print("=" * 60)
    print("   Parquet → CSV 轉檔工具")
    print("=" * 60)


def interactive_select_symbols(converter: CSVConverter) -> list:
    """互動式商品選擇選單"""
    available = converter.scan_symbols()
    if not available:
        print("[Error] 找不到任何商品目錄，請確認 raw_ticks 路徑：", RAW_TICKS_DIR)
        sys.exit(1)

    print("\n可用商品：")
    for i, sym in enumerate(available, 1):
        print(f"  {i}. {sym}")
    print("  0. 全部轉換")

    choice = input("\n請選擇商品 (可多選，用逗號分隔，如: 1,2): ").strip()

    if choice == "0":
        return available

    selected = []
    for part in choice.split(","):
        part = part.strip()
        if part.isdigit():
            idx = int(part) - 1
            if 0 <= idx < len(available):
                selected.append(available[idx])
    return selected


def interactive_date_range(converter: CSVConverter, symbol: str) -> Tuple[date, date]:
    """互動式日期範圍選擇"""
    min_date, max_date = converter.scan_date_range(symbol)
    today = date.today()

    print(f"\n商品 {symbol} 的資料範圍：")
    if min_date and max_date:
        print(f"  最早日期：{min_date}")
        print(f"  最晚日期：{max_date}")
    else:
        print("  無法偵測日期範圍")

    default_start = min_date.strftime("%Y-%m-%d") if min_date else "2025-01-01"
    default_end = today.strftime("%Y-%m-%d")

    start_str = input(f"起始日期 (預設 {default_start}): ").strip() or default_start
    end_str = input(f"結束日期 (預設 {default_end}): ").strip() or default_end

    try:
        start = datetime.strptime(start_str, "%Y-%m-%d").date()
        end = datetime.strptime(end_str, "%Y-%m-%d").date()
    except ValueError:
        print("[Error] 日期格式錯誤，請使用 YYYY-MM-DD")
        sys.exit(1)

    if start > end:
        print("[Error] 起始日期不能晚於結束日期")
        sys.exit(1)

    return start, end


def parse_args():
    """命令列參數解析"""
    parser = argparse.ArgumentParser(
        description="將 raw_ticks 的 Parquet 檔案轉換為 CSV",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例：
  # 互動模式（顯示選單）
  python convert_to_csv.py

  # 指定商品與日期範圍
  python convert_to_csv.py --symbols TXF,MXF --start 2025-01-01 --end 2025-03-31

  # 轉換全部商品所有日期
  python convert_to_csv.py --all
        """
    )
    parser.add_argument("-s", "--symbols", type=str,
                        help="商品代碼，多個用逗號分隔 (如: TXF,MXF)")
    parser.add_argument("--start", type=str,
                        help="起始日期 (YYYY-MM-DD)")
    parser.add_argument("--end", type=str,
                        help="結束日期 (YYYY-MM-DD)")
    parser.add_argument("--all", action="store_true",
                        help="轉換所有商品所有日期")
    parser.add_argument("--output", type=str,
                        help=f"輸出目錄 (預設: {CSV_OUTPUT_DIR})")
    parser.add_argument("--force", action="store_true",
                        help="強制重新轉換（即使 CSV 已存在）")
    return parser.parse_args()


def main():
    print_banner()

    args = parse_args()
    converter = CSVConverter(output_dir=args.output)

    # 決定商品清單
    if args.symbols:
        symbols = [s.strip().upper() for s in args.symbols.split(",")]
    elif args.all:
        symbols = converter.scan_symbols()
        if not symbols:
            print("找不到任何商品")
            return
    else:
        # 互動模式
        symbols = interactive_select_symbols(converter)
        if not symbols:
            print("未選擇任何商品")
            return

    # 決定日期範圍
    if args.start and args.end:
        try:
            start = datetime.strptime(args.start, "%Y-%m-%d").date()
            end = datetime.strptime(args.end, "%Y-%m-%d").date()
        except ValueError:
            print("日期格式錯誤，請使用 YYYY-MM-DD")
            return
    elif args.start or args.end:
        print("--start 和 --end 必須同時提供")
        return
    else:
        # 互動模式：對第一個商品選擇日期範圍
        start, end = interactive_date_range(converter, symbols[0])

    # 確認未來日期排除
    today = date.today()
    if end > today:
        print(f"結束日期 {end} 晚於今天 {today}，未來日期將被自動排除")
        confirm = input("是否繼續？(y/n): ").strip().lower()
        if confirm != "y":
            return

    # 開始批次轉換
    print(f"\n開始轉換")
    print(f"   商品：{', '.join(symbols)}")
    print(f"   日期：{start} ~ {end}")
    print(f"   輸出：{converter.output_dir}")
    if args.force:
        print(f"   模式：強制重新轉換（覆蓋已存在檔案）")
    else:
        print(f"   模式：跳過已存在檔案")
    print()

    total_success = 0
    total_failed = 0
    total_skipped = 0

    for sym in symbols:
        result = converter.batch_convert(sym, start, end, skip_existing=not args.force)
        total_success += result["success"]
        total_failed += result["failed"]
        total_skipped += result.get("skipped", 0)

        print(f"\n{sym} 完成：成功 {result['success']}，跳過 {result.get('skipped', 0)}，失敗 {result['failed']}")
        if result["errors"]:
            for err in result["errors"][:5]:  # 只顯示前 5 個錯誤
                print(f"   ! {err}")
            if len(result["errors"]) > 5:
                print(f"   ... 還有 {len(result['errors']) - 5} 個錯誤")

    print("\n" + "=" * 60)
    print(f"總計：成功 {total_success}，跳過 {total_skipped}，失敗 {total_failed}")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n使用者中斷操作")
        sys.exit(0)
    except Exception as e:
        print(f"\n程式錯誤：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
