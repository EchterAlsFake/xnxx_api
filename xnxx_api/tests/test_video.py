from ..xnxx_api import Video
url = "https://www.xnxx.com/video-1b9bufc9/die_zierliche_stieftochter_passt_kaum_in_den_mund_ihres_stiefvaters"
# This will be the URL for all tests

video = Video(url)


def test_video_title():
    title = video.title
    assert isinstance(title, str) and len(title) > 0


def test_author():
    author = video.author
    assert isinstance(author, str) and len(author) > 0


def test_length():
    length = video.length
    assert isinstance(length, str) and len(length) > 0


def test_highest_quality():
    highest_quality = video.highest_quality
    assert isinstance(highest_quality, str) and len(highest_quality) > 0


def test_views():
    views = video.views
    assert isinstance(views, str) and len(views) > 0


def test_comment_count():
    comment_count = video.comment_count
    assert isinstance(comment_count, str)


def test_likes():
    likes = video.likes
    assert isinstance(likes, str)


def test_dislikes():
    dislikes = video.dislikes
    assert isinstance(dislikes, str)


def test_pornstars():
    pornstars = video.pornstars
    assert isinstance(pornstars, list)  # Some videos don't contain pornstars, which is why we don't test it here


def test_description():
    description = video.description
    assert isinstance(description, str) and len(description) > 0


def test_keywords():
    tags = video.tags
    assert isinstance(tags, list) and len(tags) > 0


def test_thumbnail_url():
    thumbnail_url = video.thumbnail_url
    assert isinstance(thumbnail_url, list) and len(thumbnail_url) > 0


def test_publish_date():
    publish_date = video.publish_date
    assert isinstance(publish_date, str) and len(publish_date) > 0


def test_content_url():
    content_url = video.content_url
    assert isinstance(content_url, str) and len(content_url) > 0


def test_get_segments():
    segments = list(video.get_segments(quality="best"))
    assert len(segments) > 10

def test_download_low():
    assert video.download(quality="worst", downloader="threaded") is True