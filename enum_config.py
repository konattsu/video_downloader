from enum import Enum


class DownloadMode(Enum):
    MAX = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    M4A = 4
    WAV = 5


class Thumbnail(Enum):
    PLAIN = 0
    GET_WEBP = 1
    GET_PNG = 2
    SET = 3
    GET_AND_SET = 4


class FileNameFormat(Enum):
    """D: date, T: title, X: index"""

    PLAIN = 0
    D_T = 1
    T_D = 2
    X_T = 3
    T_X = 4
    D_T_X = 5
    D_X_T = 6
    X_T_D = 7
    X_D_T = 8
    T_X_D = 9
    T_D_X = 10
