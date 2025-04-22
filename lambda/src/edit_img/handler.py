from loguru import logger
from PIL import Image, ImageDraw, ImageFilter, ImageFont


def handler(event, context) -> None:  # noqa: ANN001, ARG001
    return main()


def main(image: Image, title: str) -> Image:
    origin_image = image.convert("RGBA")
    w, h = origin_image.size
    font_path = "fonts/Bold.ttf"

    logger.info(f"Title: {title}")
    logger.info(f"Image size: width {w} - height {h}")

    blur_image = origin_image.filter(ImageFilter.GaussianBlur(4))
    title_image = create_title(w, h, title, font_path)

    return Image.alpha_composite(blur_image, title_image)


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
        ((10, subtitle_top - 20), (790, title_bottom + 20)),
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


if __name__ == "__main__":
    img = Image.open("image.png")
    main(img.copy(), "This is main title").save("test_image.png")
    img.save("origin_image.png")
