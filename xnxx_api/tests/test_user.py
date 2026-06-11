from ..xnxx_api import Client
import pytest

@pytest.mark.asyncio
async def test_all():
    client = Client()
    user = await client.get_user("https://www.xnxx.com/pornstar/cory-chase")
    objects_video = ["title", "publish_date", "length", "author"]

    assert isinstance(user.total_video_views, str)
    assert user.total_videos > 0

    idx = 0
    async for video in user.videos():
        idx += 1
        if idx == 3:
            break

        for object in objects_video:
            assert isinstance(getattr(video, object), str)

