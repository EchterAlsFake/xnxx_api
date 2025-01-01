from ..xnxx_api import Client

client = Client()
user = client.get_user("https://www.xnxx.com/pornstar/cory-chase")
objects_video = ["title", "publish_date", "length", "author"]



def test_video_views():
    assert isinstance(user.total_video_views, str)
    assert user.total_videos > 0

def test_videos():
    for idx, video in enumerate(user.videos):
        if idx == 3:
            break
        for object in objects_video:
            assert isinstance(getattr(video, object), str)

