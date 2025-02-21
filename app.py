import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.font_manager as fm
import math

def load_csv_files(folder_path):
    """讀取當前目錄下所有 CSV 檔案"""
    return [f for f in os.listdir(folder_path) if f.endswith(".csv")]

def clean_and_merge_data(csv_files, folder_path):
    """讀取並合併所有 CSV 檔案的數據"""
    required_cols = ["採樣時間", "懸浮固體", "氨氮", "生化需氧量", "總磷"]
    all_data = []

    for file in csv_files:
        file_path = os.path.join(folder_path, file)
        df = pd.read_csv(file_path)
        if all(col in df.columns for col in required_cols):
            df["來源檔案"] = file  
            all_data.append(df[required_cols + ["來源檔案"]])
        else:
            print(f"⚠️ 檔案 {file} 缺少必要欄位，已跳過！")

    if not all_data:
        return None

    df_all = pd.concat(all_data, ignore_index=True)
    df_all["採樣時間"] = pd.to_datetime(df_all["採樣時間"], errors="coerce")
    df_all = df_all.dropna(subset=["採樣時間"])
    df_all = df_all.sort_values(by="採樣時間")

    for col in ["懸浮固體", "氨氮", "生化需氧量", "總磷"]:
        df_all[col] = pd.to_numeric(df_all[col], errors="coerce")

    return df_all

def nice_num(x):
    """計算較為『好看』的刻度間隔"""
    exponent = math.floor(math.log10(x))
    fraction = x / (10 ** exponent)
    if fraction < 1.5:
        nice_fraction = 1
    elif fraction < 3:
        nice_fraction = 2
    elif fraction < 7:
        nice_fraction = 5
    else:
        nice_fraction = 10
    return nice_fraction * (10 ** exponent)

def calculate_max_values(df_all):
    """
    計算所有地點中，每個檢測物的最大值，
    並以該最大值乘以 1.05 作為各參數的基準上限
    """
    max_values = {}
    for param in ["懸浮固體", "氨氮", "生化需氧量", "總磷"]:
        raw_max = df_all[param].max(skipna=True)
        if pd.isna(raw_max) or raw_max <= 0:
            raw_max = 1
        max_values[param] = raw_max * 1.05
    return max_values

def generate_plots_for_file(df_all, folder_path, file_name, max_values):
    """針對每個 CSV 檔案生成獨立的水質變化圖，並統一 Y 軸上限"""
    if df_all is None or df_all.empty:
        print("❌ 沒有可用的數據來生成圖表！")
        return
    
    min_year = df_all["採樣時間"].dt.year.min()
    max_year = df_all["採樣時間"].dt.year.max()

    parameters = [
        ("懸浮固體", "懸浮固體", 50),
        ("氨氮", "氨氮", 0.1),
        ("生化需氧量", "生化需氧量", 1),
        ("總磷", "總磷", 25)
    ]

    fig, axs = plt.subplots(2, 2, figsize=(16, 12))
    axs = axs.flatten()

    for i, (param, title, baseline) in enumerate(parameters):
        ax = axs[i]
        has_scatter_label = False

        group = df_all[df_all["來源檔案"] == file_name].copy()  # **這裡加上 copy()**
        if group.empty:
            continue

        # **線性補值，確保折線不會斷裂**
        group[param] = group[param].interpolate(method="linear")

        # 畫折線圖
        ax.plot(group["採樣時間"], group[param], marker="o", markersize=4, linestyle="-", label=file_name)
        
        # **只標記真實超標點，不補值**
        if baseline is not None:
            over_mask = group[param] > baseline
            if over_mask.any():
                over_points = group.loc[over_mask, ["採樣時間", param]].dropna()  
                if not has_scatter_label and not over_points.empty:
                    ax.scatter(over_points["採樣時間"], over_points[param],
                               color="orange", s=40, zorder=5, label="超過基準線")
                    has_scatter_label = True
                elif not over_points.empty:
                    ax.scatter(over_points["採樣時間"], over_points[param],
                               color="orange", s=40, zorder=5)

        # 畫基準線
        if baseline is not None:
            ax.axhline(y=baseline, color="red", linestyle="--", label=f"基準線 ({baseline})")

        # 設定 X 軸格式
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.set_xlim(pd.Timestamp(f"{min_year}-01-01"), pd.Timestamp(f"{max_year}-12-31"))
        ax.tick_params(axis="x", rotation=45)

        # 根據所有地點的最大值(乘以1.05)計算 Y 軸上限與刻度
        raw_max = max_values[param]
        tick_interval = nice_num(raw_max / 5)
        y_limit = math.ceil(raw_max / tick_interval) * tick_interval
        ticks = np.arange(0, y_limit + tick_interval, tick_interval)

        ax.set_ylim(0, y_limit)
        ax.set_yticks(ticks)

        ax.set_title(title)
        ax.set_xlabel("")
        ax.set_ylabel(f"{param} (mg/L)")
        ax.legend()
        ax.grid(True)

    plt.tight_layout()

    img_folder = os.path.join(folder_path, "img")
    os.makedirs(img_folder, exist_ok=True)
    img_path = os.path.join(img_folder, f"{file_name}_water_quality_trends.png")
    plt.savefig(img_path, dpi=300, bbox_inches="tight")
    print(f"✅ 圖片已儲存至 {img_path}")
    plt.close(fig)


if __name__ == "__main__":
    folder_path = os.getcwd()  
    font_path = os.path.join(folder_path, "STHeiti Medium.ttc")
    
    if os.path.exists(font_path):
        plt.rcParams["font.family"] = fm.FontProperties(fname=font_path).get_name()
    else:
        print("⚠️ 找不到 STHeiti Medium.ttc，將使用預設字體！")

    csv_files = load_csv_files(folder_path)
    
    if csv_files:
        df_all = clean_and_merge_data(csv_files, folder_path)
        if df_all is not None:
            max_values = calculate_max_values(df_all)
            for file_name in csv_files:
                generate_plots_for_file(df_all, folder_path, file_name, max_values)
