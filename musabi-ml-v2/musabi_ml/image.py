from PIL import Image, ImageDraw, ImageFilter, ImageFont


def write_title(image: Image, title: str) -> Image:
    w, h = image.size
    font = ImageFont.truetype("/System/Library/Fonts/Avenir Next.ttc", 200)
    ImageDraw.Draw(image.filter(ImageFilter.GaussianBlur(4))).text(
        (w // 2, h // 2),
        title,
        "white",
        font=font,
        anchor="mm",
    )
    return image
