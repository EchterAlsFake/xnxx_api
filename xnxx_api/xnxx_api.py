from base_api.modules.type_hints import DownloadReport

try:
    from modules.consts import *
    from modules.errors import *
    from modules.type_hints import *
    from modules.search_filters import *

except (ModuleNotFoundError, ImportError):
    from .modules.consts import *
    from .modules.errors import *
    from .modules.type_hints import *
    from .modules.search_filters import *

import os
import re
import html
import json
import logging
import argparse
import threading
import math

from bs4 import BeautifulSoup
from typing import AsyncGenerator
from functools import cached_property
from curl_cffi import Response, AsyncSession
from base_api.base import BaseCore, setup_logger, Helper
from base_api.modules.static_functions import str_to_bool
from base_api.modules.errors import NetworkingError, InvalidProxy, BotProtectionDetected, UnknownError, ResourceGone

try:
    import lxml
    parser = "lxml"

except (ModuleNotFoundError, ImportError):
    parser = "html.parser"


async def on_error(url: str, error: Exception, attempt: int) -> bool:
    print(f"URL: {url}, ERROR: {error}, Attempt: {attempt}")

    if isinstance(error, ResourceGone):
        return False

    return True


async def get_html_content(core: BaseCore, url: str) -> str | None | dict:
    # What should I do here?
    try:
        content = await core.fetch(url)
        if isinstance(content, str):
            return content

        if isinstance(content, Response):
            raise RegionBlocked(f"The Video: {url} is not available in your country!")

    except NetworkingError as e:
        raise NetworkError(str(e)) from e

    except InvalidProxy as e:
        raise ProxyError(str(e)) from e

    except BotProtectionDetected as e:
        raise BotDetection(str(e)) from e

    except UnknownError as e:
        raise UnknownNetworkError(str(e)) from e



class Video:
    def __init__(self, url: str, core: BaseCore, html_content: str | None = None):
        self.url = url
        self.core = core
        self.available_m3u8_urls = None
        self.script_content = None
        self.html_content = html_content
        self.metadata_matches = None
        self.json_content = None
        self._soup: BeautifulSoup | None = None
        self.logger = setup_logger(name="XNXX API - [Video]", log_file=None, level=logging.CRITICAL)

    def enable_logging(self, log_file, level, log_ip: str | None = None, log_port: int | None = None):
        self.logger = setup_logger(name="XNXX API - [Video]", log_file=log_file, level=level, http_ip=log_ip, http_port=log_port)

    async def init(self):
        if not REGEX_VIDEO_CHECK.search(self.url):
            raise InvalidUrl("The video URL is invalid!")

        if not self.html_content:
            self.html_content = await get_html_content(core=self.core, url=self.url)

        self._soup = BeautifulSoup(self.html_content, parser)

        self.get_script_content()
        self.get_metadata_matches()
        self.extract_json_from_html()
        return self

    @property
    def soup(self) -> BeautifulSoup:
        if not self._soup:
            raise ValueError("You probably forgot to call init")

        return self._soup

    @classmethod
    def is_desired_script(cls, tag):
        if tag.name != "script":
            return False
        script_contents = ['html5player', 'setVideoTitle', 'setVideoUrlLow']
        return all(content in tag.text for content in script_contents)

    def get_metadata_matches(self) -> None:
        metadata_span = self.soup.find('span', class_='metadata')
        metadata_text = metadata_span.get_text()

        # Use a regex to extract the desired strings
        self.metadata_matches = re.findall(r'(\d+min|\d+p|\d[\d.,]*\s*[views]*)', metadata_text)

    def get_script_content(self) -> None:
        target_script = self.soup.find(self.is_desired_script)
        if target_script:
            self.script_content = target_script.text

        else:
            raise InvalidResponse("Couldn't extract JSON from HTML")

    def extract_json_from_html(self) -> None:
        # Find the <script> tag with type="application/ld+json"
        script_tag = self.soup.find('script', {'type': 'application/ld+json'})

        if script_tag:
            json_text = script_tag.string.strip()  # Get the content of the tag as a string
            data = json.loads(json_text)
            self.json_content = data

    @cached_property
    def m3u8_base_url(self) -> str:
        """
        The m3u8 base URL is a file that contains the list of segments (.ts files) for the different resolutions.
        This is basically the whole magic for all my APIs :)
        :return: (str) The m3u8 base URL
        """
        return REGEX_VIDEO_M3U8.search(self.script_content).group(1)

    async def get_segments(self, quality: str) -> list:
        return await self.core.get_segments(quality=quality, m3u8_url_master=self.m3u8_base_url)

    async def download(self, quality, path="./", callback: callback_hint=None, no_title=False, remux: bool = False,
                 callback_remux: callback_hint =None, start_segment: int = 0, stop_event: threading.Event | None = None,
                 segment_state_path: str | None = None, segment_dir: str | None = None,
                 return_report: bool = False, cleanup_on_stop: bool = True, keep_segment_dir: bool = False
                 ) -> bool | DownloadReport:
        """
        :param callback:
        :param quality:
        :param path:
        :param no_title:
        :param remux:
        :param callback_remux:
        :param start_segment:
        :param stop_event:
        :param segment_state_path:
        :param segment_dir:
        :param return_report:
        :param cleanup_on_stop:
        :param keep_segment_dir:
        :return:
        """
        if not no_title:
            path = os.path.join(path, f"{self.title}.mp4")

        return await self.core.download(video=self, quality=quality, path=path, callback=callback, remux=remux,
                           callback_remux=callback_remux, start_segment=start_segment, stop_event=stop_event,
                           segment_state_path=segment_state_path, segment_dir=segment_dir, return_report=return_report,
                           cleanup_on_stop=cleanup_on_stop, keep_segment_dir=keep_segment_dir)

    @cached_property
    def title(self) -> str:
        return html.unescape(REGEX_VIDEO_TITLE.search(self.script_content).group(1))

    @cached_property
    def author(self) -> str:
        return REGEX_VIDEO_UPLOADER.search(self.script_content).group(1)

    @cached_property
    def length(self) -> str:
        length = self.metadata_matches[0]
        length = str(length).strip("min")
        return length

    @cached_property
    def highest_quality(self) -> str:
        return self.metadata_matches[1]

    @cached_property
    def views(self) -> str:
        try:
            views = self.metadata_matches[2]

        except IndexError:
            views = self.metadata_matches[1]

        return views

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


