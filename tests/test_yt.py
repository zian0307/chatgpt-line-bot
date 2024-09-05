import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatgpt_linebot.modules.youtube_recommend import recommend_videos

if __name__ == '__main__':
    print(recommend_videos())