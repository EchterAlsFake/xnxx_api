class Callback:
    @classmethod
    def custom_callback(cls, downloaded, total):
        """This is an example of how you can implement the custom callback"""

        percentage = (downloaded / total) * 100
        print(f"Downloaded: {downloaded} bytes / {total} bytes ({percentage:.2f}%)")

    @classmethod
    def text_progress_bar(cls, downloaded, total):
        bar_length = 50
        filled_length = int(round(bar_length * downloaded / float(total)))
        percents = round(100.0 * downloaded / float(total), 1)
        bar = '#' * filled_length + '-' * (bar_length - filled_length)
        print(f"\r[{bar}] {percents}%", end='')