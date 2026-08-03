from pathlib import Path

import yt_dlp


def download_video_4k(url):
    save_path = Path.home() / "Downloads"
    # オプション設定
    ydl_opts = {
        # 'bestvideo+bestaudio/best' は、最高画質の映像と最高音質の音声をダウンロードし、
        # それらが利用できない場合は単一ファイルで最高画質のものを取得するという指定です。
        "format": "bestvideo+bestaudio",
        # 映像と音声を結合してmp4にする設定（FFmpegが必要です）
        "merge_output_format": "mp4",
        # 保存するファイル名の形式（動画タイトル.拡張子）
        "outtmpl": str(save_path / "%(title)s.%(ext)s"),
        # エラー無視やプレイリストダウンロードの可否など
        "ignoreerrors": True,
        "js_runtimes": {"node": {"path": None}},
        "remote_components": ["ejs:github"],
        "cookiesfrombrowser": ("chrome",),
        "extractor_args": {
            "youtube": {"player_client": ["tv_downgraded", "web_embedded"]}
        },
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"ダウンロードを開始します: {url}")
            ydl.download([url])
            print("ダウンロードが完了しました。")
    except Exception as e:
        print(f"エラーが発生しました: {e}")


if __name__ == "__main__":
    target_url = ""
    download_video_4k(target_url)
