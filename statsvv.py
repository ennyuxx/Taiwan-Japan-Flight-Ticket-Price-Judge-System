# statsvv.py
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# 0. 讀取與前處理

def load_data(csv_file: str) -> pd.DataFrame:
    """讀取原始機票資料並做基本清理。"""
    df = pd.read_csv(csv_file, encoding="utf-8")

    # 去除分類欄位多餘空白
    for col in ["出發地", "目的地", "淡旺季", "飛行時間"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # 票價轉成數值型態
    df["票價"] = pd.to_numeric(df["票價"], errors="coerce")
    df = df.dropna(subset=["票價"])
    df["票價"] = df["票價"].astype(int)

    # 建立方向欄位（去程/回程分析用）
    df["方向"] = df["出發地"] + "→" + df["目的地"]

    # 圖表所使用的中英時間轉換
    df["飛行時間"] = df["飛行時間"].map({"早": "Morning", "午": "Noon", "晚": "Evening"})

    return df


def build_thresholds(df: pd.DataFrame):
    """
    建立兩套門檻表：
    1. thresholds_season：依「出發地 + 目的地 + 淡旺季 + 飛行時間」分組
    2. thresholds_general：依「出發地 + 目的地 + 飛行時間」分組（不分季節）
    """
    # 1) 有淡旺季版本
    group_season = ["出發地", "目的地", "淡旺季", "飛行時間"]
    q_season = (
        df.groupby(group_season)["票價"]
          .quantile([0.25, 0.5, 0.75])
          .unstack()
    )
    q_season.columns = ["p25", "p50", "p75"]
    thresholds_season = q_season.reset_index()

    # 2) 整體價格版本（不分淡旺季）
    group_general = ["出發地", "目的地", "飛行時間"]
    q_general = (
        df.groupby(group_general)["票價"]
          .quantile([0.25, 0.5, 0.75])
          .unstack()
    )
    q_general.columns = ["p25", "p50", "p75"]
    thresholds_general = q_general.reset_index()

    return thresholds_season, thresholds_general

# 1. 時間、季節

def classify_time_slot(time_str: str) -> str | None:
    s = time_str.strip()
    try:
        t = datetime.strptime(s, "%H:%M").time()
    except ValueError:
        return None

    h, m = t.hour, t.minute

    # 早：06:00~09:59
    if 6 <= h <= 9:
        return "早"

    # 午：10:00~14:59
    if 10 <= h <= 14:
        return "午"

    # 晚：15:00~20:59
    if 15 <= h <= 20:
        return "晚"
    return None



def normalize_season_input(season_input: str) -> str | None :
    s = season_input.strip()
    if s in ["旺", "旺季"]:
        return "旺"
    if s in ["淡", "淡季"]:
        return "淡"
    if s in ["不知道", "不確定", "?", "NA", "na"]:
        return "不知道"
    return None

# 2. 價格判斷

def judge_price(
    dep: str,
    arr: str,
    time_slot: str,
    price: int,
    thresholds_df: pd.DataFrame,
    season: str | None = None
) -> str:
    time_map = {"早": "Morning", "午": "Noon", "晚": "Evening"}
    time_key = time_map.get(time_slot, time_slot)  # 找不到就用原本的值

    # 基本條件：方向 + 時段
    cond = (
        (thresholds_df["出發地"] == dep) &
        (thresholds_df["目的地"] == arr) &
        (thresholds_df["飛行時間"] == time_key)  
    )

    if season in ("旺", "淡") and "淡旺季" in thresholds_df.columns:
        cond = cond & (thresholds_df["淡旺季"] == season)


    row = thresholds_df[cond]

    if row.empty:
        return "這個出發地/目的地/季節/時段的組合在資料中沒有樣本，暫時無法判斷。"

    p25 = row["p25"].values[0]
    p50 = row["p50"].values[0]
    p75 = row["p75"].values[0]

    if price <= p25:
        level = "非常便宜"
        advice = "強烈建議購買，之後很難再看到更低價。"
    elif price <= p50:
        level = "偏便宜或合理價"
        advice = "價格在樣本分布中偏低，建議直接購買。"
    elif price <= p75:
        level = "偏貴"
        advice = "價格略高，若行程可彈性，建議再觀望一段時間。"
    else:
        level = "很貴"
        advice = "價格明顯高於一般水準，不建議現在購買。"

    season_text = f"[{season}季]" if season is not None else "[不分季節]"
    return (
        f"{dep}→{arr} {season_text} [{time_slot}班]\n"  # 這裡仍然用「早/午/晚」呈現給使用者
        f"目前票價：{price} 元\n"
        f"樣本分布：p25≈{int(p25)}、p50≈{int(p50)}、p75≈{int(p75)}\n"
        f"判斷結果：{level}。\n"
        f"建議：{advice}"
    )

# 3. 視覺化圖表

def show_summary_plots(df: pd.DataFrame):
 # 1. Overall price distribution
    plt.figure()
    df["票價"].hist(bins=10)
    plt.title("Overall Ticket Price Distribution")
    plt.xlabel("Ticket Price (NTD)")
    plt.ylabel("Count")
    plt.show()

# 2. Price distribution by route direction
    df.boxplot(column="票價", by="方向")
    plt.title("Ticket Price Distribution by Route Direction")
    plt.suptitle("")  
    plt.xlabel("Direction")
    plt.ylabel("Ticket Price (NTD)")
    plt.show()

# 3. Price distribution by flight time slot
    df.boxplot(column="票價", by="飛行時間")
    plt.title("Ticket Price Distribution by Time Slot")
    plt.suptitle("")
    plt.xlabel("Time Slot (Morning / Noon / Evening)")
    plt.ylabel("Ticket Price (NTD)")
    plt.show()