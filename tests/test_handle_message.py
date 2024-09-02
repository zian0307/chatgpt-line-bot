import unittest
from unittest.mock import Mock
from chatgpt_linebot.urls import handle_message

class TestHandleMessage(unittest.TestCase):
    def setUp(self):
        # 創建一個模擬的 LINE Event Object
        self.mock_event = Mock()
        self.mock_event.message.text = "測試消息"

    def test_handle_message_normal(self):
        # 測試正常消息處理
        handle_message(self.mock_event)
        # 由於函數沒有返回值，我們需要檢查預期的副作用
        # 例如，檢查是否調用了某個方法來回覆消息
        self.mock_event.reply_token.reply_message.assert_called_once()

    def test_handle_message_empty(self):
        # 測試空消息
        self.mock_event.message.text = ""
        handle_message(self.mock_event)
        # 檢查空消息的處理方式，可能是特定的回覆或者不回覆
        # 這裡的斷言需要根據實際的處理邏輯來編寫

    def test_handle_message_long(self):
        # 測試超長消息
        self.mock_event.message.text = "a" * 1000  # 假設1000字符為超長消息
        handle_message(self.mock_event)
        # 檢查超長消息的處理方式

    # 可以添加更多測試用例...

if __name__ == '__main__':
    unittest.main()
