import json
import psycopg2
from psycopg2.extras import execute_values

# # 讀取 JSON 文件
# with open('store_info.json', 'r', encoding='utf-8') as file:
#     stores_data = json.load(file)

# # 數據庫連接設置
# db_params = {
#     "dbname": "postgres",
#     "user": "james.chen",
#     "password": "",
#     "host": "localhost"
# }

# # 連接到數據庫
# conn = psycopg2.connect(**db_params)
# cur = conn.cursor()

# # 準備插入數據
# insert_query = """
# INSERT INTO stores (city, name, address, map_link, tel, location)
# VALUES %s
# """

# # 轉換數據格式
# values = [
#     (
#         store['city'],
#         store['name'],
#         store['address'],
#         store['map_link'],
#         store['tel'],
#         f"POINT({store['longitude']} {store['latitude']})"
#     )
#     for store in stores_data
# ]

# # 執行批量插入
# execute_values(cur, insert_query, values)

# # 提交事務並關閉連接
# conn.commit()
# cur.close()
# conn.close()

# print(f"成功導入 {len(values)} 條記錄")