import json
import os
from pathlib import Path
from typing import TypedDict

from dotenv import load_dotenv
from loguru import logger
from moviepy.editor import (
    CompositeVideoClip,
    ImageClip,
    VideoFileClip,
    concatenate_videoclips,
)


class ImageMovieSettings(TypedDict):
    pre_time: int
    fade_time: int
    post_time: int


class MovieBatchSettings(TypedDict):
    movie_batch: list[ImageMovieSettings]


class Settings(TypedDict):
    movies: list[MovieBatchSettings]


def load_settings() -> Settings:
    with Path("movie.settings.json").open("r") as f:
        return json.load(f)


def main() -> None:
    prj_path = Path(os.environ["PROJECT_PATH"])
    settings = load_settings()
    for movie_idx, setting in enumerate(settings["movies"]):
        movie_names, start_times = [], []
        start_time = 0
        for file_idx, batch_setting in enumerate(setting["movie_batch"]):
            movie_name = fade_image(
                prj_path,
                batch_setting["pre_time"],
                batch_setting["fade_time"],
                batch_setting["post_time"],
                movie_idx,
                file_idx,
            )
            movie_names.append(movie_name)
            start_times.append(start_time)
            start_time = (
                start_time
                + batch_setting["pre_time"]
                + batch_setting["fade_time"]
                + batch_setting["post_time"]
            )
        merge_movie(prj_path, movie_names, start_times, movie_idx)


def merge_movie(
    project_path: Path,
    movie_names: list[str],
    start_times: list[int],
    movie_idx: int = 0,
) -> None:
    clips = []
    logger.info(f"Movies: {movie_names}")
    logger.info(f"Start times: {start_times}")
    for name, start in zip(movie_names, start_times, strict=True):
        clips.append(
            VideoFileClip(str(project_path / name))
            .set_start(start)
            .set_position((0, 0)),
        )
    merged_clip = CompositeVideoClip(clips)
    merged_clip.write_videofile(
        str(project_path / f"{movie_idx}_fade_video.mp4"),
        fps=60,
    )


def fade_image(
    project_path: Path,
    pre_time: int,
    fade_time: int,
    post_time: int,
    movie_idx: int = 0,
    file_idx: int = 0,
) -> str:
    before_clip = ImageClip(
        str(project_path / f"{movie_idx}_image-{file_idx}-.png"),
        duration=pre_time + fade_time + post_time,
    )
    after_clip = ImageClip(
        str(project_path / f"{movie_idx}_image-{file_idx+1}-.png"),
        duration=fade_time + post_time,
    )
    before_clip = before_clip.set_start(0).set_position((0, 0))
    change_clip = (
        after_clip.crossfadein(fade_time).set_start(pre_time).set_position((0, 0))
    )
    merged_clip = CompositeVideoClip([before_clip, change_clip])
    result_name = f"{movie_idx}_fade_video_{file_idx}.mp4"
    merged_clip.write_videofile(str(project_path / result_name), fps=60)
    return result_name


def fade_movie(
    project_path: Path,
) -> None:
    before_clip = VideoFileClip(
        str(project_path / "image-1_animation.mp4"),
    ).loop(duration=30)
    change_clip = VideoFileClip(
        str(project_path / "image-2_animation.mp4"),
    ).loop(duration=27)
    before_clip = before_clip.set_start(0).set_position((0, 0))
    change_clip = change_clip.crossfadein(20).set_start(3).set_position((0, 0))
    merged_clip = CompositeVideoClip([before_clip, change_clip])
    merged_clip.write_videofile(
        str(project_path / "fade_video_1.mp4"),
        fps=60,
    )


def challenge(project_path: Path) -> None:
    before_clip = ImageClip(str(project_path / "image.png"), duration=8)
    change_clip = ImageClip(str(project_path / "image_c.png"), duration=0.1)
    after_clip = ImageClip(str(project_path / "image.png"), duration=3.9)
    base_clip = concatenate_videoclips(
        [before_clip, change_clip, after_clip],
        method="compose",
    )
    bar_clip = ImageClip(str(project_path / "bar.png"), duration=12)
    bar_clip = bar_clip.set_position(("center", 800))
    target_clip = ImageClip(str(project_path / "target.png"), duration=12)
    target_clip = target_clip.set_position((400, 800))
    seek_clip = ImageClip(str(project_path / "seek.png"), duration=12)
    seek_clip = seek_clip.set_position(lambda t: (t * 50, 800))
    composite = CompositeVideoClip(
        [base_clip, bar_clip, target_clip, seek_clip],
        size=base_clip.size,
    )
    composite.write_videofile(str(project_path / "challenge_video.mp4"), fps=30)


if __name__ == "__main__":
    load_dotenv()
    main()
