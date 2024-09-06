from typing import Dict, List
import g4f
from openai import OpenAI
import config
from g4f.client import Client
from chatgpt_linebot.memory import Memory

g4f.debug.logging = False


def generate_chat_response(message: List[Dict]) -> str:
    """使用 OpenAI API 優先,如果失敗則回退到 gpt4free 提供者"""
    try:
        # 嘗試使用 OpenAI API
        client = OpenAI(api_key=config.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=message
        )
        response = response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API 失敗: {e}")
        try:
            # Fallback to g4f if OpenAI API fails
            client = Client()
            response = client.chat.completions.create(
                model="gpt-3.5-turbo", messages=message, ignored=["Cnote", "Aichatos"]
            )
            response = response.choices[0].message.content
        except Exception as e:
            response = (
                "There're something wrong in both OpenAI and g4f APIs, please try again.\n"
                f"{e}"
            )
            print(e)

    return response

def chat_completion(id: int, memory: Memory) -> str:
    """Use OpenAI API via gpt4free providers"""
    response = generate_chat_response(memory.get(id))
    memory.append(id, 'system', response)
    # print(memory.storage)
    return response
