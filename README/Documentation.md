from re import search

# XNXX API Documentation

> - Version 1.4.1
> - Author: Johannes Habel
> - Copyright (C) 2024
> - License: LGPLv3
> - Dependencies: requests, lxml, bs4, ffmpeg-progress-yield, eaf_base_api
> - Optional dependency: ffmpeg (installed in your path)


> [!WARNING]
> The ToS of xnxx.com clearly say that using scrapers / bots isn't allowed.
> Using this API is on your risk. I am not liable for your actions!

# Table of Contents
- [Importing the API](#importing-the-api)
- [Initializing the Client](#initializing-the-client)
- [The Video object](#the-video-object)
    - [Attributes](#attributes)
    - [Downloading](#downloading-a-video)
    - [Custom callback](#custom-callback-for-downloading--videos)
- [Searching](#searching)
- [Model / Users](#models--users)
- [Locals](#locals)
  - [Quality](#the-quality-object)
  - [Searching Filters](#searching-filters)

# Importing the API

#### To import all modules, you should use the following:

```python
from xnxx_api import Client, Quality
```

# Initializing the Client

- The Client is needed for all basic operations and will be used to handle everything.

```python
from xnxx_api.xnxx_api import Client

client = Client()

# Now you can fetch a Video object:

video = client.get_video("<video_url")
```


# The Video Object

The video object has the following values:

### Attributes

| Attribute        | Returns |  is cached?   |
|:-----------------|:-------:|:-------------:|
| .title           |   str   |      Yes      |
| .author          |   str   |      Yes      |
| .length          |   str   |      Yes      |
| .highest_quality |   str   |      Yes      |
| .views           |   int   |      Yes      |
| .comment_count   |   int   |      Yes      |
| .likes           |   int   |      Yes      |
| .dislikes        |   int   |      Yes      |
| .pornstars       |  list   |      Yes      |
| .description     |   str   |      Yes      |
| .tags            |  list   |      Yes      |
| .thumbnail_url   |  list   |      Yes      |
| .publish_date    |   str   |      Yes      |
| .content_url     |   str   |      Yes      |

### Downloading a Video:

Explanation: 

Videos are downloaded using segments. These are extracted from the master m3u8 for a given Quality.
There are three ways of downloading videos:

- Default: fetching one by one segment
- FFMPEG: Let ffmpeg handle all this for you
- Threaded: Using multiple workers to fetch the segments (recommended!)

When downloading a video, you can give a `downloader` argument which represents a downloader.

You can import the three downloaders using:

```python
from base_api.modules.download import FFMPEG, threaded, default
from base_api.modules.quality import Quality
from xnxx_api.xnxx_api import Client

client = Client()
video = client.get_video("...")
video.download(downloader=threaded, quality=Quality.BEST, path="./IdontKnow.mp4")
                                            # See Locals
# This will save the video in the current working directory with the filename "IdontKnow.mp4"
```

### Custom Callback for downloading videos

You may want to specify a custom callback for downloading videos. Luckily for you, I made it as easy as
possible :)

1. Create a callback function, which takes `pos` and `total` as arguments.
2. `pos` represents the current number of downloaded segments
3. `total` represents the total number of segments

Here's an example:

```python
def custom_callback(pos, total):
    """This is an example of how you can implement the custom callback"""

    percentage = (pos / total) * 100
    print(f"Downloaded: {pos} segments / {total} segments ({percentage:.2f}%)")
    # You see it's really simple :)
```

When downloading a video, you can just specify your callback functions in the `callback` argument

# Searching
```python
from xnxx_api import Client
from xnxx_api import search_filters

client = Client()
search = client.search("<query>", upload_time=search_filters.UploadTime.month, length=search_filters.Length.X_0_10min, 
                       searching_quality=search_filters.SearchingQuality.X_720p, mode=search_filters.Mode.default)
# this is an example

for video in search.videos:
  print(video.title)
  # Iterate like this over results
```

> [!Important]
> You can also search using categories with filters. Specify the category name in the query.

# Models / Users

```python
from xnxx_api.xnxx_api import Client

client = Client()
model = client.get_user("<user_url>") # example: xnxx.com/pornstar/...

videos = model.videos

for video in videos:
  print(video.title)
  
# Total number of videos:
print(model.total_videos)


```


# Locals

## The Quality Object

First: Import the Quality object:

```python
from base_api.modules.quality import Quality
```

There are three quality types:

- Quality.BEST
- Quality.HALF
- Quality.WORST

> [!IMPORTANT]
> - You can also pass a string instead of a Quality object. e.g instead of `Quality.BEST`, you can say `best`
> - The same goes for threading modes. Instead of `download.threaded` you can just say `threaded` as a string

## Searching Filters

Currently, there are three filters available:

- Searching Quality
- Upload Time
- Length
- Mode

They are located in:

```python
from xnxx_api import search_filters
from xnxx_api.xnxx_api import Client
# Use them like this:

search = Client().search("<query>", length=search_filters.Length.X_0_10min, upload_time=search_filters.UploadTime.year,
                         searching_quality=search_filters.SearchingQuality.X_1080p_plus, mode=search_filters.Mode.default)
videos = search.videos
# I think the names explain what it does :)
```