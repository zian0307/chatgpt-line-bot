import json
import re

import requests
from bs4 import BeautifulSoup

from chatgpt_linebot.modules.chat import generate_chat_response
from chatgpt_linebot.prompts import horoscope_template


class Horoscope:
    HOST = "https://www.cosmopolitan.com/tw/horoscopes/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    error_msg = (
        "Cannot get the horoscope, please try again.🥶\n"
    )


    def __init__(self) -> None:
        self.horoscope_urls = self.get_horoscope_urls()

    def get_horoscope_urls(self) -> list:
        """Get all horoscope urls
        Returns
        -------
        horoscope_urls (List[Dict]):
            [
                {'name': '天蠍座', 'url': 'https://www...'},
                {'name': '獅子座', 'url': 'https://www...'},
                ...
            ]
        """
        try:
            response = requests.get(f"{self.HOST}weekly/", headers=self.headers)
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find the script tag containing JSON data
            script_tag = soup.find('script', {'id': 'json-ld'})

            horoscope_urls = []

            if not script_tag:
                return
            # Extract the text content of the script tag
            script_content = script_tag.contents[0]

            # Load the JSON data
            json_data = json.loads(script_content)

            # Extract the information for each zodiac sign
            for item in json_data['itemListElement']:
                name = item['name']
                url = item['url']
                horoscope_urls.append({"name": name, "url": url})

            return horoscope_urls

        except Exception as e:
            print(e)

    def _process_horoscope_response(self, content: str) -> str:
        if not content:
            return f"{self.error_msg}\nContent is None."
        response = generate_chat_response(
            [{"role": "user", "content": horoscope_template+content}]
        )
        return response

    def get_horoscope_response(self, target: str) -> str:
        if not self.horoscope_urls:
            return f"{self.error_msg}\nNot found any horoscope urls."
        
        match_target = re.search(r'(\w{2}座)', target)

        if not match_target:
            return self.error_msg
        
        for horoscope_url in self.horoscope_urls:
            if horoscope_url.get('name') == match_target.group():
                res = requests.get(horoscope_url.get('url'), headers=self.headers)
                soup = BeautifulSoup(res.content, 'html.parser')
                meta_excerpt = soup.find('meta', {'name': 'sailthru.excerpt'})

                if not meta_excerpt:
                    return f"{self.error_msg}\nParse horoscope url failed."

                content = meta_excerpt.get('content')
                return self._process_horoscope_response(content)

        return self.error_msg
