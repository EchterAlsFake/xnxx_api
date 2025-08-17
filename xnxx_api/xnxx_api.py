try:
    from modules.consts import *
    from modules.errors import *
    from modules.search_filters import *

except (ModuleNotFoundError, ImportError):
    from .modules.consts import *
    from .modules.errors import *
    from .modules.search_filters import *

import os
import html
import json
import logging
import argparse
import traceback

from httpx import Response
from bs4 import BeautifulSoup
from functools import cached_property
from typing import Union, Generator, Optional
from base_api.modules.config import RuntimeConfig
from base_api.base import BaseCore, Callback, setup_logger
from concurrent.futures import ThreadPoolExecutor, as_completed


class ErrorVideo:
    """Drop-in-ish stand-in that raises when accessed."""
    def __init__(self, url: str, err: Exception):
        self.url = url
        self._err = err

    def __getattr__(self, _):
        # Any attribute access surfaces the original error
        raise self._err


class Helper:
    def __init__(self, core: BaseCore):
        self.core = core
        self.url = None

    def _get_video(self, url: str):
        return Video(url, core=self.core)

    def _make_video_safe(self, url: str):
        try:
            return Video(url, core=self.core)
        except Exception as e:
            return ErrorVideo(url, e)


    def build_url(self, base_url: str, is_user: bool, is_goldtab: bool, page: int):
        if is_user:
            base_url = f"{base_url}/videos/best/{page}"

        if is_goldtab:
            base_url = f"{base_url}?from_goldtab"

        else:
            base_url = f"{base_url}/{page}"

        return base_url

    def iterator(self, max_workers: int = 20, pages: int = 0, from_goldtab=False, user=False,
                 extractor_function = None):
        if pages == 0:
            pages = 99

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for page in range(pages):
                url = self.build_url(base_url=self.url, is_user=user, is_goldtab=from_goldtab, page=page)

                print(f"Fetching: {url}")
                content = self.core.fetch(url)

                if isinstance(content, Response):
                    return

                video_urls = extractor_function(content=content)

                if video_urls is False:
                    return

                futures = [executor.submit(self._make_video_safe, url) for url in video_urls]
                for future in as_completed(futures):
                    yield future.result()


class Video:
    def __init__(self, url, core: Optional[BaseCore] = None):
        self.url = url
        self.core = core
        self.available_m3u8_urls = None
        self.script_content = None
        self.html_content = None
        self.metadata_matches = None
        self.json_content = None
        self.logger = setup_logger(name="XNXX API - [Video]", log_file=None, level=logging.CRITICAL)

        if not REGEX_VIDEO_CHECK.search(self.url):
            raise InvalidUrl("The video URL is invalid!")

        else:
            self.get_base_html()
            self.get_script_content()
            self.get_metadata_matches()
            self.extract_json_from_html()

    def enable_logging(self, log_file, level, log_ip: str = None, log_port: int = None):
        self.logger = setup_logger(name="XNXX API - [Video]", log_file=log_file, level=level, http_ip=log_ip, http_port=log_port)

    def get_base_html(self) -> None:
        self.html_content = self.core.fetch(url=self.url)
        if isinstance(self.html_content, Response):
            raise RegionBlocked(f"The Video: {self.url} is not available in your country!")

    @classmethod
    def is_desired_script(cls, tag):
        if tag.name != "script":
            return False
        script_contents = ['html5player', 'setVideoTitle', 'setVideoUrlLow']
        return all(content in tag.text for content in script_contents)

    def get_metadata_matches(self) -> None:
        soup = BeautifulSoup(self.html_content, 'html.parser')
        metadata_span = soup.find('span', class_='metadata')
        metadata_text = metadata_span.get_text()

        # Use a regex to extract the desired strings
        self.metadata_matches = re.findall(r'(\d+min|\d+p|\d[\d.,]*\s*[views]*)', metadata_text)

    def get_script_content(self) -> None:
        soup = BeautifulSoup(self.html_content, "html.parser")
        target_script = soup.find(self.is_desired_script)
        if target_script:
            self.script_content = target_script.text

        else:
            raise InvalidResponse("Couldn't extract JSON from HTML")

    def extract_json_from_html(self) -> None:
        soup = BeautifulSoup(self.html_content, "html.parser")
        # Find the <script> tag with type="application/ld+json"
        script_tag = soup.find('script', {'type': 'application/ld+json'})

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

    def get_segments(self, quality: str) -> list:
        return self.core.get_segments(quality=quality, m3u8_url_master=self.m3u8_base_url)

    def download(self, quality: str, downloader: str, path: str = "./", callback=Callback.text_progress_bar,
                 no_title: bool = False, remux: bool = False, callback_remux = None) -> bool:

        if no_title is False:
            path = os.path.join(path, f"{self.title}.mp4")

        try:
            self.core.download(video=self, quality=quality, path=path, callback=callback, downloader=downloader, remux=remux,
                               callback_remux=callback_remux)
            return True

        except Exception:
            error = traceback.format_exc()
            self.logger.error(error)
            return False

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
    def __init__(self, query: str, core: Optional[BaseCore], upload_time: Union[str, UploadTime], length: Union[str, Length], searching_quality:
                                                Union[str, SearchingQuality], mode: Union[str, Mode]):
        super().__init__(core)

        self.core = core
        self.query = self.validate_query(query)
        self.upload_time = upload_time
        self.length = length
        self.searching_quality = searching_quality
        self.mode = mode
        self.logger = setup_logger(name="XNXX API - [Search]", log_file=None, level=logging.CRITICAL)

    def enable_logging(self, log_file, level, log_ip: str = None, log_port: int = None):
        self.logger = setup_logger(name="XNXX API - [Search]", log_file=log_file, level=level, http_ip=log_ip, http_port=log_port)

    @classmethod
    def validate_query(cls, query):
        return query.replace(" ", "+")

    @cached_property
    def html_content(self) -> str:
        # Now this is going to be weird, just don't ask
        return self.core.fetch(f"https://www.xnxx.com/search{self.mode}{self.upload_time}{self.length}{self.searching_quality}/{self.query}")

    @cached_property
    def total_pages(self) -> str:
        return REGEX_SEARCH_TOTAL_PAGES.search(self.html_content).group(1)

    def videos(self, max_workers: int = 20, pages: int = 0) -> Generator[Video, None, None]:
        def _extractor(content):
            urls = REGEX_SCRAPE_VIDEOS.findall(content)
            video_urls = []
            for url_ in urls:
                if not "THUMBNUM" in url_:
                    video_urls.append(f"https://www.xnxx.com/video-{url_}")

            return video_urls

        self.url = f"https://www.xnxx.com/search{self.mode}{self.upload_time}{self.length}{self.searching_quality}/{self.query}"
        yield from self.iterator(max_workers=max_workers, pages=pages, extractor_function=_extractor)


