import folium
import pandas as pd
import time
import os
import branca.colormap as cm
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# 📌 假設的藻類數據（不同時間點）
data = [
    {"station": "站點 A", "lat": 24.2650, "lon": 121.2000, "time": "2024-01", "algae": 50},
    {"station": "站點 B", "lat": 24.2610, "lon": 121.2100, "time": "2024-01", "algae": 200},
    {"station": "站點 C", "lat": 24.2630, "lon": 121.2200, "time": "2024-01", "algae": 500},
]

df = pd.DataFrame(data)

# 📌 設定綠色漸變顏色（淺綠 -> 深綠）
color_scale = cm.LinearColormap(
    colors=["#b3ffb3", "#66ff66", "#00cc00", "#008000"],  # 從淺綠到深綠
    vmin=0,  # 最小值
    vmax=500,  # 最大值
)

# 📌 設定顏色函數
def get_color(value):
    return color_scale(value)

# 📌 設定 Selenium 無頭模式
chrome_options = Options()
chrome_options.add_argument("--headless")  # 無頭模式（不開啟視窗）
chrome_options.add_argument("--window-size=1200x800")  # 設定視窗大小
chrome_options.add_argument("--disable-gpu")  # 避免 GPU 影響
chrome_options.add_argument("--no-sandbox")  # 防止 sandbox 限制

# 使用 webdriver-manager 下載並安裝 ChromeDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# 📌 依據不同時間點產生地圖
time_points = df["time"].unique()
for time_point in time_points:
    # 過濾該時間的數據
    filtered_df = df[df["time"] == time_point]

    # 建立 Folium 地圖
    m = folium.Map(location=[24.2565, 121.2066], zoom_start=13, tiles="CartoDB Positron", attr="CartoDB")

    # 📌 1. CartoDB Positron（簡潔地圖，水域淡藍色）
    folium.TileLayer("CartoDB Positron", name="簡潔地圖（強調水域）", attr="CartoDB").add_to(m)

    # 📌 2. CartoDB Voyager（更深藍的水域）
    folium.TileLayer("CartoDB Voyager", name="簡潔地圖（強調水體）", attr="CartoDB").add_to(m)


    # 📌 4. OpenStreetMap（開放地圖，標準水域顯示）
    folium.TileLayer("OpenStreetMap", name="標準地圖（含水域）", attr="OSM").add_to(m)


    
    folium.TileLayer("CartoDB Dark_Matter", name="黑色主題", attr="CartoDB").add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="衛星影像（無道路）",
    ).add_to(m)

    folium.LayerControl().add_to(m)  # 加入地圖圖層切換按鈕

    # 📌 加入站點標記
    for _, row in filtered_df.iterrows():
        popup_html = f"""
        <div style="width: 250px;">
            <b>站點名稱：</b> {row['station']}<br>
            <b>藻類數量：</b> {row['algae']}<br>
            <b>時間：</b> {row['time']}
        </div>
        """

        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=8,
            color=get_color(row["algae"]),  # 使用漸變綠色
            fill=True,
            fill_color=get_color(row["algae"]),
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=500),
        ).add_to(m)

    # 📌 加入顏色標示圖例
    color_scale.caption = "藻類數量分佈"
    m.add_child(color_scale)

    # 📌 儲存 HTML
    map_filename = f"map_{time_point}.html"
    m.save(map_filename)

    # 📌 取得 HTML 檔案的完整路徑
    map_filepath = os.path.abspath(map_filename)

    # 📌 開啟 HTML 截圖
    driver.get(f"file://{map_filepath}")
    time.sleep(5)  # 等待 5 秒，確保地圖加載完成

    # 📌 儲存圖片
    image_filename = f"map_{time_point}.png"
    driver.save_screenshot(image_filename)
    print(f"✅ 已儲存圖片: {image_filename}")

# 📌 關閉 Selenium 瀏覽器
driver.quit()
print("🎉 所有地圖已成功儲存！")
