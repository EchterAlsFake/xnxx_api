import pytest
from ..xnxx_api import Client




@pytest.mark.asyncio
async def test_user_all():
    client = Client()
    user = await client.get_user("https://www.xnxx.com/pornstar/cory-chase")
    videos = await user.videos(pages=2)
    objects_video = ["title", "publish_date", "length", "author"]

    assert isinstance(user.total_video_views, str)
    assert int(user.total_videos) > int(0)

    for idx, video in enumerate(videos):
        if idx == 3:
            break

        for object in objects_video:
            assert isinstance(getattr(video, object), str)

