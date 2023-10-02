from loguru import logger
from PIL import Image, ImageDraw, ImageFilter, ImageFont


def write_title(image: Image, title: str) -> Image:
    w, h = image.size
    font_path = "fonts/mgenplus-1p-regular.ttf"

    logger.info(f"Title {title}")
    logger.info(f"Image size: width {w} - height {h}")

    blur_image = image.filter(ImageFilter.GaussianBlur(4))
    draw = ImageDraw.Draw(blur_image)
    textsize = calc_textsize(draw, title, w * 0.8, font_path)
    font = ImageFont.truetype(font_path, textsize)
    draw.text(
        (w // 2, h // 2),
        title,
        "white",
        font=font,
        anchor="mm",
    )
    return blur_image


def calc_textsize(
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
    write_title(img.copy(), "Title").save("test_image.png")
    img.save("origin_image.png")
