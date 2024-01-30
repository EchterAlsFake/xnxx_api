# Thanks to: https://github.com/EchterAlsFake/PHUB/blob/master/src/phub/modules/download.py

import os
import time
import requests
from requests import adapters
from concurrent.futures import ThreadPoolExecutor, as_completed
from ffmpeg_progress_yield import FfmpegProgress
from typing import Callable


CallbackType = Callable[[int, int], None]


def download_segment_threaded(args):
    url, index, length, callback = args
    for _ in range(5):  # Retry mechanism
        try:
            segment = requests.get(url, timeout=10)
            if segment.ok:
                callback(index + 1, length)
                return segment.content
        except requests.RequestException as e:
            print(f"Error downloading segment {index + 1}: {e}")
    return b''


def threaded(video, quality, callback, path, start: int = 0, num_workers: int = 10):
    segments = list(video.get_segments(quality))[start:]
    length = len(segments)
    buffer = bytearray()

    # Using ThreadPoolExecutor to download segments in parallel
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        # Prepare the list of tasks
        futures = [executor.submit(download_segment_threaded, (url, i, length, callback)) for i, url in enumerate(segments)]
        for future in as_completed(futures):
            try:
                # Collect results as they complete
                segment_data = future.result()
                buffer.extend(segment_data)
            except Exception as e:
                print(f"Error in downloading segment: {e}")

    # Write the collected segments to a file
    with open(path, 'wb') as file:
        file.write(buffer)


def default(video, quality, callback, path, start: int = 0):
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


def FFMPEG(video,
           quality,
           callback: CallbackType,
           path: str,
           start: int = 0) -> None:
    '''
    Download using FFMPEG with real-time progress reporting.
    FFMPEG must be installed on your system.
    You can override FFMPEG access with consts.FFMPEG_COMMAND.

    Args:
        video       (Video): The video object to download.
        quality   (Quality): The video quality.
        callback (Callable): Download progress callback.
        path          (str): The video download path.
        start         (int): Where to start the download from. Used for download retries.
    '''

    m3u = video.get_m3u8_by_quality(quality)

    # Build the command for FFMPEG
    FFMPEG_COMMAND = "ffmpeg" + ' -i "{input}" -bsf:a aac_adtstoasc -y -c copy {output}'
    command = FFMPEG_COMMAND.format(input=m3u, output=path).split()

    # Removes quotation marks from the url
    command[2] = command[2].strip('"')

    # Initialize FfmpegProgress and execute the command
    ff = FfmpegProgress(command)
    for progress in ff.run_command_with_progress():
        # Update the callback with the current progress
        callback(int(round(progress)), 100)

        if progress == 100:
            print("Download Successful")


