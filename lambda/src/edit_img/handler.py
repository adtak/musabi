import io
import os

import boto3
import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from src.shared import (
    handle_exceptions,
    get_logger,
    validate_required_fields,
    safe_dict_access,
)


@handle_exceptions("edit_img")
def handler(event: dict, context: object) -> dict:  # noqa: ARG001
    return main(
        image_url=safe_dict_access(event, "ImgUrl", ""),
        title=safe_dict_access(event, "DishName", ""),
        bucket_name=os.getenv("BUCKET_NAME"),
        exec_name=safe_dict_access(event, "ExecName", ""),
    )


def main(image_url: str, title: str, bucket_name: str, exec_name: str) -> dict:
    """Main function to edit image with title overlay."""
    logger = get_logger("edit_img")
    
    try:
        # Validate required input fields
        validate_required_fields(
            {
                "image_url": image_url,
                "title": title, 
                "bucket_name": bucket_name,
                "exec_name": exec_name
            },
            ["image_url", "title", "bucket_name", "exec_name"]
        )
        
        logger.info(f"Processing image for title: {title}")
        
        # Download and process image
        response = requests.get(image_url, timeout=30, stream=True)
        response.raise_for_status()
        
        image = Image.open(response.raw).convert("RGBA")
        w, h = image.size
        font_path = "src/edit_img/fonts/Bold.ttf"

        logger.info(f"Image size: width {w} - height {h}")

        # Create edited image with title
        blur_image = image.filter(ImageFilter.GaussianBlur(4))
        title_image = create_title(w, h, title, font_path)
        result_image = Image.alpha_composite(blur_image, title_image)

        # Upload images to S3
        logger.info("Uploading images to S3...")
        edit_image_uri = put_image(result_image, bucket_name, f"{exec_name}/0.png")
        origin_image_uri = put_image(image, bucket_name, f"{exec_name}/1.png")
        
        logger.info("Image editing completed successfully")
        
        return {
            "EditImgUri": edit_image_uri,
            "OriginImgUri": origin_image_uri,
        }
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise


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
    """Calculate optimal font size for given text width constraints."""
    logger = get_logger("edit_img")
    
    try:
        max_iterations = 200  # Prevent infinite loops
        iteration = 0
        
        while iteration < max_iterations:
            font = ImageFont.truetype(font_path, font_size)
            text_width = draw.textlength(text, font)
            if text_width < text_width_max:
                font_size += 1
                iteration += 1
            else:
                break
        
        logger.info(f"Calculated font size {font_size} after {iteration} iterations")
        return max(font_size - 1, 5)  # Ensure minimum font size
        
    except Exception as e:
        logger.warning(f"Error calculating font size, using default: {str(e)}")
        return 50  # Default fallback font size


def put_image(image: Image, bucket_name: str, s3_object_key: str) -> str:
    """Upload image to S3 with error handling."""
    logger = get_logger("edit_img")
    
    try:
        logger.info(f"Uploading image to s3://{bucket_name}/{s3_object_key}")
        
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
        
        s3_uri = f"s3://{bucket_name}/{s3_object_key}"
        logger.info(f"Successfully uploaded image to {s3_uri}")
        return s3_uri
        
    except Exception as e:
        logger.error(f"Failed to upload image to S3: {str(e)}")
        raise


if __name__ == "__main__":
    main(
        "",
        "",
    ).save("test_image.png")
