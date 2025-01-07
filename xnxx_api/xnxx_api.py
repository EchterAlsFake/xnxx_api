import asyncio

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

from typing import Union, Generator, List
from bs4 import BeautifulSoup
from functools import cached_property
from base_api import BaseCore, Callback

core = BaseCore()
logging.basicConfig(format='%(name)s %(levelname)s %(asctime)s %(message)s', datefmt='%I:%M:%S %p')
logger = logging.getLogger("XNXX API")
logger.setLevel(logging.DEBUG)

def disable_logging() -> None:
    logger.setLevel(logging.CRITICAL)


class Video:
    def __init__(self, url, content):
        self.url = url
        self.available_m3u8_urls = None
        self.script_content = None
        self.metadata_matches = None
        self.json_content = None
        self.html_content = content
        self.get_script_content()
        self.get_metadata_matches()
        self.extract_json_from_html()

    @classmethod
    async def create(cls, url):
        if not REGEX_VIDEO_CHECK.search(url):
            raise InvalidUrl("The video URL is invalid!")

        content = await core.fetch(url)
        return cls(url, content)


    @classmethod
    def is_desired_script(cls, tag):
        if tag.name != "script":
            return False
        script_contents = ['html5player', 'setVideoTitle', 'setVideoUrlLow']
        return all(content in tag.text for content in script_contents)

    def get_metadata_matches(self) -> None:
        soup = BeautifulSoup(self.html_content, 'html.parser')
        metadata_span = soup.find('span', class_='metadata')
        metadata_text = metadata_span.get_text(separator=' ', strip=True)

        # Use a regex to extract the desired strings
        self.metadata_matches = re.findall(r'(\d+min|\d+p|\d[\d.,]*\s*[views]*)', metadata_text)

    def get_script_content(self) -> None:
        soup = BeautifulSoup(self.html_content, features="html.parser")
        target_script = soup.find(self.is_desired_script)
        if target_script:
            self.script_content = target_script.text

        else:
            raise InvalidResponse("Couldn't extract JSON from HTML")

    def extract_json_from_html(self) -> None:
        soup = BeautifulSoup(self.html_content, features="html.parser")
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

    async def get_segments(self, quality: str) -> list:
        return await core.get_segments(quality=quality, m3u8_url_master=self.m3u8_base_url)

    async def download(self, quality: str, downloader: str, path: str = "./", callback=Callback.text_progress_bar,
                 no_title: bool = False) -> bool:

        if no_title is False:
            path = os.path.join(path, self.title + ".mp4")

        try:
            await core.download(video=self, quality=quality, path=path, callback=callback, downloader=downloader)
            return True

        except Exception:
            error = traceback.format_exc()
            logger.error(error)
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
    def __init__(self, query: str, upload_time: Union[str, UploadTime], length: Union[str, Length], searching_quality:
                                                Union[str, SearchingQuality], mode: Union[str, Mode], content: str,
                                                pages: int = 2):

        self.query = self.validate_query(query)
        self.html_content = content
        self.upload_time = upload_time
        self.length = length
        self.searching_quality = searching_quality
        self.mode = mode
        self.pages = pages

    @classmethod
    async def create(cls, query: str, upload_time: Union[str, UploadTime], length: Union[str, Length], searching_quality:
                                                Union[str, SearchingQuality], mode: Union[str, Mode], pages: int = 2):

        content = await core.fetch(f"https://www.xnxx.com/search{mode}{upload_time}{length}{searching_quality}/{query}")
        return cls(query=query, content=content, length=length, searching_quality=searching_quality, mode=mode,
                   upload_time=upload_time, pages=pages)

    @classmethod
    def validate_query(cls, query):
        return query.replace(" ", "+")

    @cached_property
    def total_pages(self) -> str:
        return REGEX_SEARCH_TOTAL_PAGES.search(self.html_content).group(1)

    @cached_property
    async def videos(self) -> List[Video]:
        urls = []

        urls.append(f"https://www.xnxx.com/search{self.mode}{self.upload_time}{self.length}{self.searching_quality}/{self.query}")

        """
        I would not recommend you to attempt to fetch from self.total_pages, because this will mostly scrape over 100 pages 
        and after some time you will get blocked from XNXX, so please limit your search results."""

        for i in range(1, int(self.pages)):
            url = f"https://www.xnxx.com/search{self.mode}{self.upload_time}{self.length}{self.searching_quality}/{self.query}/{i}"
            urls.append(url)

        tasks = [asyncio.create_task(core.fetch(url)) for url in urls]
        results = await asyncio.gather(*tasks)

        scraped_urls = []
        video_urls = []

        for page in results:
            urls_ = REGEX_SCRAPE_VIDEOS.findall(page)
            scraped_urls.extend(urls_)

        for url in scraped_urls:
            video_urls.append(f"https://www.xnxx.com/video-{url}")


        video_tasks = [asyncio.create_task(Video.create(url)) for url in video_urls]
        video_results = await asyncio.gather(*video_tasks)
        return video_results


