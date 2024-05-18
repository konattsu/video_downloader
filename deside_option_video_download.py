import csv
import os
import re
import subprocess
from array import array
from itertools import zip_longest
from logging import getLogger
from typing import Any

from analysis_urls import AnalysisUrls
from enum_config import DownloadMode, FileNameFormat, Thumbnail
from logger_config import LoggerConfigurator
from types_config import DlYdlOpts, Playlist, PlaylistList, UrlsDataList, VideoDataList

UrlTitleIdx = tuple[str, str, int]
UrlsTitleIdxList = list[UrlTitleIdx]

UrlFilename = tuple[str, str]
UrlsFilenameList = list[UrlFilename]

CusOpt = dict[str, Any]


class DesideOptionVideoDownload:
    def __init__(self, cookie_file: str = "") -> None:
        LoggerConfigurator()
        self.logger = getLogger()
        # const
        self.REQUIRED_URL: str = "https://"
        self.EXT_M4A: str = ".m4a"
        self.EXT_MP4: str = ".mp4"
        self.PRIVATE_VIDEO_TITLE: str = "[Private video]"
        # variable
        self.ffmpeg_path: str = ""
        self.dir_path: str = ""
        self.cookie_file: str = cookie_file
        self.download_mode: DownloadMode = DownloadMode.HIGH
        self.thumbnail_mode: Thumbnail = Thumbnail.PLAIN
        self.file_name_fmt: FileNameFormat = FileNameFormat.PLAIN
        self.can_use_ffmpeg: bool = False

    def run(self) -> tuple[DlYdlOpts, CusOpt, UrlsFilenameList] | None:
        urls: list[str] = []

        # start
        self.input_dir_path()

        self.can_use_ffmpeg = self.use_ffmpeg_or()

        self.input_urls(urls)

        url_title_idx_li = self.parse_urls(urls)

        if not url_title_idx_li:
            self.logger.info(
                "Video was not selected or failed to retrieve information."
                " Therefore, it is terminated."
            )
            return None

        self.select_download_mode()

        self.select_thumbnail()

        self.select_filename()

        ydl_opts = self.assembly_ydl_opts()

        multi_url_filename = self.assembly_file_name(url_title_idx_li)

        custom_opt = self.assembly_custom_opt()

        return (ydl_opts, custom_opt, multi_url_filename)

    def input_urls(self, urls: list[str]) -> list[str]:
        USAGE_MESS = (
            "Enter the URLs. Type 'csv' to read URLs from csv file. Press F to finish."
        )
        print(USAGE_MESS)
        while True:
            user_input = input("  > ").strip(" '\"")
            if user_input in ["F", "f"]:
                # Ends when there is more than one url.
                if len(urls) >= 1:
                    return urls
                print("Specify one or more URLs.")
            elif user_input.lower() == "csv":
                self.input_csv_path(urls)
                print(USAGE_MESS)
            elif self.REQUIRED_URL not in user_input:
                # For strings that are not always urls
                print(
                    f"'{user_input}' cannot be used as it doesn't contain "
                    f"'{self.REQUIRED_URL}'."
                )
            else:
                urls.append(user_input)

    def input_csv_path(self, urls: list[str]) -> None:
        print("Enter the path to the CSV file path.")
        while True:
            csv_path = input("  > ").strip(" \"'")
            if os.path.isfile(csv_path):
                break
            print(f"'{csv_path}' does not exist.")
        self.read_from_csv_file(urls, csv_path)

    def read_from_csv_file(self, urls: list[str], file_path: str) -> None:
        with open(file_path) as f:
            reader = csv.reader(f)
            for row in reader:
                row = [url.strip() for url in row]
                for url in row:
                    if self.REQUIRED_URL not in url:
                        # For strings that are not always urls
                        self.logger.info(
                            f"'{url}' cannot be used as it doesn't contain "
                            f"'{self.REQUIRED_URL}'."
                        )
                        continue
                    urls.append(url)
                    self.logger.debug(f"Read url: '{url}'")
        self.logger.info("Urls in the csv file was read.")

    def input_dir_path(self) -> None:
        # Continue when appropriate values are entered.
        if not os.path.isdir(self.dir_path):
            print("Enter the directory path to save files. Relative paths can be used.")
            while True:
                path = input("  > ").strip(" \"'")
                if os.path.isdir(path):
                    self.dir_path = path
                    break
                else:
                    self.logger.warning(f"Cannot be accessed: '{path}'")
        self.logger.info(f"'{self.dir_path}' is selected as the storage location.")

    def use_ffmpeg_or(self) -> bool:
        # Continue when initialized with appropriate values
        ret = self.input_ffmpeg_filepath(only_once=True)
        if ret:
            return True
        ret = self.user_agree(
            "Do you want to use ffmpeg.exe to make all functions available?"
        )
        if ret:
            self.input_ffmpeg_filepath()
            return True
        return False

    def input_ffmpeg_filepath(self, only_once: bool = False) -> bool:
        # Continue when initialized with appropriate values
        ret = self.ffmpeg_execution_test(self.ffmpeg_path, should_log_errors=False)
        if ret:
            return True
        elif only_once:
            return False
        while True:
            path = input("Enter the path of 'ffmpeg.exe'. ").strip(" \"'")
            ret = self.ffmpeg_execution_test(path)
            if ret:
                self.ffmpeg_path = path
                return True

    def ffmpeg_execution_test(
        self, ffmpeg_path: str, should_log_errors: bool = True
    ) -> bool:
        if not ffmpeg_path:
            return False
        self.logger.debug(f"ffmpeg path: '{ffmpeg_path}'.")
        try:
            subprocess.run(
                [ffmpeg_path, "-version"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.logger.info(
                f"'{ffmpeg_path}' is selected as the location for 'ffmpeg.exe'."
            )
            return True
        except FileNotFoundError:
            if should_log_errors:
                self.logger.warning(f"'{ffmpeg_path}' not found.")
        except subprocess.CalledProcessError:
            if should_log_errors:
                self.logger.warning(f"'{ffmpeg_path}' is not available.")
        return False

    def user_agree(self, message: str) -> bool:
        OPT_MESS = "<y/n>"
        while True:
            user_input = input(f"{message} {OPT_MESS} ").lower()
            if user_input in ["yes", "y"]:
                return True
            elif user_input in ["no", "n"]:
                return False
            self.logger.warning(
                f"'{user_input}' is an invalid input. Please enter {OPT_MESS}."
            )

    def parse_urls(self, urls: list[str]) -> UrlsTitleIdxList:
        multi_url_title_idx: UrlsTitleIdxList = []

        self.logger.info("Start parsing the urls.")
        analyzer = AnalysisUrls(cookiefile=self.cookie_file)
        urls_data = analyzer.get_urls_data(urls)
        self.logger.info("Finish parsing the urls.")
        print()

        multi_pl_data, nl_data = self.extract_playlist(urls_data)

        for a in nl_data:
            multi_url_title_idx.append((a["url"], a["title"], 0))

        if len(multi_pl_data) == 0:
            return multi_url_title_idx
        print(f"{len(multi_pl_data)} playlists are included in urls.")
        for idx, pl_data in enumerate(multi_pl_data, start=1):
            print(f"Playlist for the {idx} / {len(multi_pl_data)}.")
            bool_arr = self.select_range_playlist(pl_data)
            for idx, data in enumerate(pl_data):
                if bool_arr[idx]:
                    multi_url_title_idx.append(
                        (data["url"], data["title"], data["index"])
                    )
        return multi_url_title_idx

    def extract_playlist(
        # fmt: off
            self,
            urls_data: UrlsDataList,
        # fmt: on
    ) -> tuple[PlaylistList, VideoDataList]:
        """Methods for extracting playlists.

        Args:
            urls_data (List[Dict[str, Any]]): List of url data. Each data
            is in dictionary format and has an "index" key, which represents the order
            in the playlist.

        Returns:
            tuple[]: Returns a tuple of playlist data and non-playlist data.
            Playlist data is a list containing a list of video data for each playlist.
            Non-playlist data is a list of video data that is not a playlist.

        Example:
            >>> urls_data = urls_data = [
            ...    {
            ...         "url": "video_url_1",
            ...         "title": "Playlist_1",
            ...         "index": 1,
            ...         "same_playlist": 1,
            ...         "directly_specified": False,
            ...     },
            ...     {
            ...         "url": "video_url_2",
            ...         "title": "Playlist_2",
            ...         "index": 2,
            ...         "same_playlist": 1,
            ...         "directly_specified": True,
            ...     },
            ...     {
            ...         "url": "video_url_3",
            ...         "title": "Playlist_3",
            ...         "index": 1,
            ...         "same_playlist": 2,
            ...         "directly_specified": True,
            ...     },
            ...     {
            ...         "url": "video_url_4",
            ...         "title": "Video_1",
            ...         "index": 0,
            ...         "same_playlist": 0,
            ...         "directly_specified": True,
            ...     },
            ... ]
            >>> opts_setter = SetOptionVideoDownload()
            >>> multi_pl_data, non_pl_data = opts_setter.extract_playlist(urls_data)
            >>> print(multi_pl_data)
            [
                {
                    "url": "video_url_1",
                    "title": "Playlist_1",
                    "index": 1,
                    "same_playlist": 1,
                    "directly_specified": False,
                },
                {
                    "url": "video_url_2",
                    "title": "Playlist_2",
                    "index": 2,
                    "same_playlist": 1,
                    "directly_specified": True,
                },
            ], [
                {
                    "url": "video_url_3",
                    "title": "Playlist_3",
                    "index": 1,
                    "same_playlist": 2,
                    "directly_specified": True,
                },
            ]
            >>> print(non_pl_data)
            [
                {
                "url": "video_url_4",
                "title": "Video_1",
                "index": 0,
                "same_playlist": 0,
                "directly_specified": True,
                },
            ]
        """

        multi_pl_data: PlaylistList = []  # Listed by playlist
        nl_data: VideoDataList = []  # Normal video, not a playlist
        pl_data: Playlist = []
        last_idx: int = 0

        for data in urls_data:
            idx: int = data["index"]
            # Skip when it isn't playlist
            if idx == 0:
                nl_data.append(data)
                continue
            # On a different playlist
            if idx < last_idx:
                multi_pl_data.append(pl_data)
                pl_data = []
            pl_data.append(data)
            last_idx = idx
        # When ended up on the playlist
        if pl_data:
            multi_pl_data.append(pl_data)
        return multi_pl_data, nl_data

    def select_range_playlist(self, pl_data: Playlist) -> array:
        USAGE = (
            "Specify the range to be downloaded by index. "
            "Specifying outside the range will be ignored. "
            "Multiple designations can be comma-separated.\n"
            "You can also use the following notation.\n"
            "F:        Exit selection\n"
            "all:      Select all\n"
            "original: Only the specified videos\n"
            "display:  Display current selection\n"
            "reset:    Deselect All\n"
            "usage:    Display how to use\n"
            "1, 5-7:   Meaning 1, 5, 6, 7"
        )
        bool_arr = array("b", [0] * len(pl_data))

        for data in pl_data:
            if data["title"] != self.PRIVATE_VIDEO_TITLE:
                print(f"\t{data['index']:3d}: {data['title']}")
        print(USAGE)
        while True:
            text = re.sub(r"\s+", "", input("  > ").lower())
            parts = text.split(",")
            parts = [a for a in parts if a != ""]
            for part in parts:
                if part == "f":
                    self.logger.info("Finish range selection.")
                    self.disable_private_videos(bool_arr, pl_data)
                    return bool_arr
                elif part == "usage":
                    print(USAGE)
                    continue
                ret = self.analyze_range_input(part, pl_data, bool_arr)
                if not ret[0]:
                    self.logger.info(
                        f"Entered '{part}' is skipped due to syntax error."
                    )
                elif not ret[1]:
                    self.logger.info(
                        "The out-of-range portion of the entered value was ignored."
                    )

    def analyze_range_input(
        self, part: str, pl_data: Playlist, bool_arr: array
    ) -> tuple[bool, bool]:
        """Set the specified range to True.

        Args:
            part (str): String representing a range. (lower-case)
            pl_data (Playlist): A list of playlist from which to select
            a range.
            bool_arr (array): Download each video in the playlist or.

        Returns:
            tuple[bool, bool]: A tuple indicating the status of the selected content:
            First, if the syntax is correct, Second, if the range is correct.
            If the syntax is invalid, the second value will also be false.
        """

        RET_CORRECT = (True, True)
        RET_SYNTAX_ERROR = (False, False)
        RET_RANGE_ERROR = (True, False)

        if part == "all":
            self.array_bool_change(bool_arr, 0, len(bool_arr) - 1)
            return RET_CORRECT
        elif part == "original":
            for data in pl_data:
                if data["directly_specified"]:
                    bool_arr[data["index"] - 1] = True
                    return RET_CORRECT
            # Since the url of the playlist itself is specified
            return RET_RANGE_ERROR
        elif part == "display":
            for idx, (data, state) in enumerate(zip(pl_data, bool_arr), start=1):
                state = "True" if state else "F"
                title = data["title"]
                if title != self.PRIVATE_VIDEO_TITLE:
                    print(f"\t{idx:3d}: {state}, \tTitle: '{title}'")
            return RET_CORRECT
        elif part == "reset":
            self.array_bool_change(bool_arr, 0, len(bool_arr) - 1, value=False)
            return RET_CORRECT

        repatter = re.compile(r"[^\d-]")
        result = repatter.search(part)
        # When invalid characters are included
        if result is not None:
            return RET_SYNTAX_ERROR
        # When a single number is specified
        elif part.isdigit():
            a = int(part)
            if 1 <= a <= len(bool_arr):
                bool_arr[a - 1] = True
            else:
                return RET_RANGE_ERROR
        # When the format is as 1-4
        else:
            repatter = re.compile(r"\d+-\d+")
            result = repatter.match(part)
            if result is None:
                return RET_SYNTAX_ERROR
            dust = list(map(int, part.split("-")))
            dust.sort()
            out_of_range = self.array_bool_change(bool_arr, dust[0] - 1, dust[1] - 1)
            if out_of_range:
                return RET_RANGE_ERROR
        return RET_CORRECT

    def disable_private_videos(self, bool_arr: array, pl_data: Playlist) -> None:
        for i, data in enumerate(pl_data):
            if data["title"] == self.PRIVATE_VIDEO_TITLE:
                bool_arr[i] = False  # TODO 似ているやつ別メソッドに

    def array_bool_change(
        # fmt: off
            self, array: array, first: int, last: int, value: bool = True
        # fmt: on
    ) -> bool:
        out_of_range = False
        if first < 0:
            first = 0
            out_of_range = True
        try:
            for i in range(first, last + 1):
                array[i] = value
        except IndexError:
            out_of_range = True
        return out_of_range

    def select_download_mode(self) -> None:
        MODE_DICT = {
            "1": "Max quality",
            "2": "High quality",
            "3": "Normal quality, 720p or less",
            "4": "Low quality, 480p or less",
            "5": "Only audio, ext=m4a",
            "6": "Only audio, ext=wav",
        }
        MODE_NOTE = (
            "Note: The sound quality does not change between 5 and 6, "
            "but the file size of 6 is very large. 6 requires 'ffmpeg.exe'."
        )

        print("Select the type of file to download.")
        ret = self.input_enum_value(MODE_DICT, MODE_NOTE, list("6"))
        self.download_mode = DownloadMode(ret)

    def select_thumbnail(self) -> None:
        MODE_DICT = {
            "1": "Nothing",
            "2": "Get thumbnails, ext=webp",
            "3": "Get thumbnails, ext=png",
            "4": "Set thumbnails",
            "5": "Get and Set thumbnails, ext=png",
        }
        MODE_NOTE = (
            "Thumbnails cannot be specified if the download format is an audio file. "
            "3 to 5 require 'ffmpeg.exe'. When embedding a thumbnail, "
            "add the image to the very first frame of the video."
        )

        print("Select settings about thumbnails.")
        ret = self.input_enum_value(MODE_DICT, MODE_NOTE, list("345"))
        self.thumbnail_mode = Thumbnail(ret)

    def select_filename(self) -> None:
        MODE_DICT = {
            "1": "T",
            "2": "D + T",
            "3": "T + D",
            "4": "X + T",
            "5": "T + X",
            "6": "D + T + X",
            "7": "D + X + T",
            "8": "X + T + D",
            "9": "X + D + T",
            "10": "T + X + D",
            "11": "T + D + X",
        }
        MODE_NOTE = (
            "D: Upload Date, X: index, T: Title.\n"
            "'index' means the index of the playlist. If it isn't playlist, "
            "nothing is entered in the index. The options to use 'date' "
            "takes a little longer."
        )

        print("Select the type of file name to download.")
        ret = self.input_enum_value(MODE_DICT, MODE_NOTE, [""])
        self.file_name_fmt = FileNameFormat(ret)

    def input_enum_value(
        # fmt: off
            self,
            mode_dict: dict[str, str],
            mode_note: str,
            requires_ffmpeg: list[str],
        # fmt: on
    ) -> int:
        for key, value in mode_dict.items():
            print(f" {key:2}: {value}")
        print(mode_note)
        while True:
            user_input = input("  > ").strip(" ")
            if user_input not in mode_dict:
                print("Invalid input.")
            elif (not self.can_use_ffmpeg) and (user_input in requires_ffmpeg):
                print(
                    "This option is not available due to the absence of 'ffmpeg.exe'."
                )
            else:
                self.logger.info(f"{mode_dict[user_input]} is selected.")
                print()
                return int(user_input) - 1

    def assembly_ydl_opts(self) -> DlYdlOpts:
        ydl_opts: DlYdlOpts = {
            "format": self.get_download_mode(),
            "writethumbnail": self.get_thumbnail_mode(),
            "outtmpl": "deletion prohibited",
        }
        if self.cookie_file:
            ydl_opts["cookiefile"] = self.cookie_file
        return ydl_opts

    def get_thumbnail_mode(self) -> bool:
        if self.thumbnail_mode == Thumbnail.PLAIN:
            return False
        return True

    def get_download_mode(self) -> str:
        format_opt = {
            DownloadMode.MAX: "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/"
            "best",
            DownloadMode.HIGH: "best[fps<=30]",
            DownloadMode.NORMAL: "best[height<=720][fps<=30]",
            DownloadMode.LOW: "best[height<=480][fps<=30]",
            DownloadMode.M4A: "bestaudio[ext=m4a]",
            DownloadMode.WAV: "bestaudio[ext=m4a]",
        }
        return format_opt[self.download_mode]

    def assembly_file_name(
        # fmt: off
            self, url_title_idx_li: UrlsTitleIdxList
        # fmt: on
    ) -> UrlsFilenameList:
        multi_url_filename: UrlsFilenameList = []
        # Get the order of items for file names
        combination_dict: dict[str, int] = self.calculate_combination()
        combination: tuple[str, ...] = tuple(
            key
            for key, value in sorted(combination_dict.items(), key=lambda x: x[1])
            if value != -1
        )
        # Get the upload date, only if upload date is used as the file name
        multi_upload_date: list[str] = []
        if "upload_date" in combination:
            multi_upload_date = self.get_upload_date(
                [url_title_idx[0] for url_title_idx in url_title_idx_li]
            )
        # Create a list of file name and url tuples
        for url_title_idx, upload_date in zip_longest(
            url_title_idx_li, multi_upload_date
        ):
            url_filename = self.assembly_filename(
                url_title_idx,
                upload_date,
                combination,
            )
            multi_url_filename.append(url_filename)
        return multi_url_filename

    def calculate_combination(self) -> dict[str, int]:
        T = "title"
        D = "upload_date"  # TODO upload_dateを色んな箇所でめっちゃ使っとるから
        X = "index"  # 定数として定義するのはありかも
        FMT_ORDER = {
            FileNameFormat.PLAIN: [T],
            FileNameFormat.D_T: [D, T],
            FileNameFormat.T_D: [T, D],
            FileNameFormat.X_T: [X, T],
            FileNameFormat.T_X: [T, X],
            FileNameFormat.D_T_X: [D, T, X],
            FileNameFormat.D_X_T: [D, X, T],
            FileNameFormat.X_D_T: [X, D, T],
            FileNameFormat.X_T_D: [X, T, D],
            FileNameFormat.T_D_X: [T, D, X],
            FileNameFormat.T_X_D: [T, X, D],
        }
        combination: dict[str, int] = {
            D: -1,
            X: -1,
            T: -1,
        }
        if self.file_name_fmt not in FMT_ORDER:
            raise ValueError(f"Unsupported file name format: {self.file_name_fmt}")
        order = FMT_ORDER[self.file_name_fmt]
        for i, item in enumerate(order):
            combination[item] = i
        return combination

    def get_upload_date(self, urls: list[str]) -> list[str]:
        UPLOAD_DATE = "upload_date"
        multi_upload_date: list[str] = []

        self.logger.info("Start getting the upload date.")
        analyzer = AnalysisUrls(cookiefile=self.cookie_file)
        multi_data = analyzer.get_urls_detailed_data(urls, UPLOAD_DATE)
        self.logger.info("Finish getting the upload date.")
        for data in multi_data:
            date = data[UPLOAD_DATE]
            if not isinstance(date, str):
                self.logger.error(f"Unexpected error. Date: '{date}'")
                date = "ERROR"
            multi_upload_date.append(date)
        return multi_upload_date

    def assembly_filename(
        # fmt:off
            self,
            url_title_idx: UrlTitleIdx,
            upload_date: str | None,
            combination: tuple[str, ...],
        # fmt:on
    ) -> UrlFilename:
        DELIM = ","
        filename: str = ""
        ext: str = ""
        url, title, idx = url_title_idx

        for item in combination:
            if item == "upload_date":
                if upload_date is None:
                    # TODO ほかにもあるUnexpected errorが起きた時に呼び出すメソッド
                    # ログ保存用のメソッド作る
                    self.logger.error("Unexpected error in 'assembly_filename'.")
                    continue
                filename += upload_date
            elif item == "title":
                filename += self.remove_symbols(title)
            elif item == "index" and idx != 0:
                filename += str(idx)
            # When index is specified but not a playlist
            else:
                continue
            filename += DELIM
        if self.download_mode in [DownloadMode.M4A, DownloadMode.WAV]:
            ext = self.EXT_M4A
        else:
            ext = self.EXT_MP4
        return (url, filename.strip(DELIM) + ext)

    def remove_symbols(self, string: str) -> str:
        pattern = re.compile(r"\W")
        ret = pattern.sub("", string)
        return ret

    def assembly_custom_opt(self) -> CusOpt:
        return {
            "dir_path": self.dir_path,
            "ffmpeg_path": self.ffmpeg_path,
            "download_mode": self.download_mode,
            "thumbnail_mode": self.thumbnail_mode,
        }


# 全メソッド名取得 __で始まる特殊メソッド除外
# if __name__ == "__main__":
#     methods = [
#         method
#         for method in SetOptionVideoDownload.__dict__
#         if callable(getattr(SetOptionVideoDownload, method))
#         and not method.startswith("__")
#     ]
#     print(methods)
