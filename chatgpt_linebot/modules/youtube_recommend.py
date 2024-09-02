import random
from typing import Dict, List
import logging

from googleapiclient.discovery import build

import config
from chatgpt_linebot.modules.gpt import chat_completion
from chatgpt_linebot.prompts import youtube_recommend_template

# 設定日誌
logging.basicConfig(level=logging.DEBUG)

def get_youtube_client():
    """獲取 YouTube API 客戶端"""
    try:
        youtube_api_key = config.YOUTUBE_API_KEY
        return build("youtube", "v3", developerKey=youtube_api_key)
    except Exception as e:
        logging.error(f"獲取 YouTube API 客戶端失敗: {e}")
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
        logging.error(f"獲取熱門音樂影片失敗: {e}")
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
        logging.error(f"格式化影片資訊失敗: 缺少鍵 {e}")
        return {}

def recommend_videos() -> str:
    """推薦 YouTube 影片"""
    try:
        popular_videos = get_popular_music_videos()
        if not popular_videos:
            return "無法獲取熱門音樂影片。"

        selected_videos = random.sample(popular_videos, 3)
        video_info = [format_video_info(video) for video in selected_videos]

        prompt = f"{youtube_recommend_template}{video_info}"
        return chat_completion([{"role": "user", "content": prompt}])
    except Exception as e:
        logging.error(f"推薦影片失敗: {e}")
        return "推薦影片時發生錯誤。"
