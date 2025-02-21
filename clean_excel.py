import pandas as pd
import re
import os
import traceback

# 設定 log 檔案名稱
LOG_FILE = "error_log.txt"

def log_error(message):
    """ 記錄錯誤到 log 檔案 """
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(message + "\n")

def clean_data(value):
    """
    清理數據：
      - 若數據不是字串則直接回傳
      - 移除前後空白
      - 移除開頭或結尾的 '*' 字元
      - 如果數據為 '-' 或 '—' 則回傳 0
      - 如果數據包含括號 ()，則取括號內的數字
      - 如果數據包含 '@'，則取 '@' 後面的數字
      - 如果數據包含 '<'，則取 '<' 後面的數字並除以 2
      - 如果數據為 "ND"（不分大小寫），則回傳 0
      - 嘗試將數據轉為數字，轉換失敗則保留原值
    """
    if not isinstance(value, str):
        return value
    value = value.strip()
    
    # 移除數據開頭或結尾的 '*' 字元
    value = re.sub(r'^\*|\*$', '', value)
    
    # 如果數據為 '-' 或 '—' 則回傳 0
    if value in ['-', '—']:
        return 0

    # 如果數據包含括號 ()，則取括號內的數字
    if "(" in value and ")" in value:
        m = re.search(r'\(([\d.]+)\)', value)
        if m:
            try:
                return float(m.group(1))
            except:
                pass

    # 如果數據包含 '@'，則取 @ 後面的數字
    if "@" in value:
        m = re.search(r'@([\d.]+)', value)
        if m:
            try:
                return float(m.group(1))
            except:
                pass

    # 如果數據包含 '<'，則取 '<' 後面的數字並除以 2
    if "<" in value:
        m = re.search(r'<\s*([\d.]+)', value)
        if m:
            try:
                return float(m.group(1)) / 2
            except:
                pass

    # 如果數據為 "ND"（不分大小寫），則回傳 0
    if value.upper() == "ND" or value == "N.A.":
        return 0

    # 嘗試轉換成數字
    try:
        return float(value)
    except ValueError:
        return value

def process_sheets(input_file, sheet_names):
    """
    處理 Excel 檔案中的多個工作表，並輸出對應的 CSV 檔案
    """
    required_headers = ["採樣時間", "懸浮固體", "氨氮", "生化需氧量", "總磷"]

    for sheet_name in sheet_names:
        try:
            # 讀取 Excel 檔案中的指定工作表，改用 openpyxl 引擎
            df = pd.read_excel(input_file, engine="openpyxl", sheet_name=sheet_name)
        except Exception as e:
            error_message = f"讀取工作表 {sheet_name} 時發生錯誤: {e}\n{traceback.format_exc()}"
            print(error_message)
            log_error(error_message)
            continue

        # 檢查 DataFrame 是否為空
        if df.empty:
            error_message = f"工作表 {sheet_name} 為空，跳過處理"
            print(error_message)
            log_error(error_message)
            continue

        # 篩選出工作表中存在的所需欄位
        available_columns = [col for col in df.columns if col in required_headers]
        if not available_columns:
            error_message = f"工作表 {sheet_name} 不包含所需的欄位，跳過處理"
            print(error_message)
            log_error(error_message)
            continue

        # 逐列檢查數據格式，找出可能導致錯誤的值
        problematic_rows = []
        for index, row in df.iterrows():
            for col in available_columns:
                try:
                    _ = clean_data(row[col])
                except Exception as e:
                    problematic_rows.append(row)
                    error_message = f"數據錯誤: 工作表 {sheet_name}，列 {index+1}，欄位 {col}，值: {row[col]}，錯誤: {e}"
                    print(error_message)
                    log_error(error_message)

        # 如果有問題數據，存成 CSV 方便檢查
        if problematic_rows:
            error_df = pd.DataFrame(problematic_rows)
            error_file = f"error_data_{sheet_name}.csv"
            error_df.to_csv(error_file, index=False, encoding="utf-8-sig")
            log_error(f"已儲存問題數據至 {error_file}")

        # 僅保留所需欄位，並在第一欄新增 "來源工作表"
        df_filtered = df[available_columns].copy()
        df_filtered.insert(0, "來源工作表", sheet_name)

        # 對每個欄位的數據進行清理處理
        for col in available_columns:
            df_filtered[col] = df_filtered[col].apply(clean_data)

        # 設定輸出檔案名稱
        output_file = f"{sheet_name}.csv"

        # 輸出 CSV，設定 utf-8-sig 以利 Excel 正確顯示中文
        df_filtered.to_csv(output_file, index=False, encoding="utf-8-sig")
        print(f"資料已成功匯出至 {output_file}")

if __name__ == "__main__":
    input_file = "德基各測站歷年水質.xlsx"  # Excel 檔案名稱
    sheet_names = ["G-1", "G-1A", "G-1B", "G-1B上", "G-1B中", "G-2", "G-3", "G-3A", "G-3B", "G-4", "G-5"]  # 需要處理的工作表名稱
    process_sheets(input_file, sheet_names)
