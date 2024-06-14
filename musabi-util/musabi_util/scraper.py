import datetime
import json
import os
import re
import time
from pathlib import Path
from typing import Any

import yt_dlp
from dotenv import load_dotenv
from loguru import logger


def main(playlist_url: str, output_dir: str = "outputs") -> None:
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=False)
    params = {
        "format": "bestaudio/best",
        "outtmpl": str(output_path / "%(id)s.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "128",
            },
        ],
        "quiet": True,
        "extract_flat": True,
    }
    with yt_dlp.YoutubeDL(params) as ydl:
        playlist_info = ydl.extract_info(playlist_url, download=False)
        entries = playlist_info.get("entries", [])
        for i, entry in enumerate(entries):
            url = entry["url"]
            logger.info(
                f"Extracting {entry['title']} {url} ({i+1}/{len(entries)})",
            )
            try:
                _save_info(output_path, ydl.extract_info(url, download=False))
                ydl.download([url])
            except yt_dlp.DownloadError:
                logger.info(f"Failed to download {url}")


def _save_info(output_path: Path, info: dict[str, Any]) -> None:
    parsed = _parse_description(info["description"])
    with (output_path / f"{info['id']}.json").open(
        "w",
        encoding="utf8",
    ) as f:
        json.dump(parsed, f, ensure_ascii=False)


def _parse_description(description: str) -> list[dict[str, int | str]]:
    results = []
    pattern = re.compile(r"\[(.*)\] (.*)")
    for desc in description.split("\n"):
        matches = pattern.match(desc)
        if matches:
            time_str, title = matches.groups()
            results.append({"title": title, "timestamp": _strpsec(time_str) * 1000})
    return results


def _strpsec(time_str: str) -> int:
    if time_str.count(":") == 1:
        t = time.strptime(time_str, "%M:%S")
    else:
        t = time.strptime(time_str, "%H:%M:%S")
    return int(
        datetime.timedelta(
            hours=t.tm_hour,
            minutes=t.tm_min,
            seconds=t.tm_sec,
        ).total_seconds(),
    )


if __name__ == "__main__":
    load_dotenv()
    main(os.environ["PLAYLIST_URL"])
