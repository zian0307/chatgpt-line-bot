import requests
from icrawler import ImageDownloader
from icrawler.builtin import GoogleImageCrawler
from serpapi.google_search import GoogleSearch
import config
from bs4 import BeautifulSoup

serpapi_key = config.SERPAPI_API_KEY

class CustomLinkPrinter(ImageDownloader):
    """Only get image urls instead of store
    
    References
    ----------
    [Issue#73](https://github.com/hellock/icrawler/issues/73)
    """
    file_urls = []

    def get_filename(self, task, default_ext):
        file_idx = self.fetched_num + self.file_idx_offset
        return '{:04d}.{}'.format(file_idx, default_ext)

    def download(self, task, default_ext, timeout=5, max_retry=3, overwrite=False, **kwargs):
        file_url = task['file_url']
        filename = self.get_filename(task, default_ext)

        task['success'] = True
        task['filename'] = filename

        if not self.signal.get('reach_max_num'):
            self.file_urls.append(file_url)

        self.fetched_num += 1

        if self.reach_max_num():
            self.signal.set(reach_max_num=True)


class ImageCrawler:
    """Crawl the Image"""
    def __init__(
        self,
        nums: int = 1,
        api_key: str = serpapi_key
    ) -> None:
        self.image_save_path = "./"
        self.nums = nums
        self.api_key = api_key

    def _is_img_url(self, url) -> bool:
        """Check the image url is valid or invalid"""
        try:
            response = requests.head(url)
            content_type = response.headers['content-type']
            return content_type.startswith('image/')
        except (requests.RequestException, KeyError):
            return False

    def _serpapi(self, search_query: str) -> list[str]:
        """Serpapi for google search images"""
        params = {
            "engine": "google_images",
            "q": search_query,
            "location": "Taiwan",
            "hl": "zh-tw",
            "gl": "tw",
            "api_key": self.api_key
        }
        search = GoogleSearch(params)
        results = search.get_dict()
        images = results['images_results']

        return [image['original'] for image in images[:self.nums]]

    def _icrawler(self, search_query: str, prefix_name: str = 'tmp') -> list[str]:
        """Icrawler for google search images (Free)"""
        google_crawler = GoogleImageCrawler(
            downloader_cls=CustomLinkPrinter,
            storage={'root_dir': self.image_save_path},
            parser_threads=4,
            downloader_threads=4
        )

        # TODO: https://github.com/hellock/icrawler/issues/40
        google_crawler.session.verify = False
        google_crawler.downloader.file_urls = []

        google_crawler.crawl(
            keyword=search_query,
            max_num=self.nums,
            file_idx_offset=0
        )
        img_urls = google_crawler.downloader.file_urls
        print(f'Get image urls: {img_urls}')

        return img_urls[:self.nums]

    def _beautifulsoup_search(self, search_query: str) -> list[str]:
        """BeautifulSoup and Requests for Google Image Search"""
        search_url = f"https://www.google.com/search?hl=zh-TW&tbm=isch&q={search_query}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }

        response = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        img_tags = soup.find_all('img')

        img_urls = []
        for img in img_tags:
            img_url = img.get('src')
            if img_url and img_url.startswith('http'):
                img_urls.append(img_url)
                if len(img_urls) >= self.nums:
                    break

        return img_urls

    def get_url(self, search_query: str) -> str:
        engines = ['serpapi', 'icrawler', 'beautifulsoup']
        
        for engine in engines:
            try:
                if engine == 'serpapi':
                    urls = self._serpapi(search_query)
                elif engine == 'icrawler':
                    urls = self._icrawler(search_query)
                elif engine == 'beautifulsoup':
                    urls = self._beautifulsoup_search(search_query)
                
                for url in urls:
                    if self._is_img_url(url):
                        return url
            
            except Exception as e:
                print(f'\033[31m使用 {engine} 時發生錯誤: {e}')
                continue  # 如果當前引擎失敗，繼續嘗試下一個引擎
        
        print('\033[31m所有搜尋引擎都失敗了')
        return None  # 如果所有引擎都失敗，返回 None