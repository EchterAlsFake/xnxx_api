<h1 align="center">XNXX API</h1> 

<div align="center">
    <a href="https://pepy.tech/project/xnxx_api"><img src="https://static.pepy.tech/badge/xnxx_api" alt="Downloads"></a>
    <a href="https://github.com/EchterAlsFake/xnxx_api/workflows/"><img src="https://github.com/EchterAlsFake/xnxx_api/workflows/CodeQL/badge.svg" alt="CodeQL Analysis"/></a>
</div>

# Description
 
XNXX API is an API for xnxx.com. It allows you to fetch information from videos using regexes and requests.

# Disclaimer

[!IMPORTANT] The xxnx API is in violation to xnxx's ToS!

Copyright Information: I have no intention of stealing copyright protected content or slowing down
a website. Contact me at my E-Mail, and I'll take this Repository immediately offline.

> EchterAlsFake@proton.me

# Quickstart

### Have a look at the [Documentation](https://github.com/EchterAlsFake/xnxx_api/blob/master/README/Documentation.md) for more details

- Install the library with `pip install xnxx_api`


```python
from xnxx_api.xnxx_api import Client, Quality, threaded
# Initialize a Client object
client = Client()

# Fetch a video
video_object = client.get_video("<insert_url_here>")

# Information from Video objects
print(video_object.title)
print(video_object.likes)
# Download the video

video_object.download(downloader=threaded, quality=Quality.BEST, output_path="your_output_path + filename")

# SEE DOCUMENTATION FOR MORE
```

# Changelog
See [Changelog](https://github.com/EchterAlsFake/xnxx_api/blob/master/README/Changelog.md) for more details.

# Contribution
Do you see any issues or having some feature requests? Simply open an Issue or talk
in the discussions.

Pull requests are also welcome.

# License
Licensed under the LGPLv3 License

Copyright (C) 2023–2024 Johannes Habel

# Support

Leave a star on the repository. That's enough :) 


