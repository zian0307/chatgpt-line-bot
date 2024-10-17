import requests
from bs4 import BeautifulSoup
import json

# # 目標URL
# url = 'https://pokemongaole.com.tw/stores'

# # 發送HTTP請求
# response = requests.get(url)

# # 確認請求成功
# if response.status_code == 200:
#     # 解析HTML
#     soup = BeautifulSoup(response.content, 'html.parser')
    
#     # 假設店鋪位置在特定的HTML標籤中，這裡假設位置可能在 <div class="store-location"> 中
#     store_elements = soup.find_all('div', class_='store-location')
    
#     # 遍歷並列印出店鋪位置信息
#     for store in store_elements:
#         print(store.get_text(strip=True))
# else:
#     print(f"無法存取網站，狀態碼: {response.status_code}")


def get_store_info(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    stores = []
    
    store_elements = soup.find_all('div', class_='store-info')
    
    for store in store_elements:
        # 獲取完整的店名信息
        store_name_element = store.find('span', class_='font-bold')
        full_store_name = store_name_element.contents[0].strip()
        
        # 從完整店名中提取縣市和實際店名
        city = full_store_name.split(')')[0].strip('(')
        store_name = full_store_name.split(')')[-1].strip()
        
        address_element = store.find('address', class_='not-italic')
        address = address_element.contents[0].strip()
        
        map_link = store.find('a', class_='text-secondary')['href']
        
        tel = store.find('div', class_='tel').find('span', class_='flex-shrink-0').find_next('span').text.strip()

        stores.append({
            'city': city,
            'name': store_name,
            'address': address,
            'map_link': map_link,
            'tel': tel
        })
    
    return stores

def get_coordinates(address):
    api_key = "api_key"  # 請替換為您的 Google Maps API 密鑰
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": address,
        "key": api_key
    }
    response = requests.get(base_url, params=params)
    data = response.json()
    
    if data["status"] == "OK":
        location = data["results"][0]["geometry"]["location"]
        return location["lat"], location["lng"]
    else:
        return None, None

# 使用示例
# with open('soup_content.html', 'r', encoding='utf-8') as file:
#     html_content = file.read()

# store_info = get_store_info(html_content)

# # 添加經緯度信息到 store_info
# for store in store_info:
#     lat, lng = get_coordinates(store['address'])
#     store['latitude'] = lat
#     store['longitude'] = lng

# # 將 store_info 保存為 JSON 文件
# with open('store_info.json', 'w', encoding='utf-8') as json_file:
#     json.dump(store_info, json_file, ensure_ascii=False, indent=4)

# # 打印結果
# for store in store_info:
#     print(f"縣市: {store['city']}")
#     print(f"店名: {store['name']}")
#     print(f"地址: {store['address']}")
#     if store['latitude'] and store['longitude']:
#         print(f"經緯度: {store['latitude']}, {store['longitude']}")
#     else:
#         print("無法獲取經緯度")
#     print(f"地圖: {store['map_link']}")
#     print(f"電話: {store['tel']}")
#     print('-' * 30)

# print("店鋪信息已保存到 store_info.json 文件中。")
