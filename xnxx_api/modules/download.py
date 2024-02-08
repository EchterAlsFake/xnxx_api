# Thanks to: https://github.com/EchterAlsFake/PHUB/blob/master/src/phub/modules/download.py
# oh and of course ChatGPT lol

from ffmpeg_progress_yield import FfmpegProgress
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, List

CallbackType = Callable[[int, int], None]

"""
Important: The title of the video isn't applied to the output path. You need to manually append it to 
the output path. This has good reasons, to make this library more adaptable into other applications.
"""


def _thread(url: str, timeout: int) -> bytes:
    '''
    Download a single segment using requests.
    '''
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()  # This will raise an exception for HTTP errors
        return response.content
    except requests.RequestException as e:
        print(f"Failed to download segment {url}: {e}")
        return b''


def _base_threaded(segments: List[str],
                   callback: CallbackType,
                   max_workers: int = 50,
                   timeout: int = 10) -> dict[str, bytes]:
    '''
    Base threaded downloader for threaded backends.
    '''
    length = len(segments)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        buffer = {}
        future_to_url = {executor.submit(_thread, url, timeout): url for url in segments}

        completed = 0
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                segment_data = future.result()
                if segment_data:
                    buffer[url] = segment_data
                    completed += 1
                    callback(completed, length)
            except Exception as e:
                print(f"Error downloading segment {url}: {e}")

    return buffer


def threaded(max_workers: int = 100,
             timeout: int = 30) -> Callable:
    def wrapper(video,
                quality,
                callback: CallbackType,
                path: str) -> None:
        segments = list(video.get_segments(quality))

        buffer = _base_threaded(
            segments=segments,
            callback=callback,
            max_workers=max_workers,
            timeout=timeout
        )

        with open(path, 'wb') as file:
            for url in segments:
                file.write(buffer.get(url, b''))

        print(f'Successfully wrote file to {path}')

    return wrapper


def default(video, quality, callback, path, start: int = 0) -> bool:
    buffer = b''
    segments = list(video.get_segments(quality))[start:]
    length = len(segments)

    for i, url in enumerate(segments):
        for _ in range(5):

            segment = requests.get(url)

            if segment.ok:
                buffer += segment.content
                callback(i + 1, length)
                break

    with open(path, 'wb') as file:
        file.write(buffer)

    return True


def FFMPEG(video, quality, callback, path, start=0) -> bool:
    base_url = video.m3u8_base_url
    new_segment = video.get_m3u8_by_quality(quality)
    url_components = base_url.split('/')
    url_components[-1] = new_segment
    new_url = '/'.join(url_components)

    # Build the command for FFMPEG as a list directly
    command = [
        "ffmpeg",
        "-i", new_url,  # Input URL
        "-bsf:a", "aac_adtstoasc",
        "-y",  # Overwrite output files without asking
        "-c", "copy",  # Copy streams without reencoding
        path  # Output file path
    ]

    # Initialize FfmpegProgress and execute the command
    ff = FfmpegProgress(command)
    for progress in ff.run_command_with_progress():
        # Update the callback with the current progress
        callback(int(round(progress)), 100)

        if progress == 100:
            return True

    return False