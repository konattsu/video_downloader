import copy
import os
import queue
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from logging import getLogger
from queue import Queue
from threading import current_thread
from typing import Any

import yt_dlp
from enum_config import DownloadMode, Thumbnail
from logger_config import LoggerConfigurator
from types_config import DlYdlOpts, UrlsFilenameQ

DownloadStatusUrlsQ = Queue[tuple[bool, str]]

# TODO ドキュメンテーション文字列の推敲


class VideoDownloader:
    """A class for download YouTube videos."""

    def __init__(self, dl_ydl_opts: DlYdlOpts, options: dict[str, Any]) -> None:
        """Initialize the VideoDownload object.

        Args:
            ydl_opts (Dict[str, Any]): Options for downloading using yt_dlp
            options (Dict[str, Any]): Options obtained using SetOptionVideoDownload

        Attributes:
            logger: Logger object for logging messages.
            ydl_opts: Options for downloading using yt_dlp.
            dir_path: Directory where downloaded files are stored.
            ffmpeg_path: Location of 'ffmpeg.exe' to convert files, "" if not used.
            download_mode: Specifying file format. See enum_config.py
            thumbnail_mode: Specifying thumbnail format. See enum_config.py

        Example:
            >>> downloader = VideoDownloader(ydl_opts, options)
        """

        LoggerConfigurator()
        self.logger = getLogger()
        # Variable
        self.dl_ydl_opts: DlYdlOpts = copy.deepcopy(dl_ydl_opts)
        self.dir_path: str = options["dir_path"]
        self.ffmpeg_path: str = options["ffmpeg_path"]
        self.download_mode: DownloadMode = options["download_mode"]
        self.thumbnail_mode: Thumbnail = options["thumbnail_mode"]
        # Const
        self.EXT_WAV = ".wav"
        self.EXT_PNG = ".png"
        self.EXT_DEFAULT_THUMBNAIL = ".webp"
        # Reduce logs
        self.dl_ydl_opts["quiet"] = True
        self.dl_ydl_opts["noprogress"] = True

    def download_videos(self, url: str, filename: str) -> bool:
        """Download videos from YouTube.

        Args:
            url (str): The url of the video to be downloaded.
            filename (str): File name with extension of the video to be downloaded.

        Returns:
            bool: True if the download is successful, False otherwise.

        Note:
            It is strongly recommended that the URL not be a video in the playlist.
            The filename of the argument is later combined with the directory name
            of the class variable.
            Method '_set_thumbnail' embeds a thumbnail image in the first frame.

        Example:
            >>> url = "https://www.youtube.com/watch?v=abc123"
            >>> filename = "test_video.mp4"
            >>> downloader = VideoDownloader(ydl_opts, options)
            >>> result = downloader.download_videos(url, filename)
            >>> print(result)
            True

            Note: The variables ydl_opts and filename are assumed to have been
            successfully created using 'analysis_urls.py'.
        """

        dl_ydl_opts: DlYdlOpts = copy.deepcopy(self.dl_ydl_opts)
        file_path: str = os.path.join(self.dir_path, filename)
        return self._download(url, dl_ydl_opts, file_path)

    # TODO 戻り値タプルで(DL, ほかの操作(サムネとか)の結果)とかいいかも
    def _download(self, url: str, ydl_opts: DlYdlOpts, file_path: str) -> bool:
        ydl_opts["outtmpl"] = file_path
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                self.logger.info(
                    f"Filename: '{os.path.splitext(os.path.basename(file_path))[0]}'"
                )
                ydl.download([url])
            except yt_dlp.DownloadError:
                self.logger.error(
                    f"Failed to download video. url: '{url}', file_path: '{file_path}'"
                )
                # TODO このときのファイル名とかurlを保持して最後にもう一回DL試す
                return False
        if self.download_mode == DownloadMode.WAV:
            if not self._post_convert_to_wav_(file_path):
                return False
        if self.thumbnail_mode not in [Thumbnail.PLAIN, Thumbnail.GET_WEBP]:
            self._thumbnail_process(file_path)
        return True

    def _post_convert_to_wav_(self, file_fullpath: str) -> bool:
        dst_file_fullpath = self._convert_to_wav(file_fullpath)
        if dst_file_fullpath is None:
            return False
        os.remove(file_fullpath)
        return True

    def _convert_to_wav(self, file_fullpath: str) -> str | None:
        src = file_fullpath
        dst = os.path.splitext(file_fullpath)[0] + self.EXT_WAV
        ret = self._change_ext(src, dst)
        return dst if ret else None

    def _thumbnail_process(self, video_path: str) -> bool:
        thumbnail_path_wemb = (
            os.path.splitext(video_path)[0] + self.EXT_DEFAULT_THUMBNAIL
        )
        th_mode = self.thumbnail_mode

        # Convert to png format
        thumbnail_path_png = self._convert_to_png(thumbnail_path_wemb)
        if thumbnail_path_png is None:
            return False
        os.remove(thumbnail_path_wemb)
        if th_mode == Thumbnail.GET_PNG:
            return True
        # Set thumbnail to video
        ret = self._set_thumbnail(video_path, thumbnail_path_png)
        if ret is False:
            return False
        # Delete image for thumbnail
        if th_mode == Thumbnail.SET:
            os.remove(thumbnail_path_png)
        return True

    def _convert_to_png(self, file_fullpath: str) -> str | None:
        src = file_fullpath
        dst = os.path.splitext(file_fullpath)[0] + self.EXT_PNG
        ret = self._change_ext(src, dst)
        return dst if ret else None

    def _change_ext(self, src: str, dst: str) -> bool:
        ffmpeg_cmd = [self.ffmpeg_path, "-i", src, dst]
        try:
            subprocess.run(
                ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True
            )
        except subprocess.CalledProcessError as e:
            self.logger.debug(f"{e}\tcmd: '{ffmpeg_cmd}'")
            self.logger.error("Error during converting extensions.")
            return False
        return True

    def _set_thumbnail(self, video_path: str, img_path: str) -> bool:
        if self.download_mode in [DownloadMode.M4A, DownloadMode.WAV]:
            self.logger.warning(
                "Image cannot be embedded in audio files. A image is saved instead."
            )
            return False
        # To avoid duplicate names for input and output files, rename original name
        TMP_STR = "IN_SET_THUMBNAIL"
        split_path = os.path.splitext(video_path)
        tmp_video_path = split_path[0] + TMP_STR + split_path[1]
        ffmpeg_cmd = [
            "ffmpeg",
            "-i",
            video_path,
            "-i",
            img_path,
            "-c",
            "copy",
            "-map",
            "1",
            "-map",
            "0",
            "-disposition:v:0",
            "attached_pic",
            tmp_video_path,
        ]
        try:
            subprocess.run(
                ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True
            )
        except subprocess.CalledProcessError as e:
            self.logger.debug(e)
            self.logger.warning("Error during setting thumbnail.")
            return False
        self._post_set_thumbnail(tmp_video_path, video_path)
        return True

    def _post_set_thumbnail(self, old_video_path: str, new_video_path: str) -> None:
        self.logger.debug(f"old -> new '{old_video_path}'->'{new_video_path}'.")
        os.remove(new_video_path)
        os.rename(old_video_path, new_video_path)


