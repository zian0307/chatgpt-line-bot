from chatgpt_linebot.urls import agent, search_image_url


if __name__ == '__main__':
    tool, input_query = agent("給我楓之谷菈菈的照片")
    img_url = search_image_url(input_query)
    print(f"工具: {tool}")
    print(f"輸入查詢: {input_query}")
    print(f"圖片URL: {img_url}")
