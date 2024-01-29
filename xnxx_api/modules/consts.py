import re

# ROOT URLs
ROOT_URL = "https://www.xnxx.com/"


# REGEX
REGEX_VIDEO_CHECK = re.compile(r"xnxx.com/(.*?)")
REGEX_VIDEO_TITLE = re.compile(r"html5player\.setVideoTitle\('([^']*)'\);")
REGEX_VIDEO_UPLOADER = re.compile(r"html5player\.setUploaderName\('([^']*)'\);")
REGEX_VIDEO_RATING = re.compile(r'<span class="value">\s*(\d+)\s*</span>')
REGEX_VIDEO_PORNSTARS = re.compile(r'<a class="is-pornstar" href="/search/(.*?)">')
REGEX_VIDEO_KEYWORDS = re.compile(r'<a class="is-keyword" href="/search/(.*?)">')
REGEX_VIDEO_M3U8 = re.compile(r"html5player\.setVideoHLS\('([^']+)'\);")