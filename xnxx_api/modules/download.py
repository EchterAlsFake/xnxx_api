# Thanks to: https://github.com/EchterAlsFake/PHUB/blob/master/src/phub/modules/download.py
# oh and of course ChatGPT lol

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from ffmpeg_progress_yield import FfmpegProgress
from typing import Callable


CallbackType = Callable[[int, int], None]

"""
Important: The title of the video isn't applied to the output path. You need to manually append it to 
the output path. This has good reasons, to make this library more adaptable into other applications.
"""


def download_segment(args, retry_count=5):
    url, length, callback, processed_segments = args
    for attempt in range(retry_count):
        try:
            segment = requests.get(url, timeout=10)
            if segment.ok:
                with processed_segments.get_lock():  # Ensure thread-safe increment
                    processed_segments.value += 1
                    current_processed = processed_segments.value
                callback(current_processed, length)
                return segment.content
        except ConnectionError as e:
            if 'HTTPSConnectionPool' in str(e) and attempt < retry_count - 1:
                print(f"Retry {attempt + 1} for segment due to HTTPSConnectionPool error.")
                continue  # Retry for HTTPSConnectionPool errors
            else:
                print(f"Error downloading segment after {attempt + 1} attempts: {e}")
        except requests.RequestException as e:
            print(f"Error downloading segment: {e}")
            break  # No retry for other types of errors
    return b''


def threaded(video, quality, callback, path, start: int = 0, num_workers: int = 10) -> bool:
    from multiprocessing import Value

    segments = list(video.get_segments(quality))[start:]
    length = len(segments)
    buffer = bytearray()

    processed_segments = Value('i', 0)  # Shared value for counting processed segments

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(download_segment, (url, length, callback, processed_segments)) for url in segments]
        for future in as_completed(futures):
            try:
                segment_data = future.result()
                buffer.extend(segment_data)
            except Exception as e:
                print(f"Exception in downloading segment: {e}")

    with open(path, 'wb') as file:
        file.write(buffer)

    return True


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


def FFMPEG(video,
           quality,
           callback: CallbackType,
           path: str,
           start: int = 0) -> bool:

    base_url = video.m3u8_base_url
    new_segment = video.get_m3u8_by_quality(quality)
    url_components = base_url.split('/')
    url_components[-1] = new_segment
    new_url = '/'.join(url_components)

    # Build the command for FFMPEG
    FFMPEG_COMMAND = "ffmpeg" + ' -i "{input}" -bsf:a aac_adtstoasc -y -c copy {output}'
    command = FFMPEG_COMMAND.format(input=new_url, output=path).split()

    # Removes quotation marks from the url
    command[2] = command[2].strip('"')

    # Initialize FfmpegProgress and execute the command
    ff = FfmpegProgress(command)
    for progress in ff.run_command_with_progress():
        # Update the callback with the current progress
        callback(int(round(progress)), 100)

        if progress == 100:
            return True
