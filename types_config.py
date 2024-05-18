from typing import TypedDict, NotRequired
from queue import Queue


class UrlData(TypedDict):
    url: str
    title: str
    index: int
    same_playlist: int
    directly_specified: bool


UrlsDataList = list[UrlData]
"""list[UrlData] may be used instead of UrlsDataList on a dare"""


# ==================== ====================
class VideoData(UrlData):
    url: str
    title: str
    index: int
    same_playlist: int
    directly_specified: bool


VideoDataList = list[VideoData]
Playlist = list[VideoData]
PlaylistList = list[Playlist]


# ==================== ====================
# For ydl_opts
class YdlOpts(TypedDict):
    quiet: NotRequired[bool]
    cookiefile: NotRequired[str]


class ExYdlOpts(YdlOpts):
    extract_flat: bool


class DlYdlOpts(YdlOpts):
    outtmpl: str
    format: str
    writethumbnail: bool
    noprogress: NotRequired[bool]


UrlsFilenameQ = Queue[tuple[str, str]]

# https://qiita.com/simonritchie/items/63218b0a5c4a3d3632a1
# https://typing.readthedocs.io/en/latest/spec/


pass
"""
main.pyとなにかで使うやつもここに入れていい
-> 複数ファイルから使用するものだと自由に定義してOK

set_opt... にあるクラスの__init__でcookie_fileを引数にとってもいいかも

"""
