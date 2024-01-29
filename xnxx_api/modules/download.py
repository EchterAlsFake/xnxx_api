# Thanks to: https://github.com/EchterAlsFake/PHUB/blob/master/src/phub/modules/download.py

import os
import time
import requests
from requests import adapters
from concurrent.futures import ThreadPoolExecutor as Pool, as_completed
from ffmpeg_progress_yield import FfmpegProgress
from typing import Callable

CallbackType = Callable[[int, int], None]


def default(video, quality, callback, path, start: int = 0):
    buffer = b''
    segments = list(video.get_segments(quality))[start:]
    length = len(segments)

    for i, url in enumerate(segments):
        for _ in range(5):

            segment = video.client.call(url, throw=False, timeout=4, silent=True)

            if segment.ok:
                buffer += segment.content
                callback(i + 1, length)
                break

    with open(path, 'wb') as file:
        file.write(buffer)

def FFMPEG(video: Video,
           quality: Quality,
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


def _thread(session, url: str, timeout: int) -> bytes:
    '''
    Download a single segment.
    '''

    return session.get(url, timeout=timeout, silent=True).content


def _base_threaded(segments: list[str],
                   callback: CallbackType,
                   max_workers: int = 50,
                   timeout: int = 10,
                   disable_client_delay: bool = True) -> dict[str, bytes]:
    '''
    base thread downloader for threaded backends.
    '''

    length = len(segments)

    with Pool(max_workers=max_workers) as executor:

        buffer: dict[str, bytes] = {}
        segments = segments.copy()  # Avoid deleting parsed segments

        while 1:
            futures = {executor.submit(_thread, client, url, timeout): url
                       for url in segments}


            for future in as_completed(futures):

                url = futures[future]
                segment_name = consts.re.ffmpeg_line(url)

                segment = future.result()
                buffer[url] = segment

                # Remove future and call callback
                segments.remove(url)
                callback(len(buffer), length)



            if lns := len(segments):
                print("Retrying to fetch %s segments", lns)
                continue

            break

    return buffer
