import random
from datetime import date
from typing import Dict, List
import hashlib

from googleapiclient.discovery import build

import config
from chatgpt_linebot.modules.chat import generate_chat_response
from chatgpt_linebot.prompts import youtube_recommend_template


def get_youtube_client():
    """獲取 YouTube API 客戶端"""
    try:
        youtube_api_key = config.YOUTUBE_API_KEY
        return build("youtube", "v3", developerKey=youtube_api_key)
    except Exception as e:
        print(f"獲取 YouTube API 客戶端失敗: {e}")
        raise


def get_popular_music_videos(max_results: int = 50) -> List[Dict]:
    """獲取熱門音樂影片"""
    try:
        youtube = get_youtube_client()
        request = youtube.videos().list(
            part="snippet",
            chart="mostPopular",
            regionCode="TW",
            videoCategoryId="10",
            maxResults=max_results,
        )
        response = request.execute()
        return response["items"]
    except Exception as e:
        print(f"獲取熱門音樂影片失敗: {e}")
        return []


def format_video_info(video: Dict) -> Dict:
    """格式化影片資訊"""
    try:
        return {
            "title": video["snippet"]["title"],
            "channel": video["snippet"]["channelTitle"],
            "url": f"https://www.youtube.com/watch?v={video['id']}",
        }
    except KeyError as e:
        print(f"格式化影片資訊失敗: 缺少鍵 {e}")
        return {}


def get_daily_seed(date_str: str) -> int:
    """根據日期字符串生成一個穩定的種子"""
    return int(hashlib.md5(date_str.encode()).hexdigest(), 16)


def recommend_videos() -> str:
    """推薦 YouTube 影片"""
    try:
        popular_videos = get_popular_music_videos()
        if not popular_videos:
            return "無法獲取熱門音樂影片。"

        # 使用當前日期作為種子
        today = date.today().isoformat()
        daily_seed = get_daily_seed(today)
        
        # 使用日期種子來選擇影片
        random.seed(daily_seed)
        selected_video = random.choice(popular_videos)
        video_info = format_video_info(selected_video)

        prompt = f"{youtube_recommend_template}{[video_info]}"
        return generate_chat_response([{"role": "user", "content": prompt}])

    except Exception as e:
        print(f"推薦影片失敗: {e}")
        return "推薦影片時發生錯誤。"
