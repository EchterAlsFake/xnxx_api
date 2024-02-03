from ..xnxx_api import Video, Quality

url = "https://www.xnxx.com/video-16vi44cb/besorg_dir_jetzt_ein_sex-date_auf_fuckmatch.fun_-_deutsch_fuck"
# This will be the URL for all tests

video = Video(url)


def test_video_title():
    title = video.title
    assert isinstance(title, str) and len(title) > 0


def test_uploader():
    uploader = video.uploader
    assert isinstance(uploader, str) and len(uploader) > 0


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
    keywords = video.keywords
    assert isinstance(keywords, list) and len(keywords) > 0


def test_thumbnail_url():
    thumbnail_url = video.thumbnail_url
    assert isinstance(thumbnail_url, list) and len(thumbnail_url) > 0


def test_upload_date():
    upload_date = video.upload_date
    assert isinstance(upload_date, str) and len(upload_date) > 0


def test_content_url():
    content_url = video.content_url
    assert isinstance(content_url, str) and len(content_url) > 0


def test_quality():
    quality = video.fix_quality("best")
    assert isinstance(quality, Quality)


def test_get_segments():
    segments = video.get_segments(quality=Quality.BEST)
    segment_list = []

    for segment in segments:
        segment_list.append(segment)

    assert len(segment_list) > 10

