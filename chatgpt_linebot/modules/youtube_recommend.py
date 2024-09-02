import random
from typing import Dict, List

from googleapiclient.discovery import build

import config
from chatgpt_linebot.modules.gpt import chat_completion
from chatgpt_linebot.prompts import youtube_recommend_template


def get_youtube_client():
    """獲取 YouTube API 客戶端"""
    youtube_api_key = config.YOUTUBE_API_KEY
    return build("youtube", "v3", developerKey=youtube_api_key)


def get_popular_music_videos(max_results: int = 50) -> List[Dict]:
    """獲取熱門音樂影片"""
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


def format_video_info(video: Dict) -> Dict:
    """格式化影片資訊"""
    return {
        "title": video["snippet"]["title"],
        "channel": video["snippet"]["channelTitle"],
        "url": f"https://www.youtube.com/watch?v={video['id']}",
    }


def recommend_videos() -> str:
    """推薦 YouTube 影片"""
    popular_videos = get_popular_music_videos()
    selected_videos = random.sample(popular_videos, 3)
    video_info = [format_video_info(video) for video in selected_videos]

    prompt = f"{youtube_recommend_template}{video_info}"
    return chat_completion([{"role": "user", "content": prompt}])
