from PIL import Image, ImageDraw, ImageFont


def write_title(image: Image, title: str) -> Image:
    font = ImageFont.truetype("/System/Library/Fonts/Avenir Next.ttc", 200)
    ImageDraw.Draw(image).text(
        (960, 540),
        title,
        "white",
        font=font,
        anchor="mm",
    )
    return image
