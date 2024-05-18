from logging import getLogger
from re import search
from typing import Any

import yt_dlp
from logger_config import LoggerConfigurator
from types_config import ExYdlOpts, UrlData, UrlsDataList

Metadata = dict[str, Any]


class AnalysisUrls:
    """A class for analyzing YouTube video URLs and retrieving information."""

    def __init__(self, cookiefile: str = "") -> None:
        """Initialize the AnalysisUrls object.

        Args:
            cookiefile (str, optional): Path to the cookie file. Defaults to "".

        Attributes:
            logger: Logger object for logging messages.
            cookie_filepath (str): Path to the cookie file.
            _specified_cookie (bool): True if cookiefile is specified, False otherwise.
            _tmp_directly_specified_idx (int): Temporary index used during analysis.
            _same_playlist_idx (int): Used to assign different values for each playlist.

        Example:
            >>> analyzer = AnalysisUrls(cookiefile="dir/cookies.txt")
        """

        LoggerConfigurator()
        self.logger = getLogger()

        self.cookie_filepath: str = cookiefile
        self._specified_cookie: bool = True if cookiefile != "" else False
        self._tmp_directly_specified_idx: int = 0
        self._same_playlist_idx: int = 0

    def get_urls_data(self, urls: list[str]) -> UrlsDataList:
        """Get information for a list of URLs.

        Args:
            urls (List[str]): A list of URLs for which information is desired.

        Returns:
            UrlsData: A list containing information for each URL.

        Note:
            If index is non-zero, it is the index of the playlist.
            The index of the playlist starts from 1.
            same_playlist: If it's 1 or more, videos in the same playlist.
            Otherwise(it's 0), normal videos.

        Example:
            In this example, assume 'playlist cba321' includes 'aa11' and 'bb22'.
            >>> urls = ["https://www.youtube.com/playlist?list=cba321",
                        "https://www.youtube.com/watch?v=abc123"]
            >>> analyzer = AnalysisUrls()
            >>> result = analyzer.get_urls_data(urls)
            >>> print(result)
            [
                {
                    "url": "https://www.youtube.com/watch?v=aa11",
                    "title": "Sample Title 1",
                    "index": 1,
                    "same_playlist": 1,
                    "directly_specified": False,
                },
                {
                    "url": "https://www.youtube.com/watch?v=bb22",
                    "title": "Sample Title 2",
                    "index": 2,
                    "same_playlist": 1,
                    "directly_specified": False,
                },
                {
                    "url": "https://www.youtube.com/watch?v=abc123",
                    "title": "Sample Title 3",
                    "index": 0,
                    "same_playlist": 0,
                    "directly_specified": True,
                },
            ]
        """

        urls_with_data: UrlsDataList = []
        for idx, url in enumerate(urls, start=1):
            self.logger.info(f"Url: {url}")
            ret = self._analyze_metadata(url)
            if ret is None:
                continue
            urls_with_data.extend(ret)
            self.logger.info(f"Progress: {idx} / {len(urls)}")
        return urls_with_data

    def _analyze_metadata(self, url: str) -> list[UrlData] | None:
        ret_url_data: list[UrlData] = []
        info = self._download_metadata(url)
        if info is None:
            self.logger.warning(f"Failed to retrieve video metadata. Url: {url}")
            return None
        try:
            # When the url of the playlist 'itself' is specified
            entries = info["entries"]
            ret_url_data = self._retrieving_info_from_entries(
                entries, directly_specified_idx=self._tmp_directly_specified_idx
            )
            self._tmp_directly_specified_idx = 0
        except KeyError:
            if "&list=" in info["webpage_url"]:
                # When specifying the url of a video in the playlist
                # Search for the index of a video in a directly specified playlist
                ret = self._search_index_of_video(info["webpage_url"])
                if ret == 0:
                    self.logger.error(f"Unexpected webpage_url: {info['webpage_url']}")
                    # TODO これが発生してしまう条件をより詳しく調べる
                self._tmp_directly_specified_idx = ret
                # Recursive call with the url of the playlist itself as an argument
                ret = self._analyze_metadata(url=info["url"])
                if ret is None:
                    self.logger.error(f"Unexpected url: '{url}'.")
                    return None
                ret_url_data = ret
            else:
                # When it is a normal video, Not in playlist.
                ret_url_data.append(
                    self._create_url_data(url=info["webpage_url"], title=info["title"])
                )
        # For a playlist, the number of elements in the return value is equal
        # to the number of videos in the playlist (When normal url)
        return ret_url_data

    def _download_metadata(
        self, url: str, extract_flat: bool = True
    ) -> Metadata | None:
        ex_ydl_opts: ExYdlOpts = {"extract_flat": extract_flat, "quiet": True}
        if self._specified_cookie:
            ex_ydl_opts["cookiefile"] = self.cookie_filepath
        with yt_dlp.YoutubeDL(ex_ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url=url, download=False)
            except yt_dlp.DownloadError:
                return None
        return info

    def _create_url_data(
        self,
        url: str,
        title: str,
        index: int = 0,
        same_playlist: int = 0,
        directly_specified: bool = True,
    ) -> UrlData:
        return {
            "url": url,
            "title": title,
            "index": index,
            "same_playlist": same_playlist,
            "directly_specified": directly_specified,
        }

    def _search_index_of_video(self, url: str) -> int:
        match = search(r"&index=(\d+)", url)
        if match:
            return int(match.group(1))
        else:
            self.logger.error("Failure to retrieve index from playlist")
            # index of playlist starts from 1, returns 0 in case of error
            return 0

    def _retrieving_info_from_entries(
        self, entries: Any, directly_specified_idx: int = 0
    ) -> list[UrlData]:
        ret_urls_data: list[UrlData] = []
        self._same_playlist_idx += 1
        for idx, entry in enumerate(entries, start=1):
            directly_specified = True if idx == directly_specified_idx else False
            ret_urls_data.append(
                self._create_url_data(
                    entry["url"],
                    entry["title"],
                    index=idx,
                    same_playlist=self._same_playlist_idx,
                    directly_specified=directly_specified,
                )
            )
        return ret_urls_data

    def get_urls_detailed_data(
        self, urls: list[str], wanted_data: str
    ) -> list[dict[str, Any]]:
        """Get detailed information for a list of video URLs.

        Args:
            urls (List[str]): A list of URLs for which detailed information is desired.
            wanted_data (str): A comma-separated string specifying the data to be
            retrieved for each URL.

        Returns:
            UrlsData: A list containing detailed information with URL for each URL.

        Notes:
            - DO NOT include the playlist in the URLs. If you cannot be sure,
            use a URLs obtained using 'get_urls_with_title' method of the same class.
            - If non-existent data is specified, keyerror is generated.
            - Refer to the Output Template that exist
            in the https://github.com/yt-dlp/yt-dlp for available data

        Example:
            >>> urls = ["https://www.youtube.com/watch?v=abc123,
                        "https://www.youtube.com/watch?v=def456]
            >>> wanted_data = "upload_date, title"
            >>> analyzer = AnalysisUrls()
            >>> result = analyzer.get_urls_detailed_data(urls, wanted_data)
            >>> print(result)
            [
                {
                    "url": "https://www.youtube.com/watch?v=abc123",
                    "upload_date": "20220101",
                    "title": "Sample Title1",
                },
                {
                    "url": "https://www.youtube.com/watch?v=def456",
                    "upload_date": "20200101",
                    "title": "Sample Title2",
                }
            ]
        """
        # TODO ここ将来的にマルチスレッドに

        data_acquired: list[dict[str, Any]] = []
        want: list[str] = wanted_data.replace(" ", "").split(",")

        for idx, url in enumerate(urls, start=1):
            self.logger.info(f"Url: {url}")
            info = self._download_metadata(url, extract_flat=False)
            if info is None:
                self.logger.warning(f"Failed to retrieve video metadata. Url: '{url}'.")
                continue

            part_data_acquired: dict[str, int | str | bool] = {"url": url}
            for key in want:
                part_data_acquired[key] = info[key]

            data_acquired.append(part_data_acquired)
            self.logger.info(f"Progress: {idx} / {len(urls)}")
        return data_acquired


# if __name__ == "__main__":
#     a = AnalysisUrls()
#     b = a.get_urls_data(
#         [
#             "https://www.youtube.com/playlist?list=PLmNMakH9YANXgpe71TuVKkEePgvYKF358",
#             # "https://youtu.be/m7HF8wlnCc8",
#         ],
#     )
#     print(b)
