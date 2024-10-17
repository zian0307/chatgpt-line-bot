import time
import random
from chatgpt_linebot.modules.gaole.find_gaole import find_nearest_stores_by_db, find_nearest_stores_by_json

def benchmark(func, *args, **kwargs):
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    return result, end_time - start_time

# # 測試參數列表
# test_params = [
#     {"lat": 25.0330, "lon": 121.5654, "n": 3, "iterations": 100, "name": "台北市中心"},
#     {"lat": 22.6273, "lon": 120.3014, "n": 5, "iterations": 100, "name": "高雄市中心"},
#     {"lat": 24.1477, "lon": 120.6736, "n": 10, "iterations": 100, "name": "台中市中心"},
#     {"lat": 25.1276, "lon": 121.7392, "n": 20, "iterations": 50, "name": "基隆市"},
#     {"lat": 24.9936, "lon": 121.3010, "n": 15, "iterations": 75, "name": "桃園市"},
#     {"lat": random.uniform(21.9, 25.3), "lon": random.uniform(120.0, 122.0), "n": 5, "iterations": 100, "name": "隨機位置"}
# ]

# for params in test_params:
#     print(f"\n測試案例: {params['name']}")
#     print(f"位置: ({params['lat']:.4f}, {params['lon']:.4f}), 尋找最近的 {params['n']} 家店鋪")
#     print(f"重複次數: {params['iterations']}")

#     # 數據庫方法
#     db_total_time = 0
#     for _ in range(params['iterations']):
#         _, db_time = benchmark(find_nearest_stores_by_db, params['lat'], params['lon'], params['n'])
#         db_total_time += db_time

#     db_avg_time = db_total_time / params['iterations']

#     # JSON 方法
#     json_total_time = 0
#     for _ in range(params['iterations']):
#         _, json_time = benchmark(find_nearest_stores_by_json, params['lat'], params['lon'], params['n'])
#         json_total_time += json_time

#     json_avg_time = json_total_time / params['iterations']

#     print(f"數據庫方法平均時間: {db_avg_time:.6f} 秒")
#     print(f"JSON 方法平均時間: {json_avg_time:.6f} 秒")

#     # 比較結果
#     db_results, _ = benchmark(find_nearest_stores_by_db, params['lat'], params['lon'], params['n'])
#     json_results, _ = benchmark(find_nearest_stores_by_json, params['lat'], params['lon'], params['n'])

#     print("\n結果比較:")
#     for i, (db_store, json_store) in enumerate(zip(db_results, json_results), 1):
#         print(f"第 {i} 近的店鋪:")
#         print(f"  數據庫: {db_store['name']} - 距離: {db_store['distance']:.2f} km")
#         print(f"  JSON: {json_store['name']} - 距離: {json_store['distance']:.2f} km")
#         print(f"  距離差異: {abs(db_store['distance'] - json_store['distance']):.4f} km")
#         print()

#     # 計算平均距離差異
#     avg_distance_diff = sum(abs(db_store['distance'] - json_store['distance']) 
#                             for db_store, json_store in zip(db_results, json_results)) / len(db_results)
#     print(f"平均距離差異: {avg_distance_diff:.4f} km")

# print("\n所有測試完成")
