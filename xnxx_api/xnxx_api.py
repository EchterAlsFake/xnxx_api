try:
    from modules.consts import *
    from modules.errors import *
    from modules.search_filters import *
    from base_api.base import Core
    from base_api.modules.download import *
    from base_api.modules.progress_bars import Callback
    from base_api.modules.quality import Quality

except (ModuleNotFoundError, ImportError):
    from .modules.consts import *
    from .modules.errors import *
    from .modules.search_filters import *
    from base_api.base import Core
    from base_api.modules.progress_bars import Callback
    from base_api.modules.download import *


import requests
import json
import html

from bs4 import BeautifulSoup
from functools import cached_property


class Video:
    def __init__(self, url):
        self.url = url
        self.available_m3u8_urls = None
        self.available_qualities = None
        self.script_content = None
        self.html_content = None
        self.metadata_matches = None
        self.json_content = None
        self.session = requests.Session()

        if not REGEX_VIDEO_CHECK.search(self.url):
            raise InvalidUrl("The video URL is invalid!")

        else:
            self.get_base_html()
            self.get_script_content()
            self.get_metadata_matches()
            self.extract_json_from_html()

    def get_base_html(self):
        self.html_content = Core.get_content(url=self.url, headers=None, cookies=None, retries=MAX_RETRIES).decode("utf-8")

    @classmethod
    def is_desired_script(cls, tag):
        if tag.name != "script":
            return False
        script_contents = ['html5player', 'setVideoTitle', 'setVideoUrlLow', 'setVideoUrlHigh']
        return all(content in tag.text for content in script_contents)

    def get_metadata_matches(self):
        soup = BeautifulSoup(self.html_content, 'html.parser')
        metadata_span = soup.find('span', class_='metadata')
        metadata_text = metadata_span.get_text(separator=' ', strip=True)

        # Use a regex to extract the desired strings
        # This regex looks for patterns of text that could represent the data you're interested in
        self.metadata_matches = re.findall(r'(\d+min|\d+p|\d[\d\.,]*\s*[views]*)', metadata_text)

    def get_script_content(self):
        soup = BeautifulSoup(self.html_content, 'lxml')
        target_script = soup.find(self.is_desired_script)
        if target_script:
            self.script_content = target_script.text

        else:
            raise InvalidResponse("Couldn't extract JSON from HTML")

    def extract_json_from_html(self):
        soup = BeautifulSoup(self.html_content, 'lxml')
        # Find the <script> tag with type="application/ld+json"
        script_tag = soup.find('script', {'type': 'application/ld+json'})

        if script_tag:
            json_text = script_tag.string.strip()  # Get the content of the tag as a string
            data = json.loads(json_text)
            self.json_content = data

    @cached_property
    def m3u8_base_url(self):
        return REGEX_VIDEO_M3U8.search(self.script_content).group(1)

    def get_segments(self, quality):

        quality = Core().fix_quality(quality)

        # Some inspiration from PHUB (xD)
        base_url = self.m3u8_base_url
        new_segment = Core().get_m3u8_by_quality(quality, m3u8_base_url=base_url)
        # Split the base URL into components
        url_components = base_url.split('/')

        # Replace the last component with the new segment
        url_components[-1] = new_segment

        # Rejoin the components into the new full URL
        new_url = '/'.join(url_components)
        master_src = self.session.get(url=new_url).text

        urls = [l for l in master_src.splitlines()
                if l and not l.startswith('#')]

        segments = []

        for url in urls:
            url_components[-1] = url
            new_url = '/'.join(url_components)
            segments.append(new_url)

        return segments

    def download(self, quality, output_path, downloader, callback=Callback.text_progress_bar):
        Core().download(video=self, quality=quality, output_path=output_path, callback=callback, downloader=downloader)

    @cached_property
    def title(self) -> str:
        return html.unescape(REGEX_VIDEO_TITLE.search(self.script_content).group(1))

    @cached_property
    def author(self) -> str:
        return REGEX_VIDEO_UPLOADER.search(self.script_content).group(1)

    @cached_property
    def length(self) -> str:
        return self.metadata_matches[0]

    @cached_property
    def highest_quality(self) -> str:
        return self.metadata_matches[1]

    @cached_property
    def views(self) -> str:
        return self.metadata_matches[2]

    @cached_property
    def comment_count(self) -> str:
        return REGEX_VIDEO_COMMENT_COUNT.search(self.html_content).group(1)

    @cached_property
    def likes(self) -> str:
        return REGEX_VIDEO_LIKES.search(self.html_content).group(1)

    @cached_property
    def dislikes(self) -> str:
        return REGEX_VIDEO_DISLIKES.search(self.html_content).group(1)

    @cached_property
    def pornstars(self) -> list:
        pornstar_list = REGEX_VIDEO_PORNSTARS.findall(self.html_content)
        pornstar_list_filtered = []
        for pornstar in pornstar_list:
            pornstar = str(pornstar).replace("+", " ")
            pornstar_list_filtered.append(pornstar)

        return pornstar_list_filtered

    @cached_property
    def tags(self) -> list:
        tags_list = REGEX_VIDEO_KEYWORDS.findall(self.html_content)
        tags_list_filtered = []
        for tag in tags_list:
            tag = str(tag).replace("+", " ")
            tags_list_filtered.append(tag)

        return tags_list_filtered

    @cached_property
    def description(self) -> str:
        return html.unescape(self.json_content["description"])

    @cached_property
    def thumbnail_url(self) -> list:
        return self.json_content["thumbnailUrl"]

    @cached_property
    def publish_date(self) -> str:
        return self.json_content["uploadDate"]

    @cached_property
    def content_url(self) -> str:
        return self.json_content["contentUrl"]


