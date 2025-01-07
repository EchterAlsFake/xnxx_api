import pytest
from ..xnxx_api import Client

@pytest.mark.asyncio
async def test_all_search():
    client = Client()
    search = await client.search("fortnite", pages=2)
    videos = await search.videos

    for video in videos:
        print(video.title)

