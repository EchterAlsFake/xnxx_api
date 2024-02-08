# Thanks to: https://github.com/EchterAlsFake/PHUB/blob/master/src/phub/modules/download.py
# oh and of course ChatGPT lol

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from ffmpeg_progress_yield import FfmpegProgress
from typing import Callable
from multiprocessing import Value, Lock

CallbackType = Callable[[int, int], None]

"""
Important: The title of the video isn't applied to the output path. You need to manually append it to 
the output path. This has good reasons, to make this library more adaptable into other applications.
"""


def download_segment(args, retry_count=5):
    url, index, length, callback, processed_segments = args
    for attempt in range(retry_count):
        try:
            segment = requests.get(url, timeout=10)
            if segment.ok:
                with processed_segments.get_lock():  # Ensure thread-safe increment
                    processed_segments.value += 1
                    current_processed = processed_segments.value
                callback(current_processed, length)
                return (index, segment.content)
        except ConnectionError as e:
            if 'HTTPSConnectionPool' in str(e) and attempt < retry_count - 1:
                print(f"Retry {attempt + 1} for segment due to HTTPSConnectionPool error.")
                continue  # Retry for HTTPSConnectionPool errors
            else:
                print(f"Error downloading segment after {attempt + 1} attempts: {e}")
        except requests.RequestException as e:
            print(f"Error downloading segment: {e}")
            break  # No retry for other types of errors


def threaded(video, quality, callback, path, start: int = 0, num_workers: int = 10) -> bool:
    segments = list(video.get_segments(quality))[start:]
    length = len(segments)  # Total number of segments

    # Shared value for counting processed segments and a lock for thread-safe operations
    processed_segments = Value('i', 0)
    buffer_lock = Lock()

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        # Map each future to its corresponding segment index
        future_to_segment = {
            executor.submit(download_segment, (url, i, length, callback, processed_segments)): i
            for i, url in enumerate(segments)
        }

        for future in as_completed(future_to_segment):
            segment_index = future_to_segment[future]
            try:
                _, segment_data = future.result()
                if segment_data:
                    with buffer_lock:
                        # Write the segment data in the correct order
                        with open(path, 'ab') as file:
                            file.write(segment_data)
                with processed_segments.get_lock():
                    processed_segments.value += 1
                    # Halve the progress for the purpose of correct display
                    adjusted_progress = processed_segments.value / 2
                    progress_percent = (adjusted_progress / length) * 100
                    callback(adjusted_progress, length)
            except Exception as e:
                print(f"Exception in downloading segment: {e}")

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