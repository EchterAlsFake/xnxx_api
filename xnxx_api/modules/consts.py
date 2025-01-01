import re

# ROOT URLs
ROOT_URL = "https://www.xnxx.com/"

# REGEX
REGEX_VIDEO_CHECK = re.compile(r"xnxx.com/(.*?)")
REGEX_VIDEO_TITLE = re.compile(r"html5player\.setVideoTitle\('([^']*)'\);")
REGEX_VIDEO_UPLOADER = re.compile(r"html5player\.setUploaderName\('([^']*)'\);")
REGEX_VIDEO_LIKES = re.compile(r'<span class="icon thumb-up"></span><span class="value">(.*?)</span>', re.DOTALL)
REGEX_VIDEO_DISLIKES = re.compile(r'<span class="icon thumb-down"></span><span class="value">(.*?)</span>', re.DOTALL)
REGEX_VIDEO_COMMENT_COUNT = re.compile(r'<span class="icon comments"></span><span class="value">(.*?)</span>')
REGEX_VIDEO_PORNSTARS = re.compile(r'<a class="is-pornstar" href="/search/(.*?)">')
REGEX_VIDEO_KEYWORDS = re.compile(r'<a class="is-keyword" href="/search/(.*?)">')
REGEX_VIDEO_M3U8 = re.compile(r"html5player\.setVideoHLS\('([^']+)'\);")

REGEX_SCRAPE_VIDEOS = re.compile(r'<div class="thumb"><a href="/video-(.*?)"')

REGEX_SEARCH_TOTAL_PAGES = re.compile(r'class="last-page">(.*?)</a>')
REGEX_MODEL_TOTAL_PAGES = re.compile(r'<a class="last-page" data-page="(.*?)">')
REGEX_MODEL_TOTAL_VIDEO_VIEWS = re.compile(r'<span class="icon-f icf-eye"></span> (.*?) video views')