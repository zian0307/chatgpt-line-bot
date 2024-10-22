import re
import sys
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, Request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, LocationMessage, TextSendMessage, ImageSendMessage, LocationSendMessage

from chatgpt_linebot.database import decrypt_token, get_user_settings, save_user_settings
from chatgpt_linebot.memory import Memory
from chatgpt_linebot.modules import Horoscope, ImageCrawler, RapidAPIs, recommend_videos
from chatgpt_linebot.modules.chat import generate_chat_response, chat_completion
from chatgpt_linebot.modules.threads_function import ThreadsAPI
from chatgpt_linebot.modules.gaole.find_gaole import find_nearest_stores_by_json
from chatgpt_linebot.prompts import agent_template, girlfriend

sys.path.append(".")
import config

line_app = APIRouter()
memory = Memory(3)
horoscope = Horoscope()
rapidapis = RapidAPIs(config.RAPID)

line_bot_api = LineBotApi(config.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(config.LINE_CHANNEL_SECRET)

@line_app.post("/callback")
async def callback(request: Request) -> str:
    signature = request.headers["X-Line-Signature"]
    body = await request.body()
    try:
        handler.handle(body.decode(), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Missing Parameter")
    return "OK"

@handler.add(MessageEvent, message=(TextMessage, LocationMessage))
def handle_message(event) -> None:
    """處理用戶發送的消息"""
    print(f"開始處理消息: {event}")
    reply_token = event.reply_token
    
    if isinstance(event.message, TextMessage):
        handle_text_message(event, reply_token)
    elif isinstance(event.message, LocationMessage):
        handle_location_message(event, reply_token)
    else:
        print("未知消息類型")
        send_text_reply(reply_token, "抱歉，我無法處理這種類型的消息。")

    print("消息處理完成")

def handle_text_message(event, reply_token):
    """處理文本消息"""
    user_message = event.message.text
    source_type = event.source.type
    source_id = getattr(event.source, f"{source_type}_id", None)
    
    print(f"用戶消息: {user_message}")
    print(f"消息來源類型: {source_type}")
    print(f"消息來源ID: {source_id}")

    if source_type == "user":
        user_name = line_bot_api.get_profile(source_id).display_name
        print(f"用戶名: {user_name}")
    elif not user_message.startswith("@chat"):
        print("群組消息不以 @chat 開頭，忽略")
        return
    else:
        user_message = user_message.replace("@chat", "").strip()
        print(f"處理群組消息: {user_message}")

    if user_message.startswith("/"):
        handle_command(event, reply_token, user_message)
    else:
        process_message(event, reply_token, user_message, source_id)

def handle_location_message(event, reply_token):
    """處理位置消息"""
    user_latitude = event.message.latitude
    user_longitude = event.message.longitude
    nearest_stores = find_nearest_stores_by_json(user_latitude, user_longitude, n=3)
    # reply_message = format_nearest_stores(nearest_stores)
    try:
        reply_message = format_nearest_stores_as_location_messages(nearest_stores)
    except Exception as e:
        print(f"發生錯誤: {str(e)}")
        reply_message = format_nearest_stores(nearest_stores)
    send_text_reply(reply_token, reply_message)

def handle_command(event, reply_token, user_message):
    """處理特定命令"""
    if user_message.startswith("/set_threads_id "):
        handle_set_threads_id(event, reply_token, user_message)
    elif user_message.startswith("/set_threads_token "):
        handle_set_threads_token(event, reply_token, user_message)
    elif user_message.startswith("/threads "):
        handle_post_to_threads(event, reply_token, user_message)

def process_message(event, reply_token, user_message, source_id):
    """處理一般消息"""
    tool, input_query = agent(user_message)
    print(f"選擇的工具: {tool}")
    print(f"輸入查詢: {input_query}")

    if tool == "chat_completion":
        input_query = f"{girlfriend}:\n {input_query}"
        memory.append(source_id, "user", f"{girlfriend}:\n {user_message}")
        print("已更新記憶")

    try:
        response = execute_tool(tool, input_query, source_id)
        send_response(reply_token, response)
    except Exception as e:
        print(f"發生錯誤: {str(e)}")
        send_text_reply(reply_token, str(e))

def execute_tool(tool, input_query, source_id):
    """執行選定的工具"""
    function_map = {
        "recommend_videos": recommend_videos,
        "chat_completion": lambda: chat_completion(source_id, memory),
        "rapidapis.ai_text_to_img": rapidapis.ai_text_to_img,
        "search_image_url": search_image_url,
        "horoscope.get_horoscope_response": horoscope.get_horoscope_response,
    }
    
    selected_function = function_map.get(tool)
    
    if selected_function is None:
        # 如果沒有找到對應的工具，默認使用 chat_completion
        return chat_completion(source_id, memory)
    
    if tool == "chat_completion":
        return selected_function()
    else:
        # 對於其他工具，傳遞 input_query
        return selected_function(input_query)

def send_response(reply_token, response):
    """發送回覆"""
    if is_url(response):
        print("發送圖片回覆")
        send_image_reply(reply_token, response)
    else:
        print("發送文字回覆")
        send_text_reply(reply_token, response)

def format_nearest_stores(stores):
    """格式化最近的店鋪信息"""
    reply_message = "最近的店鋪：\n\n"
    for i, store in enumerate(stores, 1):
        reply_message += f"{i}. {store['name']}\n"
        reply_message += f"   地址：{store['address']}\n"
        reply_message += f"   電話：{store['tel']}\n"
        reply_message += f"   距離：{store['distance']:.2f} km\n"
        if "map_link" in store:
            reply_message += f"   地圖：{store['map_link']}\n"
        reply_message += "\n"
    return reply_message

def format_nearest_stores_as_location_messages(stores):
    """將最近的店鋪信息格式化為 LocationSendMessage 對象列表"""
    location_messages = []
    for store in stores[:1]:
        title = f"{store['name']} (距離: {store['distance']:.2f} km)"
        address = store['address']
        latitude = store.get('latitude')
        longitude = store.get('longitude')
        
        if latitude and longitude:
            location_message = LocationSendMessage(
                title=title,
                address=address,
                latitude=latitude,
                longitude=longitude
            )
            location_messages.append(location_message)
    
    return location_messages

def handle_set_threads_id(event, reply_token, user_message):
    """處理設置 Threads ID 的命令"""
    user_id = event.source.user_id
    threads_user_id = user_message[16:].strip()
    user_settings = get_user_settings(user_id)
    if user_settings:
        save_user_settings(user_id, threads_user_id, decrypt_token(user_settings.encrypted_token))
    else:
        save_user_settings(user_id, threads_user_id, "")
    send_text_reply(reply_token, f"喵~！我記住你的Threads名字啦：{threads_user_id} (^._.^)ﾉ")

def handle_set_threads_token(event, reply_token, user_message):
    """處理設置 Threads 訪問令牌的命令"""
    user_id = event.source.user_id
    threads_token = user_message[19:].strip()
    user_settings = get_user_settings(user_id)
    if user_settings:
        save_user_settings(user_id, user_settings.threads_user_id, threads_token)
    else:
        save_user_settings(user_id, "", threads_token)
    send_text_reply(reply_token, "喵喵~！你的Threads秘密我已經藏好啦！(=^･ω･^=)✨\n現在我們可以一起在Threads上冒險了喵~")

def handle_post_to_threads(event, reply_token, user_message):
    """處理發布到 Threads 的命令"""
    user_id = event.source.user_id
    user_settings = get_user_settings(user_id)
    if not user_settings or not user_settings.threads_user_id or not user_settings.encrypted_token:
        send_text_reply(reply_token, "喵~ 你還沒告訴我你的Threads秘密呢！(=^･ω･^=)\n用/set_threads_id和/set_threads_token告訴我好嗎？\n我們一起在Threads上玩耍喵！")
        return

    threads_content = user_message[9:]  # 移除 '/threads ' 前綴
    decrypted_token = decrypt_token(user_settings.encrypted_token)
    threads_api = ThreadsAPI(user_settings.threads_user_id, decrypted_token)
    try:
        post_id = threads_api.post_threads(threads_content)
        response = "喵 我們的小秘密已經分享到 Threads 啦 😺\n大家都能看到我們的有趣想法了呢\n要不要去看看有沒有人喜歡呢"
        print(f"發布到 Threads 成功: {post_id}")
    except Exception as e:
        response = "喵 看來 Threads 今天有點小脾氣呢 🙀\n我們待會再試試看好嗎\n現在要不要聊聊你想分享的有趣事情呢"
        print(f"發布到 Threads 時出錯: {str(e)}")
    send_text_reply(reply_token, response)

def agent(query: str) -> tuple[str, str]:
    """自動根據用戶查詢使用正確的工具。"""
    prompt = agent_template + query
    message = [{"role": "user", "content": prompt}]

    try:
        response = generate_chat_response(message)
        print(f"Agent response: {response}")

        available_tools = [
            "g4f_generate_image",
            "rapidapis.ai_text_to_img",
            "search_image_url",
            "horoscope.get_horoscope_response",
            "recommend_videos",
            "chat_completion",
        ]

        for tool in available_tools:
            if re.search(rf"\b{re.escape(tool)}\b", response, re.IGNORECASE):
                match = re.search(rf"{re.escape(tool)}:?\s*(.*)", response, re.IGNORECASE | re.DOTALL)
                input_query = match.group(1).strip() if match else query
                return tool, input_query

        return "chat_completion", query

    except Exception as e:
        print(f"Error in agent function: {e}")
        return "chat_completion", query

def is_url(string: str) -> bool:
    try:
        result = urlparse(string)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def send_image_reply(reply_token, img_url: str) -> None:
    if not img_url:
        send_text_reply(reply_token, "Cannot get image.")
    image_message = ImageSendMessage(original_content_url=img_url, preview_image_url=img_url)
    line_bot_api.reply_message(reply_token, messages=image_message)

def send_text_reply(reply_token, text: str) -> None:
    if not text:
        text = "There're some problem in server."
    text_message = TextSendMessage(text=text)
    line_bot_api.reply_message(reply_token, messages=text_message)

def search_image_url(query: str) -> str:
    img_crawler = ImageCrawler(nums=5)
    img_url = img_crawler.get_url(query)
    if not img_url:
        img_serp = ImageCrawler(engine="serpapi", nums=5, api_key=config.SERPAPI_API_KEY)
        img_url = img_serp.get_url(query)
        print("Used Serpapi search image instead of icrawler.")
    return img_url

@line_app.get("/recommend")
def recommend_from_yt() -> None:
    videos = recommend_videos()
    if videos and "There're something wrong in openai api when call, please try again." not in videos:
        line_bot_api.broadcast(TextSendMessage(text=videos))
        for group_id in config.KNOWN_GROUP_IDS:
            try:
                line_bot_api.push_message(group_id, TextSendMessage(text=videos))
                print(f"成功發送消息到群組 {group_id}")
            except LineBotApiError as e:
                print(f"發送消息到群組 {group_id} 時出錯：{str(e)}")
        print("成功推薦影片")
        return {"status": "success", "message": "推薦了影片。"}
    else:
        print("推薦影片失敗")
        return {"status": "failed", "message": "未獲取推薦影片。"}
