# Thanks to: https://github.com/EchterAlsFake/PHUB/blob/master/src/phub/modules/download.py
# oh and of course ChatGPT lol

import time
import requests
from ffmpeg_progress_yield import FfmpegProgress
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, List

CallbackType = Callable[[int, int], None]

"""
Important: The title of the video isn't applied to the output path. You need to manually append it to 
the output path. This has good reasons, to make this library more adaptable into other applications.
"""


def download_segment(url: str, timeout: int, retries: int = 3, backoff_factor: float = 0.3) -> tuple[str, bytes, bool]:
    """
    Attempt to download a single segment, retrying on failure.
    Returns a tuple of the URL, content (empty if failed after retries), and a success flag.
    """
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()  # Raises stored HTTPError, if one occurred.
            return (url, response.content, True)  # Success
        except requests.RequestException as e:
            print(f"Retry {attempt + 1} for {url}: {e}")
            time.sleep(backoff_factor * (2 ** attempt))  # Exponential backoff

    # After all retries have failed
    return (url, b'', False)  # Failed download


def improved_threaded(max_workers: int = 50, timeout: int = 10, retries: int = 3):
    """
    Creates a wrapper function for the actual download process, with retry logic.
    """
    def wrapper(segments, callback, path):
        """
        Download video segments in parallel, with retries for failures, and write to a file.
        """
        length = len(segments)
        completed, successful_downloads = 0, 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_segment = {executor.submit(download_segment, url, timeout, retries): url for url in segments}

            for future in as_completed(future_to_segment):
                segment_url = future_to_segment[future]
                try:
                    _, data, success = future.result()
                    completed += 1
                    if success:
                        successful_downloads += 1
                    callback(completed, length)  # Update callback regardless of success to reflect progress
                except Exception as e:
                    print(f"Unhandled error downloading segment {segment_url}: {e}")

        print(f"Completed downloading {completed} out of {length} segments, with {successful_downloads} successful.")

        # Writing only successful downloads to the file
        with open(path, 'wb') as file:
            for segment_url in segments:
                if segment_url in future_to_segment:
                    future = future_to_segment[segment_url]
                    try:
                        _, data, success = future.result()
                        if success:
                            file.write(data)
                    except:
                        pass  # This block could further handle or log missing data scenarios

        print(f"Successfully wrote file to {path}")

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