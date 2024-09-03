from chatgpt_linebot.modules.chat import generate_chat_response


if __name__ == '__main__':
   print(generate_chat_response([{"role": "user", "content": "Hello"}]))