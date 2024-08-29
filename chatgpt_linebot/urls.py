import sys
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, Request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *

from chatgpt_linebot.memory import Memory
from chatgpt_linebot.modules import (
    Horoscope,
    ImageCrawler,
    RapidAPIs,
    chat,
    chat_completion,
    g4f_generate_image,
    recommend_videos,
)
from chatgpt_linebot.prompts import agent_template, girlfriend
from chatgpt_linebot.modules.threads_function import ThreadsAPI
from chatgpt_linebot.database import get_user_settings, save_user_settings, decrypt_token

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
    """LINE Bot webhook callback

    Args:
        request (Request): Request Object.

    Raises:
        HTTPException: Invalid Signature Error

    Returns:
        str: OK
    """
    signature = request.headers["X-Line-Signature"]
    body = await request.body()

    # handle webhook body
    try:
        handler.handle(body.decode(), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Missing Parameter")
    return "OK"


def is_url(string: str) -> bool:
    try:
        result = urlparse(string)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def agent(query: str) -> tuple[str]:
    """Auto use correct tool by user query."""
    prompt = agent_template + query
    message = [{'role': 'user', 'content': prompt}]

    tool, input = chat(message).split(', ')

    print(f"""
    Agent
    =========================================
    Query: {query}
    Tool: {tool}
    Input: {input}
    """)

    return tool, input


def search_image_url(query: str) -> str:
    """Fetches image URL from different search sources."""
    img_crawler = ImageCrawler(nums=5)
    img_url = img_crawler.get_url(query)
    if not img_url:
        img_serp = ImageCrawler(engine='serpapi', nums=5, api_key=config.SERPAPI_API_KEY)
        img_url = img_serp.get_url(query)
        print('Used Serpapi search image instead of icrawler.')
    return img_url


def send_image_reply(reply_token, img_url: str) -> None:
    """Sends an image message to the user."""
    if not img_url:
        send_text_reply(reply_token, 'Cannot get image.')
    image_message = ImageSendMessage(original_content_url=img_url, preview_image_url=img_url)
    line_bot_api.reply_message(reply_token, messages=image_message)


def send_text_reply(reply_token, text: str) -> None:
    """Sends a text message to the user."""
    if not text:
        text = "There're some problem in server."
    text_message = TextSendMessage(text=text)
    line_bot_api.reply_message(reply_token, messages=text_message)


@handler.add(MessageEvent, message=(TextMessage))
def handle_message(event) -> None:
    """處理用戶發送的消息

    Args:
        event (LINE Event Object): LINE 事件對象

    這個函數處理以下幾種命令:
    1. /set_threads_id: 設置用戶的 Threads ID
    2. /set_threads_token: 設置用戶的 Threads 訪問令牌
    3. /threads: 發布內容到 Threads
    """
    # 獲取回覆令牌和用戶消息
    reply_token = event.reply_token
    user_message = event.message.text

    # 獲取消息來源類型和ID
    source_type = event.source.type
    source_id = getattr(event.source, f"{source_type}_id", None)

    # 如果是用戶發送的消息,打印用戶名和消息內容
    if source_type == 'user':
        user_name = line_bot_api.get_profile(source_id).display_name
        print(f'{user_name}: {user_message}')
    # 如果是群組消息,只處理以 @chat 開頭的消息
    else:
        if not user_message.startswith('@chat'):
            return
        else:
            user_message = user_message.replace('@chat', '')

    # 處理設置 Threads 用戶 ID 的命令
    if user_message.startswith('/set_threads_id '):
        user_id = event.source.user_id
        threads_user_id = user_message[16:].strip()
        user_settings = get_user_settings(user_id)
        if user_settings:
            save_user_settings(user_id, threads_user_id, decrypt_token(user_settings.encrypted_token))
        else:
            save_user_settings(user_id, threads_user_id, '')
        send_text_reply(reply_token, f"已設定 Threads 用戶 ID: {threads_user_id}")
        return

    # 處理設置 Threads 訪問令牌的命令
    if user_message.startswith('/set_threads_token '):
        user_id = event.source.user_id
        threads_token = user_message[19:].strip()
        user_settings = get_user_settings(user_id)
        if user_settings:
            save_user_settings(user_id, user_settings.threads_user_id, threads_token)
        else:
            save_user_settings(user_id, '', threads_token)
        send_text_reply(reply_token, "已設定並加密 Threads 訪問令牌")
        return

    # 處理發布到 Threads 的命令
    if user_message.startswith('/threads '):
        user_id = event.source.user_id
        user_settings = get_user_settings(user_id)
        if not user_settings or not user_settings.threads_user_id or not user_settings.encrypted_token:
            send_text_reply(reply_token, "請先設定您的 Threads 用戶 ID 和訪問令牌。使用 /set_threads_id 和 /set_threads_token 命令。")
            return

        threads_content = user_message[9:]  # 移除 '/threads ' 前綴
        decrypted_token = decrypt_token(user_settings.encrypted_token)
        threads_api = ThreadsAPI(user_settings.threads_user_id, decrypted_token)
        try:
            post_id = threads_api.post_threads(threads_content)
            response = f"已成功發布到Threads，帖子ID: {post_id}"
        except Exception as e:
            response = f"發布到Threads時出錯: {str(e)}"
        send_text_reply(reply_token, response)
        return
    
    tool, input_query = agent(user_message)

    # 如果是聊天完成,添加角色設定並更新記憶
    if tool in ['chat_completion']:
        input_query = f"{girlfriend}:\n {input_query}"
        memory.append(source_id, 'user', f"{girlfriend}:\n {user_message}")

    try:
        # 根據選擇的工具生成回覆
        if tool in ['chat_completion']:
            response = chat_completion(source_id, memory)
        else:
            response = eval(f"{tool}('{input_query}')")

        # 發送圖片或文字回覆
        if is_url(response):
            send_image_reply(reply_token, response)
        else:
            send_text_reply(reply_token, response)

    except Exception as e:
        # 發送錯誤信息
        send_text_reply(reply_token, e)

@line_app.get("/recommend")
def recommend_from_yt() -> None:
    """Line Bot Broadcast

    Descriptions
    ------------
    Recommend youtube videos to all followed users.
    (Use cron-job.org to call this api)

    References
    ----------
    https://www.cnblogs.com/pungchur/p/14385539.html
    https://steam.oxxostudio.tw/category/python/example/line-push-message.html
    """
    videos = recommend_videos()

    if videos and "There're something wrong in openai api when call, please try again." not in videos:
        line_bot_api.broadcast(TextSendMessage(text=videos))

        # Push message to group via known group (event.source.group_id)
        known_group_ids = [
            'C6d-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
            'Ccc-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
            'Cbb-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
        ]
        for group_id in known_group_ids:
            line_bot_api.push_message(group_id, TextSendMessage(text=videos))

        print('Successfully recommended videos')
        return {"status": "success", "message": "recommended videos."}

    else:
        print('Failed recommended videos')
        return {"status": "failed", "message": "no get recommended videos."}
