# XNXX API Documentation

> - Version 1.0
> - Author: Johannes Habel
> - Copryight (C) 2024
> - License: GPL 3
> - Dependencies: requests, lxml, bs4, ffmpeg-progress-yield 
> - Optional dependency: ffmpeg (installed in path)


# Important Notice
The ToS of xnxx.com clearly say, that using scrapers / bots isn't allowed.
> Using this API is on your risk. I am not liable for your actions!

# Table of Contents
- [Importing the API](#importing-the-api)
- [Initializing the Client](#initializing-the-client)
- [The Video object](#the-video-object)
    - [Attributes](#attributes)
    - [Downloading](#downloading-a-video)
    - [Custom callback](#custom-callback-for-downloading--videos)

- [Locals](#locals)
  - [Quality](#the-quality-object)

# Importing the API

#### To import all modules you should use the following:

```python
from xnxx_api.xnxx_api import Client, Quality
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
| .uploader        |   str   |      Yes      |
| .length          |   str   |      Yes      |
| .highest_quality |   str   |      Yes      |
| .views           |   int   |      Yes      |
| .comment_count   |   int   |      Yes      |
| .likes           |   int   |      Yes      |
| .dislikes        |   int   |      Yes      |
| .pornstars       |  list   |      Yes      |
| .description     |   str   |      Yes      |
| .keywords        |  list   |      Yes      |
| .thumbnail_url   |  list   |      Yes      |
| .upload_date     |   str   |      Yes      |
| .content_url     |   str   |      Yes      |

### Downloading a Video:

Explanation: 

Videos are downloaded using segments. These are extracted from the master m3u8 for a given Quality.
There are three ways of downloading videos:

- Default: fetching one by one segment
- FFMPEG: Let ffmpeg handle all this for you
- Threaded: Using multiple workers to fetch the segments (recommended!)

When downloading a video you can give a `downloader` argument which represents a downloader.

You can import the three downloaders using:

```python
from xnxx_api.modules.download import default, threaded, FFMPEG
from xnxx_api.xnxx_api import Client, Quality

client = Client()
video = client.get_video("...")
video.download(downloader=threaded, quality=Quality.BEST, output_path="./IdontKnow.mp4")
                                            # See Locals
# This will save the video in the current working directory with the filename "IdontKnow.mp4"
```

### Custom Callback for downloading  videos

You may want to specify a custom callback for downloading videos. Luckily for you, I made it as easy as
possible :)

1. Create a callback function, which takes `pos` and `total` as arguments.
2. `pos` represents the current amount of downloaded segments
3. `total` represents the total amount of segments

Here's an example:

```python
def custom_callback(pos, total):
    """This is an example of how you can implement the custom callback"""

    percentage = (pos / total) * 100
    print(f"Downloaded: {pos} segments / {total} segments ({percentage:.2f}%)")
    # You see it's really simple :)
```

When downloading a video, you can just specify your callback functions in the `callback` argument


# Locals

## The Quality Object

First: Import the Quality object:

```python
from xnxx_api.xnxx_api import Quality
```

There are three quality types:

- Quality.BEST
- Quality.HALF
- Quality.WORST

I think they explain themselves really good :)