class VideoDownloaderQueue:
    def __init__(
        self, ydl_opts: DlYdlOpts, option: dict[str, Any], thread_count: int = 4
    ) -> None:
        LoggerConfigurator()
        self.logger = getLogger()

        self.downloaders: list[VideoDownloader] = []
        self.thread_count: int = 0
        self._set_download_option(ydl_opts, option, thread_count)

    def _set_download_option(
        self, ydl_opts: DlYdlOpts, option: dict[str, Any], thread_count: int
    ) -> None:
        self.downloaders = [
            VideoDownloader(ydl_opts, option) for _ in range(thread_count)
        ]
        self.thread_count = thread_count

    def start_download(self, urls_filename_q: UrlsFilenameQ) -> DownloadStatusUrlsQ:
        download_status_urls_q: DownloadStatusUrlsQ = Queue()
        total_urls_len: int = urls_filename_q.qsize()

        self.logger.info("Start downloading the video.")
        with ThreadPoolExecutor(max_workers=self.thread_count) as e:
            futures = [
                e.submit(
                    self._download_videos_via_queue,
                    downloader,
                    urls_filename_q,
                    download_status_urls_q,
                    total_urls_len,
                )
                for downloader in self.downloaders
            ]

            for future in as_completed(futures):
                future.result()
        self.logger.info("Downloading of the video is completed.")
        return download_status_urls_q

    def _download_videos_via_queue(
        self,
        downloader: VideoDownloader,
        urls_filename_q: UrlsFilenameQ,
        download_status_urls_q: DownloadStatusUrlsQ,
        total_urls_len: int,
    ) -> None:
        while True:
            try:
                url, filename = urls_filename_q.get(timeout=2)
            except queue.Empty:
                self.logger.debug("Empty queue. This thread is closed.")
                # _for_debug(mess="This thread is closed")  # for debug
                return
            download_state = downloader.download_videos(url, filename)
            download_status_urls_q.put((download_state, url))
            self.logger.info(
                f"Progress: {download_status_urls_q.qsize()} / {total_urls_len}"
            )

            # _for_debug("DL")  # for debug

    def display_result(self, status_urls_q: DownloadStatusUrlsQ) -> None:
        failures_urls_q: Queue[str] = Queue()
        result: dict[str, int] = {"successes": 0, "failures": 0}

        while not status_urls_q.empty():
            state, url = status_urls_q.get()
            if not state:
                result["failures"] += 1
                failures_urls_q.put(url)
            else:
                result["successes"] += 1
        if failures_urls_q.qsize() != 0:
            self._display_failures_detail(failures_urls_q)
        self.logger.info(
            f"All downloads completed. Success / Total: '{result['successes']} / "
            f"{result['failures'] + result['successes']}'"
        )

    def _display_failures_detail(self, failures_urls_q: Queue[str]) -> None:
        self.logger.info("Below is a list of URLs that failed to downloaded.")
        while not failures_urls_q.empty():
            url = failures_urls_q.get()
            self.logger.info(f"\t> '{url}'")


def _for_debug(mess: str = ""):
    """Check if all threads are runnning, based on the DL end time of each video."""
    now = datetime.now()
    name = current_thread().name
    now = now.strftime("%H-%M-%S") + " " + name + " " + mess
    path: str = ""

    with open(path, "a") as f:
        f.write(f"{now}\n")
