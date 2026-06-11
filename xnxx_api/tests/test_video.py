import pytest
from ..xnxx_api import Client
url = "https://www.xnxx.com/video-1b9bufc9/die_zierliche_stieftochter_passt_kaum_in_den_mund_ihres_stiefvaters"
# This will be the URL for all tests

@pytest.mark.asyncio
async def test_all():
    video = await Client().get_video(url)
    title = video.title
    assert isinstance(title, str) and len(title) > 0
    author = video.author
    assert isinstance(author, str) and len(author) > 0
    length = video.length
    assert isinstance(length, str) and len(length) > 0
    highest_quality = video.highest_quality
    assert isinstance(highest_quality, str) and len(highest_quality) > 0
    views = video.views
    assert isinstance(views, str) and len(views) > 0
    comment_count = video.comment_count
    assert isinstance(comment_count, str)
    likes = video.likes
    assert isinstance(likes, str)
    dislikes = video.dislikes
    assert isinstance(dislikes, str)
    pornstars = video.pornstars
    assert isinstance(pornstars, list)  # Some videos don't contain pornstars, which is why we don't test it here
    description = video.description
    assert isinstance(description, str) and len(description) > 0
    tags = video.tags
    assert isinstance(tags, list) and len(tags) > 0
    thumbnail_url = video.thumbnail_url
    assert isinstance(thumbnail_url, list) and len(thumbnail_url) > 0
    publish_date = video.publish_date
    assert isinstance(publish_date, str) and len(publish_date) > 0
    content_url = video.content_url
    assert isinstance(content_url, str) and len(content_url) > 0
    segments = list(await video.get_segments(quality="best"))
    assert len(segments) > 10
    fortnite_1 = await video.download(quality="worst", remux=True, return_report=True)
    fortnite_2 = await video.download(quality="worst", remux=False, return_report=True)

    assert fortnite_1["status"] == "completed"
    assert fortnite_2["status"] == "completed"

