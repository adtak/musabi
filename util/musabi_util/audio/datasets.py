import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Self

import librosa
import numpy as np
from dotenv import load_dotenv

FINETUNE_KEYWORD = "melonfinetune"


def main(datasets_dir: str = "outputs/split") -> None:
    datasets_path = Path(datasets_dir)
    train, test = train_test_split(list(datasets_path.glob("*.wav")), 0.8)
    save_metadata(train, datasets_path / "train.jsonl")
    save_metadata(test, datasets_path / "eval.jsonl")
    save_config(datasets_path)


def train_test_split(data: list[str], train_size: float) -> tuple[list[str], list[str]]:
    shuffle_data = np.take(data, np.random.default_rng().permutation(len(data)))
    return np.split(shuffle_data, [int(len(data) * train_size)])


@dataclass
class DataMeta:
    key: str
    artist: str
    sample_rate: int
    file_extension: str
    description: str
    keywords: str
    duration: float
    bpm: int
    genre: list[str]
    title: str
    name: str
    instrument: list[str]
    moods: list[str]
    path: str

    @classmethod
    def from_audio(cls: type[Self], file: Path) -> Self:
        keys = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        # TODO: generate from essentia
        genres = []
        instruments = []
        moods = []
        y, sr = librosa.load(file)
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        key = keys[np.argmax(np.sum(chroma, axis=1))]
        length = librosa.get_duration(y=y, sr=sr)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        return cls(
            key=key,
            artist="",
            sample_rate=44100,
            file_extension="wav",
            description="",
            keywords=FINETUNE_KEYWORD,
            duration=length,
            bpm=round(tempo),
            genre=genres,
            title=file.stem,
            name="",
            instrument=instruments,
            moods=moods,
            path=os.environ["PATH_IN_DATAMETA"] + str(file.name),
        )


def save_metadata(files: list[Path], output: Path) -> None:
    with output.open("w") as f:
        for file in files:
            entry = asdict(DataMeta.from_audio(file))
            f.write(json.dumps(entry) + "\n")


def save_config(output: Path) -> None:
    config_file = output / "train.yaml"
    package_str = "package"
    yaml_contents = f"""#@{package_str} __global__

datasource:
  max_channels: 2
  max_sample_rate: 44100

  train: egs/train
  valid: egs/eval
  generate: egs/train
  evaluate: egs/eval
    """
    with config_file.open("w") as f:
        f.write(yaml_contents)


if __name__ == "__main__":
    load_dotenv()
    main()
