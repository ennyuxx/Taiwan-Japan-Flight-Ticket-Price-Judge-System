# mainvv.py
from statsvv import (
    load_data,
    build_thresholds,
    classify_time_slot,
    normalize_season_input,
    judge_price,
    show_summary_plots,
)

from datetime import datetime

CSV_FILE = "機票資料.csv"

# 1.使用者輸入

#半形、全形轉換
def to_half_width(s: str) -> str:
    result = ""
    for ch in s:
        code = ord(ch)

        #全形英數符號
        if 65281 <= code <= 65374:
            result += chr(code - 65248)

        #全形空白
        elif code == 12288:
            result += " "

        else:
            result += ch

    return result


def input_dep() -> str:
    while True:
        raw = input("出發地（TPE / NRT）：").strip()

        dep = to_half_width(raw).upper()

        if dep in ("TPE", "NRT"):
            return dep

        print("出發地僅支援 TPE 或 NRT，請重新輸入。")

def auto_arr(dep: str) -> str:
    if dep == "TPE":
        return "NRT"
    else:
        return "TPE"

def input_date_str() -> str:
    while True:
        date_input = input("飛行日期（格式：YYYY/MM/DD，例如 2026/01/03）：").strip()
        try:
            _ = datetime.strptime(date_input, "%Y/%m/%d")
            return date_input
        except ValueError:
            print("日期格式錯誤，請輸入YYYY/MM/DD，例如：2026/01/03。")


def input_time_and_slot() -> tuple[str, str]:
    while True:
        time_input = input("起飛時間（24 小時制 HH:MM，例如 08:30）：").strip()
        time_slot = classify_time_slot(time_input)
        if time_slot is None:
            print("系統無法從時間判斷早/午/晚，請重新輸入 HH:MM（例如 08:30）。")
            continue
        return time_input, time_slot


def input_season() -> str:
    while True:
        season_raw = input("請輸入季節（旺 / 淡 / 不知道）：").strip()
        season = normalize_season_input(season_raw)

        if season is None:
            print("輸入錯誤，請輸入「旺」、「淡」或「不知道」。")
            continue

        return season



def input_price() -> int:
    while True:
        price_str = input("目前看到的票價（台幣）：").strip()
        try:
            price = int(price_str)

            if price <= 0:
                print("票價不能為負數或為零，請重新輸入。")
                continue

            return price

        except ValueError:
            print("票價必須為阿拉伯數字（整數），請重新輸入。")

# 2.機票判別互動流程

def ticket_judge_loop(thresholds_season, thresholds_general):
    print("\n【機票價格判別模式】\n")

    while True:
        dep = input_dep()
        arr = auto_arr(dep)
        print(f"系統已自動將目的地設定為：{arr}")

        date_str = input_date_str()
        time_str, time_slot = input_time_and_slot()
        season = input_season()
        price = input_price()

        print("\n【分析結果】")
        print(f"查詢條件：{dep}→{arr}，日期 {date_str}，起飛時間 {time_str}")

        if season in ("旺", "淡"):
            print("使用模式：有季節資訊（依淡旺季 + 時段 + 方向判斷）")
            result = judge_price(
                dep, arr, time_slot, price,
                thresholds_season,
                season=season, 
            )
        else:
            print("使用模式：不知道季節（依整體價格分布 + 時段 + 方向判斷）")
            result = judge_price(
                dep, arr, time_slot, price,
                thresholds_general,
                season=None,       
            )

        print(result)
        print("————————————————\n")

        cont = input("要再查一筆嗎？(y/n)：").strip().lower()
        if cont != "y":
            print("離開機票判別模式，回到主選單。\n")
            break

# 3. 主選單流程

def main():
    df = load_data(CSV_FILE)
    thresholds_season, thresholds_general = build_thresholds(df)

    print("歡迎使用「台灣－日本機票價格判別系統」！")
    print("本系統目前支援：臺灣傳統航空之經濟艙，桃園（TPE） ↔ 東京成田（NRT）之單程航線。")
    print("系統資料來源：2026年1月至4月期間實際蒐集之票價樣本。\n")

    print("使用方式簡介：")
    print("  1. 若您知道淡季／旺季，系統將以「季節＋時段」的更精細分組分析。")
    print("  2. 若您不確定季節，系統會改用「整體價格分布」進行判斷。")
    print("  3. 起飛時間將自動分類為早／午／晚班，以提升判斷準確度。\n")

    while True:
        print("請選擇功能：")
        print("  1. 查看圖表（價格分佈）")
        print("  2. 使用機票價格判別")
        print("  3. 離開系統")
        choice = input("請輸入選項編號（1 / 2 / 3）：").strip()

        if choice == "1":
            show_summary_plots(df)
            input("\n圖表顯示完畢，按 Enter 回到主選單。")
        elif choice == "2":
            ticket_judge_loop(thresholds_season, thresholds_general)
        elif choice == "3":
            print("感謝使用機票價格判別系統！")
            break
        else:
            print("無效選項，請重新輸入 1、2 或 3。\n")


if __name__ == "__main__":
    main()