# Video Downloader

![Python](https://img.shields.io/badge/-Python-F2C63C.svg?logo=python&style=for-the-badge)

___

## Introduction

`yt-dlp`を使用してYouTube上から簡単に動画をダウンロードできます。再生リストのダウンロードも対応しており、パフォーマンス向上のためマルチスレッドを使用しています。<br>
This project allows you to easily download videos from YouTube using `yt-dlp`. It supports downloading playlists and utilizes multi-threading for improved performance and ease of use.

## Environment

| Languages / Frameworks | Version |
| ---------------------- | ------- |
| Python                 | 3.12.2  |
| (ffmpeg)               | 7.0     |

For other package versions, please refer to `requirements.txt`.

`ffmpeg` is required to use all functions.
`ffmpeg` official site [here](https://ffmpeg.org/download.html).

## Development Environment Setup

To set up the development environment, follow these steps:

1. Clone the repository:

    ```bash
    git clone https://github.com/konattsu/video_downloader.git
    ```

2. Install the required packages:

    ```bash
    pip install -r requirements.txt
    ```

## Usage

> [!NOTE]
> 基本的にはコマンドラインに従うことで動画をダウンロードできます。<br>
> Basically, you can download the video by following the command line.

To use the tool, follow these steps:

1. **Run the Tool**:

    ```bash
    python ./main.py
    ```

    また、以下のように`cookiefile`を指定することでアカウント情報を使用し限定公開動画をダウンロードできます(アクセスするための権利が必要です)。`yt-dlp`の[このコード](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py)内にある`cookiefile`というオプションを使用しています(先頭のほうにドキュメンテーション文字列で記載があります)。例えばこのファイルを入手するために、chromeを使用しているのであれば[拡張機能](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)等を利用して入手可能です。<br>
    You can also download limited public videos using your account information by specifying a `cookiefile` as follows (you need the right to access it), using the option `cookiefile` in [this code](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py) in `yt-dlp` (it is mentioned in the documentation string at the beginning). For example, if you are using chrome to obtain this file, you can use [extensions](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc), etc. to obtain it.

    ```bash
    python ./main.py --cookiefile ./cookiefile.txt
    ```

    <br>

2. **Select storage folders**

    Specify the path of the folder where videos and thumbnails are stored.
    <br>

3. **Choice to use or not to use `ffmpeg`**

    `ffmpeg`を使用すると動画を音声ファイルに変換したり、サムネイルの画像形式を変更できます。<br>
    `ffmpeg` can be used to convert videos to audio files and change the thumbnail image format.
    <br>

4. **Enter the urls**

    ダウンロードしたい動画のurlを入力します。再生リストが混ざっていても大丈夫です。またurlが入力されたcsvファイルから読み取ることもできます。<br>
    Enter the url of the video you want to download. It is okay if the playlists are mixed up; you can also read from a csv file where the url has been entered.<br>
    再生リストが含まれている場合はダウンロードする範囲を指定します。<br>
    Specify the range to download if a playlist is included.

    <br>

5. **Select download options**

    ダウンロード時の画質、ファイル名、サムネイルなどを選択します。一部機能は`ffmpeg`が必要です。<br>
    Select the video quality, file name and thumbnail for downloading. Some functions require `ffmpeg`.

    <br>

6. **Start downloading**

    ダウンロードが開始されます。存在しないurlやアクセス権限がないurlはダウンロードできず、最後に表示されます。<br>
    The download will start. URLs that do not exist or for which you do not have access rights cannot be downloaded and will be displayed at the end.

## Features

- 再生リストのダウンロード
- マルチスレッドの使用で高速化
- 画質、サムネイル、タイトルの柔軟な指定

- Download entire playlists.
- Multi-threaded downloading for faster performance.
- Flexible specification of video quality, thumbnails and titles

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
