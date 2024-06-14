import json
import os
from pathlib import Path
from typing import TypedDict

from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont


class Settings(TypedDict):
    text: str


def load_settings() -> Settings:
    with Path("image.settings.json").open("r") as f:
        return json.load(f)


def main() -> None:
    prj_path = Path(os.environ["PROJECT_PATH"])
    img_name = "image.png"
    settings = load_settings()
    img = Image.open(prj_path / img_name)
    font = ImageFont.truetype("/System/Library/Fonts/Avenir Next.ttc", 130)
    ImageDraw.Draw(img).text(
        (640, 570),
        settings["text"],
        "white",
        font=font,
        anchor="mm",
    )
    img.save(prj_path / ("font_" + img_name))


if __name__ == "__main__":
    load_dotenv()
    main()
