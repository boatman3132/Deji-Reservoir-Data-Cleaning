# 原始資料
stations = ["S-2", "S-4", "S-6", "S-8", "S-10", "S-12", "S-14", "S-16", "S-18", "S-20", "S-22", "S-24", "S-26", "S-28"]
lats = [24.25522222, 24.25888889, 24.26330556, 24.26580556, 24.26527777, 24.26536111, 24.26438888, 24.26230555, 24.26019444, 24.26163889, 24.26302778, 24.26297222, 24.26602778, 24.26866666]
lons = [121.1728333, 121.17825, 121.1820833, 121.1878056, 121.1925833, 121.1968333, 121.2035833, 121.2062778, 121.2093611, 121.2117222, 121.2214722, 121.2259167, 121.2280833, 121.2285833]

# 假設每個站點的藻類數據（僅為示範用數值）
algae_values = [50, 200, 500, 120, 80, 300, 60, 450, 100, 250, 350, 400, 90, 70]
time_measurement = "2024-01"

# 整理資料成所需格式
data = []
for i, (lat, lon, algae) in enumerate(zip(lats, lons, algae_values)):
    # 將站點依序命名為 "站點 A", "站點 B", "站點 C", ...
    station_name = f"站點 {chr(65 + i)}"
    data.append({
        "station": station_name,
        "lat": lat,
        "lon": lon,
        "time": time_measurement,
        "algae": algae
    })

print(data)
