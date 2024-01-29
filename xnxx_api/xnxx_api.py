try:
    from modules.consts import *
    from modules.locals import *
    from modules.errors import *

except (ModuleNotFoundError, ImportError):
    from .modules.consts import *
    from .modules.locals import *
    from .modules.errors import *

import requests
import json
import html

from bs4 import BeautifulSoup
from functools import cached_property


class Video:
    def __init__(self, url):
        self.url = url
        self.script_content = None
        self.html_content = None
        self.metadata_matches = None
        self.rating_metadata = None
        self.json_content = None
        self.session = requests.Session()

        if not REGEX_VIDEO_CHECK.search(self.url):
            raise InvalidUrl("The video URL is invalid!")

        else:
            self.get_base_html()
            self.get_script_content()
            self.get_metadata_matches()
            self.get_rating_metadata()
            self.extract_json_from_html()
            print(self.script_content)

    def get_base_html(self):
        self.html_content = requests.get(self.url).content.decode("utf-8")

    def get_rating_metadata(self):
        self.rating_metadata = REGEX_VIDEO_RATING.findall(self.html_content)

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
    def title(self) -> str:
        return html.unescape(REGEX_VIDEO_TITLE.search(self.script_content).group(1))

    @cached_property
    def uploader(self) -> str:
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
        return self.rating_metadata[2]

    @cached_property
    def likes(self) -> str:
        return self.rating_metadata[0]

    @cached_property
    def dislikes(self) -> str:
        return self.rating_metadata[1]

    @cached_property
    def pornstars(self) -> list:
        pornstar_list = REGEX_VIDEO_PORNSTARS.findall(self.html_content)
        pornstar_list_filtered = []
        for pornstar in pornstar_list:
            pornstar = str(pornstar).replace("+", " ")
            pornstar_list_filtered.append(pornstar)

        return pornstar_list_filtered

    @cached_property
    def keywords(self) -> list:
        keyword_list = REGEX_VIDEO_KEYWORDS.findall(self.html_content)
        keyword_list_filtered = []
        for keyword in keyword_list:
            keyword = str(keyword).replace("+", " ")
            keyword_list_filtered.append(keyword)

        return keyword_list_filtered

    @cached_property
    def description(self) -> str:
        return html.unescape(self.json_content["description"])

    @cached_property
    def thumbnail_url(self) -> list:
        return self.json_content["thumbnailUrl"]

    @cached_property
    def upload_date(self) -> str:
        return self.json_content["uploadDate"]

    @cached_property
    def content_url(self) -> str:
        return self.json_content["contentUrl"]


class Client:

    @classmethod
    def get_video(cls, url):
        return Video(url)


video = Client().get_video("https://www.xnxx.com/video-mopdd37/im_whirlpool_gibt_die_susse_sau_ihr_allerbestes_-_ist_halt_frau_...._jasmine_rouge")
print(video.description)
print(video.thumbnail_url)
print(video.upload_date)
print(video.content_url)