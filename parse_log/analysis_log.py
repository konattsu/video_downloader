"""
video_download.pyの_for_debug関数を解析するやつ
驚きの100%ChatGPT製
"""
from collections import defaultdict
from datetime import datetime

# ログファイルのパス
log_file = ""

# スレッドのインデックスごとの時間差を格納する辞書
thread_timings = defaultdict(list)

# スレッドのインデックスの頻度を格納する辞書
thread_index_count = defaultdict(int)

# ログファイルを読み込む
with open(log_file, "r") as file:
    for line in file:
        # 時刻とスレッド名を取得
        parts = line.strip().split()
        timestamp_str = parts[0]
        thread_name = parts[-2]

        # 時刻文字列を datetime オブジェクトに変換
        timestamp = datetime.strptime(timestamp_str, "%H-%M-%S")

        # スレッドのインデックスを取得
        thread_index = thread_name.split("_")[-1]

        # スレッドの動作が終了したかどうかをチェック
        if "This thread is closed" not in line:
            # スレッドの動作が終了していない場合、直前の時刻を取得して時間差を計算
            thread_timings[thread_index].append(timestamp)
            if len(thread_timings[thread_index]) > 1:
                time_difference = timestamp - thread_timings[thread_index][-2]
                print(f"Thread {thread_index}: Time Difference: {time_difference}")

        # スレッドのインデックスの頻度をカウント
        thread_index_count[thread_index] += 1

# スレッドのインデックスの頻度を出力
print("\nThread Index Frequency:")
for index, count in thread_index_count.items():
    print(f"Thread {index}: {count}")
