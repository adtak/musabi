import io

import boto3
import requests
from loguru import logger
from PIL import Image, ImageDraw, ImageFilter, ImageFont


def handler(event: dict, context: object) -> None:  # noqa: ARG001
    return main(
        event.get("ImgUrl", ""),
        event.get("DishName", ""),
        event.get("BucketName", ""),
        event.get("ExecName", ""),
    )


def main(image_url: str, title: str, bucket_name: str, exec_name: str) -> Image:
    image = Image.open(requests.get(image_url, timeout=10, stream=True).raw).convert(
        "RGBA",
    )
    w, h = image.size
    font_path = "src/edit_img/fonts/Bold.ttf"

    logger.info(f"Title: {title}")
    logger.info(f"Image size: width {w} - height {h}")

    blur_image = image.filter(ImageFilter.GaussianBlur(4))
    title_image = create_title(w, h, title, font_path)

    result_image = Image.alpha_composite(blur_image, title_image)

    edit_image_uri = put_image(result_image, bucket_name, f"{exec_name}/0.png")
    origin_image_uri = put_image(image, bucket_name, f"{exec_name}/1.png")
    return {
        "EditImgUrl": edit_image_uri,
        "OriginImgUrl": origin_image_uri,
    }


def create_title(
    origin_w: int,
    origin_h: int,
    title: str,
    font_path: str,
) -> Image:
    title_image = Image.new("RGBA", (origin_w, origin_h), (255, 255, 255, 0))
    draw = ImageDraw.Draw(title_image)

    fontsize = _calc_fontsize(draw, title, origin_w * 0.8, font_path)
    title_params = {
        "xy": (origin_w // 2, origin_h // 2),
        "text": title,
        "font": ImageFont.truetype(font_path, fontsize),
        "anchor": "mm",
    }
    _, title_top, _, title_bottom = draw.textbbox(**title_params)
    subtitle_params = {
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
    draw: ImageDraw,
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

def put_image(image: Image, bucket_name: str, s3_object_key: str) -> str:
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
    return f"s3://{bucket_name}/{s3_object_key}"


if __name__ == "__main__":
    main(
        "",
        "",
    ).save("test_image.png")