class User(Helper):
    def __init__(self, url: str, core: Optional[BaseCore]):
        super().__init__(core)
        self.url = url
        self.core = core
        self.content = self.core.fetch(url)
        self.logger = setup_logger(name="XNXX API - [User]", log_file=None, level=logging.CRITICAL)

    def enable_logging(self, file, level, log_ip: str = None, log_port: int = None):
        self.logger = setup_logger(name="XNXX API - [User]", log_file=file, level=level, http_ip=log_ip, http_port=log_port)

    @cached_property
    def base_json(self):
        url = f"{self.url}/videos/best/0?from=goldtab"
        content = self.core.fetch(url)
        data = json.loads(html.unescape(content))
        return data

    def videos(self, max_workers: int = 20, pages: int = 0) -> Generator[Video, None, None]:
        def _extractor(content):
            data = json.loads(html.unescape(content))

            if data["code"] == 404:
                return False

            videos = data["videos"]
            video_urls = []
            for video in videos:
                video_urls.append(f"https://xnxx.com{video.get('u')}")

            return video_urls

        yield from self.iterator(max_workers=max_workers, pages=pages, from_goldtab=True, extractor_function=_extractor,
                                 user=True)

    @cached_property
    def total_videos(self) -> int:
        return self.base_json["nb_videos"]

    @cached_property
    def total_video_views(self) -> str:
        return REGEX_MODEL_TOTAL_VIDEO_VIEWS.search(self.content).group(1)


class Client:
    def __init__(self, core: Optional[BaseCore] = None):
        self.core = core or BaseCore(config=RuntimeConfig())
        self.core.initialize_session(headers)

    def get_video(self, url) -> Video:
        """
        :param url: (str) The URL of the video
        :return: (Video) The video object
        """
        return Video(url, core=self.core)

    def search(self, query: str, upload_time: Union[str, UploadTime] = "", length: Union[str, Length] = "",
               searching_quality: Union[str, SearchingQuality] = "", mode: Union[str, Mode] = "") -> Search:
        """
        :param query:
        :param upload_time:
        :param length:
        :param searching_quality:
        :param mode:
        :return: (Search) the search object
        """
        return Search(query=query, core=self.core, upload_time=upload_time, length=length,
        searching_quality=searching_quality, mode=mode)

    def get_user(self, url: str) -> User:
        """
        :param url: (str) The user URL
        :return: (User) The User object
        """
        return User(url, core=self.core)


def main():
    parser = argparse.ArgumentParser(description="API Command Line Interface")
    parser.add_argument("--download", metavar="URL (str)", type=str, help="URL to download from")
    parser.add_argument("--quality", metavar="best,half,worst", type=str, help="The video quality (best,half,worst)", required=True)
    parser.add_argument("--file", metavar="Source to .txt file", type=str, help="(Optional) Specify a file with URLs (separated with new lines)")
    parser.add_argument("--output", metavar="Output directory", type=str, help="The output path (with filename)", required=True)
    parser.add_argument("--downloader", type=str, help="The Downloader (threaded,ffmpeg,default)", required=True)
    parser.add_argument("--no-title", metavar="True,False", type=str, help="Whether to apply video title automatically to output path or not", required=True)

    args = parser.parse_args()
    no_title = BaseCore().str_to_bool(args.no_title)

    if args.download:
        client = Client()
        video = client.get_video(args.download)
        video.download(quality=args.quality, path=args.output, downloader=args.downloader, no_title=no_title)

    if args.file:
        videos = []
        client = Client()

        with open(args.file, "r") as file:
            content = file.read().splitlines()

        for url in content:
            videos.append(client.get_video(url))

        for video in videos:
            video.download(quality=args.quality, path=args.output, downloader=args.downloader, no_title=no_title)


if __name__ == "__main__":
    main()