class Search(Helper):
    def __init__(self, query: str, core: BaseCore, upload_time: str | UploadTime, length: str | Length, searching_quality:
                                                str | SearchingQuality, mode: str | Mode):
        super().__init__(core, video_constructor=Video)

        self.core = core
        self.query = self.validate_query(query)
        self.upload_time = upload_time
        self.length = length
        self.searching_quality = searching_quality
        self.mode = mode
        self.html_content: str | None | dict = None
        self.logger = setup_logger(name="XNXX API - [Search]", log_file=None, level=logging.CRITICAL)

    def enable_logging(self, log_file, level, log_ip: str | None = None, log_port: int | None = None):
        self.logger = setup_logger(name="XNXX API - [Search]", log_file=log_file, level=level, http_ip=log_ip, http_port=log_port)

    @classmethod
    def validate_query(cls, query):
        return query.replace(" ", "+")

    async def init(self):
        if not self.html_content:
            self.html_content = await get_html_content(core=self.core, url=f"https://www.xnxx.com/search{self.mode}{self.upload_time}{self.length}{self.searching_quality}/{self.query}")

        assert isinstance(self.html_content, str)
        return self

    @cached_property
    def total_pages(self) -> str:
        return REGEX_SEARCH_TOTAL_PAGES.search(self.html_content).group(1)

    async def videos(self, pages_concurrency: int | None = None, videos_concurrency: int | None = None,  pages: int = 0,
                     on_video_error: on_error_hint = on_error,
                     on_page_error: on_error_hint = None
                     ) -> AsyncGenerator[Video, None]:
        self.url = f"https://www.xnxx.com/search{self.mode}{self.upload_time}{self.length}{self.searching_quality}/{self.query}"

        if pages >= int(self.total_pages):
            self.logger.warning(f"You want to fetch: {pages}, but only: {self.total_pages} are available. Reducing!")
            pages = int(self.total_pages)

        page_urls = [self.url]
        page_urls.extend([f"{self.url}/{page}" for page in range(1, int(pages))])
        videos_concurrency = (videos_concurrency or self.core.configuration.videos_concurrency)
        pages_concurrency = pages_concurrency or self.core.configuration.pages_concurrency
        assert videos_concurrency and pages_concurrency
        async for video in self.iterator(target_page_urls=page_urls, max_video_concurrency=videos_concurrency,
                                 max_page_concurrency=pages_concurrency, video_link_extractor=extractor_html,
                                         on_video_error=on_video_error, on_page_error=on_page_error):
            if isinstance(video, Video):
                yield video

