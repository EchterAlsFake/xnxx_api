import pytest
from ..xnxx_api import Client

@pytest.mark.asyncio
async def test_all():
    client = Client()
    search = await client.search("fortnite")

    idx = 0
    async for video in search.videos():
        idx += 1
        assert isinstance(video.title, str)

        if idx == 3:
            break