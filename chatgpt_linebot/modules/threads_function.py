import requests
import json

class ThreadsAPI:
    BASE_URL = "https://graph.threads.net/v1.0"

    def __init__(self, user_id, long_lived_token):
        self.user_id = user_id
        self.access_token = long_lived_token

    def create_container(self, media_type, text, image_url=None):
        endpoint = f"{self.BASE_URL}/{self.user_id}/threads"
        data = {
            "media_type": media_type,
            "text": text,
            "access_token": self.access_token
        }
        if image_url:
            data["image_url"] = image_url

        response = requests.post(endpoint, data=data)
        return response.json().get("id")

    def publish_container(self, container_id):
        endpoint = f"{self.BASE_URL}/{self.user_id}/threads_publish"
        data = {
            "creation_id": container_id,
            "access_token": self.access_token
        }
        response = requests.post(endpoint, data=data)
        return response.json().get("id")

    def post_thread(self, text, media_type="TEXT", image_url=None):
        container_id = self.create_container(media_type, text, image_url)
        return self.publish_container(container_id)

    def reply_to_thread(self, reply_text, thread_id):
        endpoint = f"{self.BASE_URL}/me/threads"
        data = {
            "media_type": "TEXT",
            "text": reply_text,
            "reply_to_id": thread_id,
            "access_token": self.access_token
        }
        response = requests.post(endpoint, data=data)
        container_id = response.json().get("id")
        return self.publish_container(container_id)

def main():
    # 請替換以下變數為您的實際值
    USER_ID = "26908317025426272"
    LONG_LIVED_TOKEN = "THQWJWNy04VUNHSlAtR25RSXVMOVhFSHM2ZAFRFbEZAKYktOZA3lOYnV5MXczTlJ0LUxNcGJuQTJRTXhaY2RvY2h3V1p0OVREeW1VeFVfWTRLNnFvRDVsQnI4ODh4VmVPSlhtaFdZATVhCSXRRN2tTUXZA5LVhPaHd1THo1QkEZD"

    api = ThreadsAPI(USER_ID, LONG_LIVED_TOKEN)

    # 發布純文字帖子
    text_post_id = api.post_thread("大家好，這是一個測試帖子！")
    print(f"純文字帖子已發布，ID: {text_post_id}")

    # 發布帶圖片的帖子
    image_post_id = api.post_thread("這是一張美麗的圖片！", "IMAGE", "https://example.com/beautiful_image.jpg")
    print(f"帶圖片的帖子已發布，ID: {image_post_id}")

    # 回覆帖子
    reply_id = api.reply_to_thread("這是一個測試回覆！", text_post_id)
    print(f"回覆已發布，ID: {reply_id}")

if __name__ == "__main__":
    main()