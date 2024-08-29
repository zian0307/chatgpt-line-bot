import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# LINE Bot 設定
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")

# SerpAPI
SERPAPI_API_KEY = os.environ.get('SERPAPI_API_KEY')

# OthersAPI
RAPID = os.environ.get('RAPID')

# YouTube API
YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY')
