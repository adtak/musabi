import io
import os
from typing import Any, TypedDict, cast

import boto3
import requests
from loguru import logger
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from src.shared.logging import log_exec


class TitleParams(TypedDict):
    xy: tuple[float, float]
    text: str
    font: ImageFont.FreeTypeFont
    anchor: str


def handler(event: dict[str, Any], context: object) -> dict[str, str]:  # noqa: ARG001
    bucket_name = os.getenv("IMAGE_BUCKET")
    if bucket_name is None:
        msg = "IMAGE_BUCKET environment variable is not set"
        raise ValueError(msg)
    image_url = cast("str", event.get("ImgUrl"))
    title = cast("str", event.get("DishName"))
    exec_name = cast("str", event.get("ExecName"))

    return main(
        image_url,
        title,
        bucket_name,
        exec_name,
    )


@log_exec
def main(
    image_url: str,
    title: str,
    bucket_name: str,
    exec_name: str,
) -> dict[str, str]:
    image = Image.open(requests.get(image_url, timeout=10, stream=True).raw).convert(
        "RGBA",
    )
    w, h = image.size
    logger.info(f"Image size: width {w} - height {h}")

    blur_image = image.filter(ImageFilter.GaussianBlur(4))
    font_path = "src/edit_img/fonts/Bold.ttf"
    title_image = create_title(w, h, title, font_path)
    result_image = Image.alpha_composite(blur_image, title_image)

    title_image_key = put_image(result_image, bucket_name, f"{exec_name}/0.png")
    image_key = put_image(image, bucket_name, f"{exec_name}/1.png")
    return {
        "TitleImgKey": title_image_key,
        "ImgKey": image_key,
    }


def create_title(
    origin_w: int,
    origin_h: int,
    title: str,
    font_path: str,
) -> Image.Image:
    title_image = Image.new("RGBA", (origin_w, origin_h), (255, 255, 255, 0))
    draw = ImageDraw.Draw(title_image)

    fontsize = _calc_fontsize(draw, title, int(origin_w * 0.8), font_path)
    title_params: TitleParams = {
        "xy": (origin_w // 2, origin_h // 2),
        "text": title,
        "font": ImageFont.truetype(font_path, fontsize),
        "anchor": "mm",
    }
    _, title_top, _, title_bottom = draw.textbbox(**title_params)
    subtitle_params: TitleParams = {
        "xy": (origin_w // 2, title_top),
        "text": "AIが考えたレシピ",
        "font": ImageFont.truetype(font_path, min(50, fontsize)),
        "anchor": "md",
    }
    _, subtitle_top, _, _ = draw.textbbox(**subtitle_params)

    draw.rounded_rectangle(
        ((10, subtitle_top - 20), (origin_w - 10, title_bottom + 20)),
        radius=50,
        fill=(200, 200, 200, 200),
    )
    draw.text(fill="white", **title_params)
    draw.text(fill="white", **subtitle_params)
    return title_image


def _calc_fontsize(
    draw: ImageDraw.ImageDraw,
    text: str,
    text_width_max: int,
    font_path: str,
    font_size: int = 5,
) -> int:
    while True:
        font = ImageFont.truetype(font_path, font_size)
        text_width = draw.textlength(text, font)
        if text_width < text_width_max:
            font_size += 1
        else:
            break
    logger.info(f"Calculated font size {font_size}")
    return font_size


def put_image(image: Image.Image, bucket_name: str, s3_object_key: str) -> str:
    image_buffer = io.BytesIO()
    image.save(image_buffer, format="PNG")
    image_buffer.seek(0)

    s3_client = boto3.client("s3")
    s3_client.put_object(
        Bucket=bucket_name,
        Key=s3_object_key,
        Body=image_buffer,
        ContentType="image/png",
    )
    return s3_object_key


if __name__ == "__main__":
    main("", "", "", "")