class User:
    def __init__(self, url: str, data, content: str):
        self.url = url
        self.base_json = data
        self.pages = round(int(self.total_videos) / 50)
        self.content = content

    @classmethod
    async def create(cls, url):
        data = await core.fetch(f"{url}/videos/best/0?from=goldtab")
        json_data = json.loads(html.unescape(data))

        content = await core.fetch(url)
        return cls(url, json_data, content)

    async def videos(self, pages) -> List[Video]:
        urls = [f"{self.url}/videos/best/{page}?from=goldtab" for page in range(pages)]
        html_tasks = [asyncio.create_task(core.fetch(url)) for url in urls]
        results = await asyncio.gather(*html_tasks)
        video_urls = []

        for result in results:

            data = json.loads(html.unescape(result))
            videos = data["videos"]
            for video in videos:
                url = video.get("u")
                video_urls.append(f"https://www.xnxx.com{url}")

        video_tasks = [asyncio.create_task(Video.create(url)) for url in video_urls]
        video_results = await asyncio.gather(*video_tasks)
        return video_results


    @cached_property
    def total_videos(self) -> str:
        return self.base_json["nb_videos"]

    @cached_property
    def total_video_views(self) -> str:
        return REGEX_MODEL_TOTAL_VIDEO_VIEWS.search(self.content).group(1)


class Client:

    @classmethod
    async def get_video(cls, url) -> Video:
        """
        :param url: (str) The URL of the video
        :return: (Video) The video object
        """
        return await Video.create(url)

    @classmethod
    async def search(cls, query: str, upload_time: Union[str, UploadTime] = "", length: Union[str, Length] = "",
                     searching_quality: Union[str, SearchingQuality] = "", mode: Union[str, Mode] = "",
                     pages: int = 2) -> Search:
        """
        :param query:
        :param upload_time:
        :param length:
        :param searching_quality:
        :param mode:
        :param pages:
        :return: (Search) the search object
        """
        return await Search.create(query=query, upload_time=upload_time, length=length, searching_quality=searching_quality,
                                   mode=mode, pages=pages)

    @classmethod
    async def get_user(cls, url: str) -> User:
        """
        :param url: (str) The user URL
        :return: (User) The User object
        """
        return await User.create(url)

def str_to_bool(value):
    if value.lower() in ("true", "1", "yes"):
        return True
    elif value.lower() in ("false", "0", "no"):
        return False
    else:
        raise argparse.ArgumentTypeError(f"Invalid boolean value: {value}")

async def main():
    parser = argparse.ArgumentParser(description="API Command Line Interface")
    parser.add_argument("--download", metavar="URL (str)", type=str, help="URL to download from")
    parser.add_argument("--quality", metavar="best,half,worst", type=str, help="The video quality (best,half,worst)", required=True)
    parser.add_argument("--file", metavar="Source to .txt file", type=str, help="(Optional) Specify a file with URLs (separated with new lines)")
    parser.add_argument("--output", metavar="Output directory", type=str, help="The output path (with filename)", required=True)
    parser.add_argument("--downloader", type=str, help="The Downloader (threaded,ffmpeg,default)", required=True)
    parser.add_argument("--no-title", metavar="True,False", type=str_to_bool, help="Whether to apply video title automatically to output path or not", required=True)

    args = parser.parse_args()
    if args.download:
        client = Client()
        video = await client.get_video(args.download)
        await video.download(quality=args.quality, path=args.output, downloader=args.downloader, no_title=args.no_title)

    if args.file:
        videos = []
        client = Client()

        with open(args.file, "r") as file:
            content = file.read().splitlines()

        for url in content:
            videos.append(await client.get_video(url))

        for video in videos:
            await video.download(quality=args.quality, path=args.output, downloader=args.downloader, no_title=args.no_title)


if __name__ == "__main__":
    asyncio.run(main())