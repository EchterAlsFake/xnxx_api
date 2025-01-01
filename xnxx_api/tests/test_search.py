from ..xnxx_api import Client

client = Client()
search = client.search("fortnite")

def test_search():
    for idx, video in enumerate(search.videos):
        assert isinstance(video.title, str)

        if idx == 3:
            break