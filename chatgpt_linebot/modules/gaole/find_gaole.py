import json
from math import radians, sin, cos, sqrt, atan2
import psycopg2
from psycopg2.extras import RealDictCursor

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # 地球半徑（公里）

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    distance = R * c
    return distance

def find_nearest_stores_by_json(latitude, longitude, n=3):
    # 讀取店鋪資訊
    with open('store_info.json', 'r', encoding='utf-8') as file:
        stores = json.load(file)
    
    # 計算每家店鋪與給定位置的距離
    for store in stores:
        if store['latitude'] and store['longitude']:
            store['distance'] = haversine_distance(
                latitude, longitude, 
                store['latitude'], store['longitude']
            )
        else:
            store['distance'] = float('inf')  # 將沒有經緯度的店鋪設置為無限遠
    
    # 根據距離排序並返回最近的 n 家店鋪
    nearest_stores = sorted(stores, key=lambda x: x['distance'])[:n]
    return nearest_stores




def find_nearest_stores_by_db(latitude, longitude, n=3):
    # 連接到數據庫
    conn = psycopg2.connect(
        dbname="postgres",
        user="james.chen",
        password="",
        host="localhost"
    )
    
    # 使用 RealDictCursor 來獲取列名
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # 使用 PostGIS 的 ST_MakePoint 和 ST_Distance 函數
    query = """
    SELECT name, address, 
           ST_X(location::geometry) as longitude, 
           ST_Y(location::geometry) as latitude,
           ST_Distance(location, ST_MakePoint(%s, %s)::geography) / 1000 as distance
    FROM stores
    ORDER BY location <-> ST_MakePoint(%s, %s)::geography
    LIMIT %s;
    """
    
    cur.execute(query, (longitude, latitude, longitude, latitude, n))
    nearest_stores = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return nearest_stores

    
# 使用示例
# user_lat = 25.0330  # 使用者的緯度
# user_lon = 121.5654  # 使用者的經度

# nearest_stores = find_nearest_stores_by_db(user_lat, user_lon)

# print(f"最接近 ({user_lat}, {user_lon}) 的三家店鋪：")
# for store in nearest_stores:
#     print(f"店名: {store['name']}")
#     print(f"地址: {store['address']}")
#     print(f"距離: {store['distance']:.2f} 公里")
#     print('-' * 30)