class User(Helper):
    def __init__(self, url: str, core: BaseCore):
        super().__init__(core, video_constructor=Video)
        self.url = url
        self.core = core
        self.content: str | None | dict = None
        self._base_json: None | dict = None
        self.logger = setup_logger(name="XNXX API - [User]", log_file=None, level=logging.CRITICAL)

    def enable_logging(self, file, level, log_ip: str | None = None, log_port: int | None = None):
        self.logger = setup_logger(name="XNXX API - [User]", log_file=file, level=level, http_ip=log_ip, http_port=log_port)

    async def init(self):
        if not self.content:
            self.content = await get_html_content(core=self.core, url=self.url)

        assert isinstance(self.content, str)

        url = f"{self.url}/videos/best/0"
        content = await get_html_content(core=self.core, url=url)
        assert isinstance(content, str)
        self._base_json = json.loads(html.unescape(content))

        return self

    @cached_property
    def base_json(self):
        if not self._base_json:
            raise ValueError("You probably forgot to call init")

        return self._base_json

    async def videos(self, videos_concurrency: int | None = None, pages_concurrency: int | None = None,
               pages: int = 0, on_video_error: on_error_hint = on_error, on_page_error: on_error_hint = None
                     ) -> AsyncGenerator[Video, None]:

        if pages >= self.total_pages:
            self.logger.warning(f"You are trying to fetch more pages than there are... Reducing to: {self.total_pages}")
            pages = int(self.total_pages)

        page_urls = [f"{self.url}/videos/best/{page}" for page in range(pages)]
        videos_concurrency = videos_concurrency or self.core.configuration.videos_concurrency
        pages_concurrency = pages_concurrency or self.core.configuration.pages_concurrency
        assert videos_concurrency and pages_concurrency
        async for video in self.iterator(target_page_urls=page_urls, max_video_concurrency=videos_concurrency,
                                 max_page_concurrency=pages_concurrency, video_link_extractor=extractor_html,
                                         on_video_error=on_video_error, on_page_error=on_page_error):
            if isinstance(video, Video):
                yield video


    @cached_property
    def total_videos(self) -> int:
        return int(self.base_json["nb_videos"])

    @cached_property
    def total_pages(self) -> int:
        return int(math.ceil(self.total_videos / int(self.base_json["nb_per_page"])))

    @cached_property
    def total_video_views(self) -> str:
        return REGEX_MODEL_TOTAL_VIDEO_VIEWS.search(self.content).group(1)


class Client:
    def __init__(self, core: BaseCore = BaseCore()):
        self.core = core
        self.core.initialize_session()
        assert isinstance(self.core.session, AsyncSession)
        self.core.session.headers.update({"Referer": "https://www.xnxx.com/"})

    async def get_video(self, url) -> Video:
        """
        :param url: (str) The URL of the video
        :return: (Video) The video object
        """
        video = Video(url, core=self.core)
        return await video.init()

    async def search(self, query: str, upload_time: str | UploadTime = "", length: str | Length = "",
               searching_quality: str | SearchingQuality = "", mode: str | Mode = "") -> Search:
        """
        :param query:
        :param upload_time:
        :param length:
        :param searching_quality:
        :param mode:
        :return: (Search) the search object
        """
        search = Search(query=query, core=self.core, upload_time=upload_time, length=length,
        searching_quality=searching_quality, mode=mode)
        return await search.init()

    async def get_user(self, url: str) -> User:
        """
        :param url: (str) The user URL
        :return: (User) The User object
        """
        user = User(url, core=self.core)
        return await user.init()


async def main():
    parser = argparse.ArgumentParser(description="API Command Line Interface")
    parser.add_argument("--download", metavar="URL (str)", type=str, help="URL to download from")
    parser.add_argument("--quality", metavar="best,half,worst", type=str, help="The video quality (best,half,worst)", required=True)
    parser.add_argument("--file", metavar="Source to .txt file", type=str, help="(Optional) Specify a file with URLs (separated with new lines)")
    parser.add_argument("--output", metavar="Output directory", type=str, help="The output path (with filename)", required=True)
    parser.add_argument("--no-title", metavar="True,False", type=str, help="Whether to apply video title automatically to output path or not", required=True)

    args = parser.parse_args()
    no_title = str_to_bool(args.no_title)

    if args.download:
        client = Client()
        video = await client.get_video(args.download)
        await video.download(quality=args.quality, path=args.output, no_title=no_title)

    if args.file:
        videos = []
        client = Client()

        with open(args.file, "r") as file:
            content = file.read().splitlines()

        for url in content:
            videos.append(await client.get_video(url))

        for video in videos:
            await video.download(quality=args.quality, path=args.output, downloader=args.downloader, no_title=no_title)


if __name__ == "__main__":
    main()
