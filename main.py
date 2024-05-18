import argparse
from queue import Queue
from typing import Tuple

from deside_option_video_download import DesideOptionVideoDownload
from video_download import VideoDownloaderQueue


def analysis_args() -> str:
    parser = argparse.ArgumentParser(description="Download videos from the internet.")
    parser.add_argument(
        "-c",
        "--cookiefile",
        action="store",
        type=str,
        default="",
        required=False,
        help=(
            "A txt file path in net space format containing cookie information "
            "to be used for download."
        ),
    )
    args = parser.parse_args()
    cookie_path: str = args.cookiefile
    return cookie_path.strip(" \"'")


def main():
    urls_filename_q: Queue[Tuple[str, str]] = Queue()
    cookiepath = analysis_args()

    set_optioner = DesideOptionVideoDownload(cookie_file=cookiepath)
    result = set_optioner.run()
    if result is None:
        return
    ydl_opts, custom_opt, multi_url_filename = result

    for url, filename in multi_url_filename:
        urls_filename_q.put((url, filename))

    video_downloader = VideoDownloaderQueue(ydl_opts, custom_opt)
    download_status_urls_q = video_downloader.start_download(urls_filename_q)
    video_downloader.display_result(download_status_urls_q)


if __name__ == "__main__":
    main()
    # TODO 通知とか送信したい