class Search:
    def __init__(self, query: str, upload_time: UploadTime, length: Length, searching_quality: SearchingQuality):
        self.query = self.validate_query(query)
        self.upload_time = upload_time
        self.length = length
        self.searching_quality = searching_quality

    @classmethod
    def validate_query(cls, query):
        return query.replace(" ", "+")

    @cached_property
    def html_content(self):
        # Now this is going to be weird, just don't ask
        return Core().get_content(f"https://www.xnxx.com/search{self.upload_time}{self.length}{self.searching_quality}/{self.query}", headers=HEADERS).decode("utf-8")

    @cached_property
    def total_pages(self):
        return REGEX_SEARCH_TOTAL_PAGES.search(self.html_content).group(1)

    @cached_property
    def videos(self):

        page = 0
        while True:

            if page == 0:
                url = f"https://www.xnxx.com/search{self.upload_time}{self.length}{self.searching_quality}/{self.query}"

            else:
                url = f"https://www.xnxx.com/search{self.upload_time}{self.length}{self.searching_quality}/{self.query}/{page}"

            content = Core().get_content(url, headers=HEADERS).decode("utf-8")
            urls = REGEX_SCRAPE_VIDEOS.findall(content)
            for url_ in urls:
                yield Video(f"https://www.xnxx.com/video-{url_}")

            if int(page) >= int(self.total_pages):
                break

            page += 1


class User:
    def __init__(self, url):
        self.url = url

    @cached_property
    def html_content(self):
        # Now this is going to be weird, just don't ask
        return Core().get_content(f"{self.url}", headers=HEADERS).decode("utf-8")

    @cached_property
    def videos(self):

        page = 0
        while True:
            url = f"{self.url}/videos/best/{page}?from=goldtab"
            content = Core().get_content(url, headers=HEADERS).decode("utf-8")
            print(content)
            urls = REGEX_SCRAPE_VIDEOS.findall(content)

            if not urls:
                break

            else:
                for url_ in urls:
                    yield Video(f"https://www.xnxx.com/video-{url_}")

            page += 1


class Client:

    @classmethod
    def get_video(cls, url):
        return Video(url)

    @classmethod
    def search(cls, query, upload_time: UploadTime = "", length: Length = "", searching_quality: SearchingQuality = ""):
        return Search(query, upload_time, length, searching_quality)

    @classmethod
    def get_user(cls, url):
        return User(url)

client = Client()
user = Client.get_user("https://www.xnxx.com/pornstar/abella-danger")
videos = user.videos
for video in videos:
    print(video.title)
